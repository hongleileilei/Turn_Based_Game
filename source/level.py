import os
import json
import random
import pygame as pg
from . import tool
from . import constants as c
from . import map, entity, gameAI

class Level(tool.State):
    def __init__(self):
        tool.State.__init__(self)
    
    def startup(self, current_time, game_info):
        # 保存状态的开始时间
        self.start_time = current_time
        # 保存游戏信息
        self.game_info = game_info
        self.loadMap()
        # 如果在地图配置文件中设置了格子信息，则读取出来
        grid = self.map_data[c.MAP_GRID] if c.MAP_GRID in self.map_data else None
        # 创建地图类
        self.map = map.Map(c.GRID_X_LEN, c.GRID_Y_LEN, grid)
        # 创建生物组
        self.setupGroup()
        # 设置初始状态为空闲状态
        self.state = c.IDLE
    
    def loadMap(self):
        '''加载地图配置文件'''
        map_file = 'level_' + str(self.game_info[c.LEVEL_NUM]) + '.json'
        file_path = os.path.join('data', 'map', map_file)
        f = open(file_path)
        # json.load 函数将json文件内容解析后返回一个字典
        self.map_data = json.load(f)
        f.close()

    def setupGroup(self):
        # 创建生物组 1
        self.group1 = entity.EntityGroup(1)
        # 根据关卡地图配置文件中的生物组 1 的配置，创建生物组 1 的生物
        self.group1.createEntity(self.map_data[c.GROUP1], self.map)
        # 创建生物组 2
        self.group2 = entity.EntityGroup(2)
        # 根据关卡地图配置文件中的生物组 2 配置，创建生物组 2 的生物
        self.group2.createEntity(self.map_data[c.GROUP2], self.map)
        # 创建伤害显示的管理组列表
        self.hurt_group = []

    def update(self, surface, current_time, mouse_pos):
        '''游戏的更新函数'''
        self.current_time = current_time

        if self.state == c.IDLE:
            # 获取下一个行动的生物
            result = self.getActiveEntity()
            if result is not None:
                entity, group = result
                # 保存当前行动生物
                self.map.active_entity = entity
                # 更新生物组的下一个行动生物索引
                group.consumeEntity()
                # 设置运行类状态为生物行为选择状态
                self.state = c.SELECT
            else:
                # 本轮两个生物组中的所有生物都行动过了，进入下一轮
                self.group1.nextTurn()
                self.group2.nextTurn()
        elif self.state == c.SELECT:
            if self.map.active_entity.group_id == 1:
                # 如果行动生物属于生物组 1，调用 getAction 函数获取行动选择
                pos, enemy = gameAI.getAction(self.map.active_entity, self.map, self.group2.group)
                if pos is None:
                    # 目的位置为 None, 表示行动生物进行远程攻击
                    self.map.active_entity.setRemoteTarget(enemy)
                else:
                    # 目的位置不为 None, 表示行动生物进行行走或近战攻击
                    self.map.active_entity.setDestination(self.map, pos[0], pos[1], enemy)
                self.state = c.ENTITY_ACT
            else:
                self.map.updateMapShow(pg.mouse.get_pos())
                if mouse_pos is not None:
                    self.mouseClick(mouse_pos)
        elif self.state == c.ENTITY_ACT:
            # 更新地图的背景显示
            self.map.updateMapShow(pg.mouse.get_pos())
            # 更新两个生物组中生物的状态
            self.group1.update(current_time, self)
            self.group2.update(current_time, self)
            if self.map.active_entity.state == c.IDLE:
                # 当前行动生物状态变成空闲状态，表示生物行动结束
                self.state = c.IDLE
        
        remove_list = []
        for hurt in self.hurt_group:
            # 更新伤害显示对象的图形坐标
            hurt.update()
            if hurt.shouldRemove():
                # 如果有伤害显示对象需要删除，添加到删除列表中
                remove_list.append(hurt)
        for hurt in remove_list:
            # 遍历删除列表，从伤害显示管理组中删除
            self.hurt_group.remove(hurt)
            
        # 检查游戏状态
        self.checkGameState()
        self.draw(surface)

    def getActiveEntity(self):
        # 从生物组 1 获取下一个行动的生物
        entity1 = self.group1.getActiveEntity()
        # 从生物组 2 获取下一个行动的生物
        entity2 = self.group2.getActiveEntity()
        if entity1 and entity2:
            # 本轮中生物组 1 和生物组 2 都有待行动的生物，
            # 则比较两个生物的速度属性值，速度快的生物先行动
            if entity1.attr.speed >= entity2.attr.speed:
                entity, group = entity1, self.group1
            else:
                entity, group = entity2, self.group2
        elif entity1:
            # 本轮中只有生物组 1 还有待行动的生物
            entity, group = entity1, self.group1
        elif entity2:
            # 本轮中只有生物组 2 还有待行动的生物
            entity, group = entity2, self.group2
        else:
            return None
        return (entity, group)

    def mouseClick(self, mouse_pos):
        # 判断鼠标点击的位置，当前行动生物是否可以走到
        if self.map.checkMouseClick(mouse_pos):
            # 鼠标点击的位置，当前行动生物可以走到，重设地图背景格子类型
            self.map.resetBackGround()
            # 设置运行类状态为生物行为执行状态
            self.state = c.ENTITY_ACT
    
    def addHurtShow(self, hurt):
        self.hurt_group.append(hurt)

    def checkGameState(self):
        # 如果有一个生物组没有生物了，关卡结束
        if self.group1.isEmpty() or self.group2.isEmpty():
            # 设置关卡运行状态结束
            self.done = True
            # 约定敌方是生物组 1，我方是生物组 2
            if self.group1.isEmpty():
                # 如果胜利，下一个状态是关卡胜利状态
                self.next = c.LEVEL_WIN
            else:
                # 如果失败，下一个状态是关卡失败状态
                self.next = c.LEVEL_LOSE

    def draw(self, surface):
        # 绘制游戏地图显示
        self.map.drawBackground(surface)
        # 绘制两个生物组中生物的图形
        self.group1.draw(surface)
        self.group2.draw(surface)
        
        for hurt in self.hurt_group:
            # 绘制伤害显示图形
            hurt.draw(surface)
        
