import pygame as pg
from . import tool
from . import constants as c
from . import aStarSearch

class Map():
    def __init__(self, width, height, grid):
        # 地图的行数
        self.width = width
        # 地图的列数
        self.height = height 
        # bg_map 是地图的背景颜色二维数组，每个元素对应一个地图格子。
        self.bg_map = [[0 for x in range(self.width)] for y in range(self.height)]
        # entity_map 是保存生物的二维数组，每个元素对应一个地图格子。
        self.entity_map = [[None for x in range(self.width)] for y in range(self.height)]
        # 保存当前行动的生物
        self.active_entity = None
        # 保存生物攻击时所在的地图位置
        self.select = None
        self.setupMapImage(grid)

    def setupMapImage(self, grid):
        # grid_map是地图的格子类型二维数组，每个元素对应一个地图格子
        self.grid_map = [[0 for x in range(self.width)] for y in range(self.height)]
        if grid is not None:
            for data in grid:
                x, y, type = data['x'], data['y'], data['type']
                self.grid_map[y][x] = type
        
        # 创建一个和地图一样大小的图片map_image，用来绘制非空的地图格子，比如格子是石块或草地。
        self.map_image = pg.Surface((c.MAP_WIDTH, c.MAP_WIDTH)).convert()
        self.rect = self.map_image.get_rect()
        self.rect.x = 0
        self.rect.y = 0
        for y in range(self.height):
            for x in range(self.width):
                type = self.grid_map[y][x]
                if type != c.MAP_EMPTY:
                    if c.MAP_HEXAGON:
                        base_x, base_y = tool.getHexMapPos(x, y)
                        self.map_image.blit(tool.GRID[type], (base_x, base_y))
                    else:
                        # (x * c.REC_SIZE, y * c.REC_SIZE)表示格子在地图上的坐标
                        self.map_image.blit(tool.GRID[type], (x * c.REC_SIZE, y * c.REC_SIZE))
        # pygame.Surface 创建的Surface对象的默认颜色是黑色，设置透明色为黑色后，图像上黑色的部分显示时变成透明
        self.map_image.set_colorkey(c.BLACK)

    def isValid(self, map_x, map_y):
        '''判断传入的地图x和y的值是否是有效的'''
        if c.MAP_HEXAGON:
            if map_y % 2 == 0:
                max_x = self.width
            else:
                max_x = self.width - 1
        else:
            max_x = self.width
        if (map_x < 0 or map_x >= max_x or
            map_y < 0 or map_y >= self.height):
            return False
        return True

    def getMapIndex(self, x, y):
        '''根据传入的坐标x和y值，返回坐标所在的格子位置'''
        if c.MAP_HEXAGON:
            return tool.getHexMapIndex(x, y)
        else:
            return (x//c.REC_SIZE, y//c.REC_SIZE)

    def isMovable(self, map_x, map_y):
        '''判断是否能移动到传入的地图格子位置'''
        return (self.grid_map[map_y][map_x] != c.MAP_STONE and
                self.entity_map[map_y][map_x] == None)

    def calHeuristicDistance(self, x1, y1, x2, y2):
        '''估计地图两个格点之间的距离'''
        if c.MAP_HEXAGON:
            dis_y = abs(y1 - y2)
            dis_x = abs(x1 - x2)
            half_y = dis_y // 2
            if dis_y >= dis_x:
                dis_x = 0
            else:
                dis_x -= half_y
            return (dis_y + dis_x)
        else:
            return abs(x1 - x2) + abs(y1 - y2)
    
    def getDistance(self, x1, y1, map_x2, map_y2):
        if c.MAP_HEXAGON:
            x2, y2 = tool.getHexMapPos(map_x2, map_y2)
            x2 += c.HEX_X_SIZE // 2
            y2 += c.HEX_Y_SIZE // 2
            distance = (abs(x1 - x2) + abs(y1 - y2))
        else:
            # 计算坐标（x1，y2）和 地图格子（map_x2, map_y2) 的中心位置之间的距离
            map_x1, map_y1 = self.getMapIndex(x1, y1)
            x2 = map_x2 * c.REC_SIZE + c.REC_SIZE//2
            y2 = map_y2 * c.REC_SIZE + c.REC_SIZE//2
            # 距离计算采用最简单的方式，计算 x 轴和 y 轴差值的和
            distance = (abs(x1 - x2) + abs(y1 - y2))
            if map_x1 != map_x2 and map_y1 != map_y2:
                # 如果是对角线上的相邻位置，距离计算会偏大，要减去一个值
                distance -= c.REC_SIZE//2
        return distance
    
    def isInRange(self, source_x, source_y, dest_x, dest_y, max_distance):
        '''调用 A* 算法函数获取两个格子之间的距离，判断是否小于等于传入的参数 max_distance'''
        distance = aStarSearch.getAStarDistance(self, (source_x, source_y), (dest_x, dest_y))
        if distance is not None:
            if distance <= max_distance:
                return True
        return False

    def checkMouseClick(self, mouse_pos):
        x, y = mouse_pos
        # 获取鼠标位置所在的地图位置
        map_x, map_y = self.getMapIndex(x, y)
        
        if self.bg_map[map_y][map_x] == c.BG_SELECT:
            # 如果格子类型是 c.BG_SELECT，表示这个格子是要行走到的目的位置
            self.active_entity.setDestination(self, map_x, map_y)
            return True
        elif self.bg_map[map_y][map_x] == c.BG_ATTACK:
            # 如果格子类型是 c.BG_ATTACK，表示这个格子上是被攻击的敌方生物
            entity = self.entity_map[map_y][map_x]
            if self.active_entity.canRemoteAttack(self):
                self.active_entity.setRemoteTarget(entity)
            else:
                # self.select 保存了生物攻击前要行走到的目的位置
                self.active_entity.setDestination(self, self.select[0], self.select[1], entity)
            return True
        return False
    
    def resetBackGround(self):
        # 恢复默认，设置所有地图格子类型为 c.BG_EMPTY
        for y in range(self.height):
            for x in range(self.width):
                self.bg_map[y][x] = c.BG_EMPTY

    def showActiveEntityRange(self):
        # 获取行动生物所在的地图位置
        map_x, map_y = self.active_entity.getMapIndex()
        # 获取行动生物的行走距离
        distance = self.active_entity.attr.distance
        
        # 设置行动生物所在的格子类型为 c.BG_ACTIVE
        self.bg_map[map_y][map_x] = c.BG_ACTIVE

        for y in range(self.height):
            for x in range(self.width):
                if (not self.isMovable(x,y) or not self.isValid(x,y) or
                    (x == map_x and y == map_y)):
                    # 忽略不能移动，位置无效或者生物所在的地图格子
                    continue
                if self.isInRange(map_x, map_y, x, y, distance):
                    # 设置距离小于等于生物行走距离的格子类型为 c.BG_RANGE
                    self.bg_map[y][x] = c.BG_RANGE

    def checkMouseMove(self, mouse_pos):
        # 获取鼠标位置所在的地图位置
        map_x, map_y = self.getMapIndex(*mouse_pos)
        
        if (not self.isValid(map_x, map_y) or 
            self.grid_map[map_y][map_x] == c.MAP_STONE):
            # 如果是无效的地图位置或者地图格子上是石头，返回
            return False
        
        # 获取行动生物所在的地图位置
        x, y = self.active_entity.getMapIndex()
        # 获取行动生物的行走距离
        distance = self.active_entity.attr.distance
        
        self.select = None
        # 判断鼠标所在的地图格子上是否有生物
        entity = self.entity_map[map_y][map_x]
        if entity is None: 
            # 鼠标所在的地图格子上没有生物
            if self.isInRange(x, y, map_x, map_y, distance):
                self.bg_map[map_y][map_x] = c.BG_SELECT
        elif entity == self.active_entity:
            # 鼠标所在的地图格子上的生物就是当前行动的生物
            self.bg_map[map_y][map_x] = c.BG_SELECT
        elif entity.group_id != self.active_entity.group_id:
            if self.active_entity.canRemoteAttack(self):
                self.bg_map[map_y][map_x] = c.BG_ATTACK
            else:
                # 鼠标所在的地图格子上的生物是敌方生物
                dir_list = tool.getAttackPositions(map_x, map_y)
                # 保存行走生物可移动到格子的列表
                res_list = []
                for offset_x, offset_y in dir_list:
                    # 遍历鼠标所在地图格子的相邻八个格子
                    tmp_x, tmp_y = map_x + offset_x, map_y + offset_y
                    if self.isValid(tmp_x, tmp_y):
                        type = self.bg_map[tmp_y][tmp_x]
                        if type == c.BG_RANGE or type == c.BG_ACTIVE:
                            # 如果这个格子是当前行动生物可以行动到的，添加到列表中
                            res_list.append((tmp_x, tmp_y))
                if len(res_list) > 0:
                    # 如果格子列表不为空，表示行走生物可以攻击到这个敌方生物。
                    min_dis = c.MAP_WIDTH
                    # 根据鼠标坐标，在格子列表中找到一个距离最小的格子
                    for tmp_x, tmp_y in res_list:
                        distance = self.getDistance(*mouse_pos, tmp_x, tmp_y)
                        if distance < min_dis:
                            min_dis = distance
                            res = (tmp_x, tmp_y)
                    # 设置这个和鼠标坐标距离最小的格子类型为 c.BG_SELECT
                    self.bg_map[res[1]][res[0]] = c.BG_SELECT
                    # 设置鼠标所在地图格子类型为 c.BG_ATTACK
                    self.bg_map[map_y][map_x] = c.BG_ATTACK
                    # 保存距离最小格子的地图位置
                    self.select = res
       
    def updateMapShow(self, mouse_pos):
        self.resetBackGround()
        
        if self.active_entity is None or self.active_entity.state != c.IDLE:
            return
        
        self.showActiveEntityRange()
        self.checkMouseMove(mouse_pos)

    def setEntity(self, map_x, map_y, value):
        # value 为 None，清除 entity_map 数组中指定位置的设置，
        # value 不为 None， 添加生物到 entity_map 数组中指定位置
        self.entity_map[map_y][map_x] = value

    def drawBackground(self, surface):
        if c.MAP_HEXAGON:
            return self.drawBackgroundHex(surface)
        else:
            return self.drawBackgroundSquare(surface)

    def drawBackgroundSquare(self, surface):
        # 根据背景格子类型，设置地图格子为不同的颜色
        for y in range(self.height):
            for x in range(self.width):
                if self.bg_map[y][x] == c.BG_EMPTY:
                    color = c.LIGHTYELLOW
                elif self.bg_map[y][x] == c.BG_ACTIVE:
                    color = c.SKY_BLUE
                elif self.bg_map[y][x] == c.BG_RANGE:
                    color = c.NAVYBLUE
                elif self.bg_map[y][x] == c.BG_SELECT:
                    color = c.GREEN
                elif self.bg_map[y][x] == c.BG_ATTACK:
                    color = c.GOLD
                
                pg.draw.rect(surface, color, (x * c.REC_SIZE, y * c.REC_SIZE, 
                        c.REC_SIZE, c.REC_SIZE))
        
        # 绘制格子类型的图片
        surface.blit(self.map_image, self.rect)

        # 绘制地图每一行的线
        for y in range(self.height):
            # 根据当前的行值，计算y轴的值为(c.REC_SIZE * y)
            start_pos = (0, 0 + c.REC_SIZE * y)
            end_pos = (c.MAP_WIDTH, c.REC_SIZE * y)
            pg.draw.line(surface, c.BLACK, start_pos, end_pos, 1)
        
        # 绘制地图每一列的线
        for x in range(self.width):
            # 根据当前的列值，计算x轴的值为(c.REC_SIZE * x)
            start_pos = (c.REC_SIZE * x, 0) 
            end_pos = (c.REC_SIZE * x, c.MAP_HEIGHT)
            pg.draw.line(surface, c.BLACK, start_pos, end_pos, 1)

    def drawBackgroundHex(self, surface):
        Y_LEN = c.HEX_Y_SIZE // 2
        X_LEN = c.HEX_X_SIZE // 2

        pg.draw.rect(surface, c.LIGHTYELLOW, pg.Rect(0, 0, c.MAP_WIDTH, c.MAP_HEIGHT))

        for y in range(self.height):
            for x in range(self.width):
                if self.bg_map[y][x] == c.BG_EMPTY:
                    color = c.LIGHTYELLOW
                elif self.bg_map[y][x] == c.BG_ACTIVE:
                    color = c.SKY_BLUE
                elif self.bg_map[y][x] == c.BG_RANGE:
                    color = c.NAVYBLUE
                elif self.bg_map[y][x] == c.BG_SELECT:
                    color = c.GREEN
                elif self.bg_map[y][x] == c.BG_ATTACK:
                    color = c.GOLD

                base_x, base_y = tool.getHexMapPos(x, y)
                # 六边形格子的六个顶点坐标
                points = [(base_x, base_y + Y_LEN//2 + Y_LEN), (base_x, base_y + Y_LEN//2),
                          (base_x + X_LEN, base_y), (base_x + X_LEN * 2, base_y + Y_LEN//2),
                          (base_x + X_LEN * 2, base_y + Y_LEN//2 + Y_LEN), (base_x + X_LEN, base_y + Y_LEN*2)]
                pg.draw.polygon(surface, color, points)

        surface.blit(self.map_image, self.rect)

        for y in range(self.height):
            for x in range(self.width):
                if y % 2 == 0:
                    base_x = X_LEN * 2 * x
                    base_y = Y_LEN * 3 * (y//2)
                else:
                    if x == self.width - 1:
                        continue
                    base_x = X_LEN * 2 * x + X_LEN
                    base_y = Y_LEN * 3 * (y//2) + Y_LEN//2 + Y_LEN
                # 六边形格子的六个顶点坐标
                points = [(base_x, base_y + Y_LEN//2 + Y_LEN), (base_x, base_y + Y_LEN//2),
                          (base_x + X_LEN, base_y), (base_x + X_LEN * 2, base_y + Y_LEN//2),
                          (base_x + X_LEN * 2, base_y + Y_LEN//2 + Y_LEN), (base_x + X_LEN, base_y + Y_LEN*2)]
                pg.draw.lines(surface, c.BLACK, True, points)