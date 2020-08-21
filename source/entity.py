import pygame as pg
from . import tool
from . import constants as c
from . import aStarSearch
from . import map

class FireBall():
    def __init__(self, x, y, enemy, hurt):
        # 创建火球图形
        frame_rect = (0, 0, 14, 14)
        self.image = tool.getImage(tool.GFX[c.FIREBALL], *frame_rect, c.WHITE, c.SIZE_MULTIPLIER)
        self.rect = self.image.get_rect()
        # 设置火球的开始坐标
        self.rect.centerx = x
        self.rect.centery = y
        self.enemy = enemy
        self.hurt = hurt
        self.done = False
        # 计算火球的速度
        self.calVelocity()
    
    def calVelocity(self):
        # 计算火球开始坐标和敌方生物中心坐标之间的距离，分为 x 轴和 y 轴距离
        dis_x = self.enemy.rect.centerx - self.rect.centerx
        dis_y = self.enemy.rect.centery - self.rect.centery
        # 计算火球在 x 轴和 y 轴的速度，单位是像素
        if c.MAP_HEXAGON:
            num = c.HEX_X_SIZE // 2
        else:
            num = c.REC_SIZE
        self.x_vel = dis_x / num
        self.y_vel = dis_y / num

    def update(self, level):
        # 更新火球的图形显示坐标
        self.rect.x += self.x_vel
        self.rect.y += self.y_vel
        # 计算火球中心坐标和敌方生物中心坐标的距离
        distance = abs(self.rect.centerx - self.enemy.rect.centerx) + abs(self.rect.centery - self.enemy.rect.centery)
        if distance < self.enemy.rect.width / 2:
            # 距离小于敌方生物图形宽度的一半值时，认为火球和敌方生物发生了碰撞，产生伤害
            self.enemy.setHurt(self.hurt, level)
            self.done = True
    
    def draw(self, surface):
        # 绘制火球图形
        surface.blit(self.image, self.rect)


class EntityAttr():
    def __init__(self, data):
        # 生命
        self.max_health = data[c.ATTR_HEALTH]
        # 行走距离
        self.distance = data[c.ATTR_DISTANCE]
        # 基础伤害
        self.damage = data[c.ATTR_DAMAGE]
        # 攻击
        self.attack = data[c.ATTR_ATTACK]
        # 防御
        self.defense = data[c.ATTR_DEFENSE]
        # 速度
        self.speed = data[c.ATTR_SPEED]
        # 是否是远程生物
        if data[c.ATTR_REMOTE] == 0:
            self.remote = False
        else:
            self.remote = True
    
    def getHurt(self, enemy_attr, damage_half=False):
        # 计算对一个敌方生物的攻击伤害，参考英雄无敌系列的伤害计算公式
        offset = 0
        # 根据我方攻击和敌方防御的差值，计算伤害的加成或减弱
        if self.attack > enemy_attr.defense:
            offset = (self.attack - enemy_attr.defense) * 0.05
        elif self.attack < enemy_attr.defense:
            offset = (self.attack - enemy_attr.defense) * 0.025
        
        # 如果 damage_half 为 True，生物的基础伤害减半
        damage = self.damage / 2 if damage_half else self.damage
        # 计算出攻击伤害
        hurt = int(damage * (1 + offset))
        
        # 如果攻击伤害超过了上下限范围，修正攻击伤害值
        if hurt > self.damage * 4:
            hurt = self.damage * 4
        elif hurt < self.damage / 4:
            hurt = self.damage / 4
        return int(hurt)


class Entity():
    def __init__(self, group, name, map_x, map_y, data):
        # 保存生物所在的生物组，生物组id ，地图位置
        self.group = group
        self.group_id = group.group_id
        self.map_x = map_x
        self.map_y = map_y
        # 加载生物的图形
        self.frames = []
        self.frame_index = 0
        self.loadFrames(name)
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        # 设置生物图形显示坐标
        self.rect.centerx, self.rect.centery = self.getRectPos(map_x, map_y)
        
        # 创建生物属性对象
        self.attr = EntityAttr(data)
        # 保存生物的生命值
        self.health = self.attr.max_health
        # 生物攻击时保存的敌方生物
        self.enemy = None
        
        # 生物初始状态为空闲
        self.state = c.IDLE
        # 记录生物图形切换的时间，用来实现生物行走的动画效果
        self.animate_timer = 0.0
        # 生物攻击定时器，用来实现生物的攻击效果
        self.attack_timer = 0
        # 记录游戏当前时间
        self.current_time = 0.0
        # 生物行走时的速度
        self.move_speed = 2
        # 生物到目的位置的行走路径
        self.walk_path = None
        
        # 是否是远程攻击
        self.remote_attack = False
        # 远程武器
        self.weapon = None
    
    def loadFrames(self, name):
        # 加载生物的图形列表
        frame_rect_list = [(64, 0, 32, 32), (96, 0, 32, 32)]
        for frame_rect in frame_rect_list:
            self.frames.append(tool.getImage(tool.GFX[name], 
                    *frame_rect, c.BLACK, c.SIZE_MULTIPLIER))

    def getMapIndex(self):
        '''返回生物的地图位置'''
        return (self.map_x, self.map_y)

    def getRectPos(self, map_x, map_y):
        '''返回在地图格子中显示生物图形的坐标'''
        if c.MAP_HEXAGON:
            base_x, base_y = tool.getHexMapPos(map_x, map_y)
            return (base_x + c.HEX_X_SIZE // 2, base_y + c.HEX_Y_SIZE // 2)
        else:
            return(map_x * c.REC_SIZE + c.REC_SIZE // 2, map_y * c.REC_SIZE + c.REC_SIZE // 2 + 3)
        
    def setDestination(self, map, map_x, map_y, enemy=None):
        # 获取到目的位置的行走路径
        path = aStarSearch.getPath(map, (self.map_x, self.map_y), (map_x, map_y))
        if path is not None:
            # 找到一条路径，保存路径和目的坐标
            self.walk_path = path
            # 设置目的位置坐标
            self.dest_x, self.dest_y = self.getRectPos(map_x, map_y)
            # 设置下一个格子的坐标为当前位置坐标
            self.next_x, self.next_y = self.rect.centerx, self.rect.centery
            # 保存敌方生物
            self.enemy = enemy
            # 设置生物状态为行走状态
            self.state = c.WALK
        elif enemy is not None:
            # 保存敌方生物
            self.enemy = enemy
            # 设置生物状态为攻击状态
            self.state = c.ATTACK
    
    def setRemoteTarget(self, enemy):
        # 生物可以远程攻击时调用，保存敌方生物
        self.enemy = enemy
        # 设置 remote_attack 为 True，表示将进行远程攻击
        self.remote_attack = True
        # 设置生物状态为攻击状态
        self.state = c.ATTACK
    
    def canRemoteAttack(self, map):
        if self.attr.remote:
            # 如果是远程生物，检查是否有敌方生物在可攻击的相邻格子
            dir_list = tool.getAttackPositions(self.map_x, self.map_y)
            for offset_x, offset_y in dir_list:
                # 遍历生物所在地图格子的相邻八个格子
                tmp_x, tmp_y = self.map_x + offset_x, self.map_y + offset_y                    
                if map.isValid(tmp_x, tmp_y):
                    entity = map.entity_map[tmp_y][tmp_x]
                    if entity is not None and entity.group_id != self.group_id:
                        # 如果有敌方生物在相邻格子，不能进行远程攻击
                        return False
            return True
        return False

    def getNextPosition(self):
        # 获取下一个格子的坐标
        if len(self.walk_path) > 0:
            next = self.walk_path[0]
            map_x, map_y = next.getPos()
            self.walk_path.remove(next)        
            return self.getRectPos(map_x, map_y)
        return None
 
    def walkToDestination(self):
        if self.rect.centerx == self.next_x and self.rect.centery == self.next_y:
            # 已经行走到下一个格子的坐标，继续获取再下一个格子的坐标
            pos = self.getNextPosition()
            if pos is None:
                self.state = c.IDLE
            else:
                # 保存路径中下一个格子的坐标
                self.next_x, self.next_y = pos

        # 行走到下一个格子的坐标，先移动 x 轴方向，在移动 y 轴方向
        if self.rect.centerx != self.next_x:
            if self.rect.centerx < self.next_x:
                # 向 x 轴右边移动
                self.rect.centerx += self.move_speed
                if self.rect.centerx > self.next_x:
                    # 如果大于下一个格子的 x 轴值，修正下
                    self.rect.centerx = self.next_x
            else:
                # 向 x 轴左边移动
                self.rect.centerx -= self.move_speed
                if self.rect.centerx < self.next_x:
                    # 如果小于下一个格子的 x 轴值，修正下
                    self.rect.centerx = self.next_x
        if self.rect.centery != self.next_y:
            if self.rect.centery < self.next_y:
                # 向 y 轴下方移动
                self.rect.centery += self.move_speed
                if self.rect.centery > self.next_y:
                    # 如果大于下一个格子的 y 轴值，修正下
                    self.rect.centery = self.next_y
            else:
                # 向 y 轴上方移动
                self.rect.centery -= self.move_speed
                if self.rect.centery < self.next_y:
                    # 如果小于下一个格子的 y 轴值，修正下
                    self.rect.centery = self.next_y

    def attack(self, enemy, level):
        # 计算出对敌方生物的攻击伤害
        if self.attr.remote:
            hurt = self.attr.getHurt(enemy.attr, True)
        else:
            hurt = self.attr.getHurt(enemy.attr)
        enemy.setHurt(hurt, level)

    def setHurt(self, damage, level):
        # 当前生命值减去攻击伤害值
        self.health -= damage
        # 创建伤害值显示对象，并添加到运行类的伤害值显示管理组中
        level.addHurtShow(HurtShow(self.rect.centerx, self.rect.y, damage))
        
        if self.health <= 0:
            # 如果生命值小于等于 0， 表示生物死亡，删除地图中生物所在的位置
            level.map.setEntity(self.map_x, self.map_y, None)
            # 从生物组中删除生物
            self.group.removeEntity(self)

    def shoot(self, enemy):
        # 获取攻击伤害
        hurt = self.attr.getHurt(enemy.attr)
        # 创建火球对象
        self.weapon = FireBall(*self.rect.center, self.enemy, hurt)

    def update(self, current_time, level):
        map = level.map
        self.current_time = current_time
        if self.state == c.WALK:
            if (self.current_time - self.animate_timer) > 200:
                # 当前图形显示时间超过 200 毫秒，切换图形索引值
                if self.frame_index == 0:
                    self.frame_index = 1
                else:
                    self.frame_index = 0
                # 更新生物图形切换的时间
                self.animate_timer = self.current_time
    
            if self.rect.centerx != self.dest_x or self.rect.centery != self.dest_y:
                # 如果还没走到目的坐标，继续行走
                self.walkToDestination()
            else:
                # 已经走到目的坐标，生物的地图位置已经改变，更新地图中生物所在的位置
                map.setEntity(self.map_x, self.map_y, None)
                self.map_x, self.map_y = map.getMapIndex(self.dest_x, self.dest_y)
                map.setEntity(self.map_x, self.map_y, self)
                # 设置行走路径为 None
                self.walk_path = None
                if self.enemy is None:
                    # 设置生物状态为空闲状态
                    self.state = c.IDLE
                else:
                    # 设置生物状态为攻击状态
                    self.state = c.ATTACK
        elif self.state == c.ATTACK:
            if self.attr.remote and self.remote_attack:
                # 远程生物进行远程攻击
                if self.weapon is None:
                    # 如果远程武器 weapon 是 None，创建远程武器
                    self.shoot(self.enemy)
                else:
                    # 调用远程武器的更新函数
                    self.weapon.update(level)
                    if self.weapon.done:
                        # 远程武器已经攻击到敌方生物，恢复默认设置
                        self.weapon = None
                        self.enemy = None
                        self.remote_attack = False
                        # 设置生物状态为空闲状态
                        self.state = c.IDLE
            else:
                if self.attack_timer == 0:
                    # 在首次进入生物攻击状态时，对敌方生物造成伤害
                    self.attack(self.enemy, level)
                    self.enemy = None
                    self.attack_timer = self.current_time
                elif (self.current_time - self.attack_timer) > 500:
                    # 生物的攻击定时器超时，重设生物的攻击定时器时间为 0
                    self.attack_timer = 0
                    # 设置生物状态为空闲状态
                    self.state = c.IDLE
    
        if self.state == c.IDLE:
            # 如果是空闲状态，设置图形索引值为 0
            self.frame_index = 0

    def draw(self, surface):
        # 获取当前显示的图形
        self.image = self.frames[self.frame_index]
        surface.blit(self.image, self.rect)
        if self.health > 0:
            # 绘制生物的生命条
            width = self.rect.width * self.health / self.attr.max_health
            height = 5
            pg.draw.rect(surface, c.RED, pg.Rect(self.rect.left, self.rect.top - height - 1, width, height))
        
        if self.weapon is not None:
            self.weapon.draw(surface)

class EntityGroup():
    def __init__(self, group_id):
        # 生物列表
        self.group = []
        self.hurt_group = []
        # 本生物组对象的 id 值
        self.group_id = group_id
        # 当前行动的生物在生物列表中的索引值
        self.entity_index = 0

    def createEntity(self, entity_list, map):
        for data in entity_list:
            # 获取生物的名称和地图位置
            entity_name, map_x, map_y = data['name'], data['x'], data['y']
            # 地图位置允许使用负数，类似 python 的列表负数索引值
            if map_x < 0:
                map_x = c.GRID_X_LEN + map_x
            if map_y < 0:
                map_y = c.GRID_Y_LEN + map_y
            
            # 创建生物对象，并添加到生物组
            entity = Entity(self, entity_name, map_x, map_y, tool.ATTR[entity_name])
            self.group.append(entity)
            # 在地图中设置生物所在的位置
            map.setEntity(map_x, map_y, entity)
        
        # 按照生物的速度从大到小排序，速度快的生物优先行动
        self.group = sorted(self.group, key=lambda x:x.attr.speed, reverse=True)

    def removeEntity(self, entity):
        # 一个生物死亡时，从生物组中删除，并更新生物列表中的索引值
        for i in range(len(self.group)):
            if self.group[i] == entity:
                if self.entity_index > i:
                    # 更新下一个行动生物的 index
                    self.entity_index -= 1
        self.group.remove(entity)
    
    def isEmpty(self):
        # 如果生物列表为空，返回 True, 否则返回 False
        if len(self.group) == 0:
            return True
        return False
    
    def nextTurn(self):
        # 生物组所有生物已经行动过一轮，重新开始下一轮
        self.entity_index = 0

    def getActiveEntity(self):       
        if self.entity_index >= len(self.group):
            # 索引值大于生物数量，表示一轮行动结束，返回 None
            entity = None
        else:
            # 获取本生物组中将要行动的生物
            entity = self.group[self.entity_index]
        return entity

    def consumeEntity(self):
        # 每次生物行动结束后调用，索引值指向下一个将要行动的生物
        self.entity_index += 1

    def update(self, current_time, level):
        # 调用本生物组中所有生物的更新函数
        for entity in self.group:
            entity.update(current_time, level)

    def draw(self, surface):
        # 绘制本生物组中的所有生物图形
        for entity in self.group:
            entity.draw(surface)

class HurtShow():
    def __init__(self, x, y, hurt):
        # 保存伤害显示的开始 y 轴坐标
        self.y = y
        # 创建伤害值的图形
        self.createHurtImage(hurt)
        self.rect = self.image.get_rect()
        # 设置伤害值的开始坐标
        self.rect.centerx = x
        self.rect.bottom = y
        # 设置伤害值图形向上方移动的速度为 1，单位是像素
        self.y_vel = -1
        # 设置向上方移动的距离为 40，单位是像素
        self.distance = 40

    def createHurtImage(self, hurt):
        # 创建字体
        font = pg.font.SysFont(None, 30)
        # 创建伤害值图形，字体颜色为红色，背景颜色是白色
        self.image = font.render(str(hurt), True, c.RED, c.WHITE)
        # 设置图形的透明颜色为白色，这样图形背景颜色在界面上显示时是透明的
        self.image.set_colorkey(c.WHITE)

    def shouldRemove(self):
        # 判断是否要删除伤害值显示
        if (self.y - self.rect.y) > self.distance:
            # 伤害值图形已经向上移动了指定的距离，可以删除
            return True
        return False

    def update(self):
        # 根据 y 轴的速度更新伤害值图形显示的坐标
        self.rect.y += self.y_vel

    def draw(self, surface):
        # 绘制伤害值图形
        surface.blit(self.image, self.rect)
