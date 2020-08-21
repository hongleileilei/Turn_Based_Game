import os # 加载 os 模块
import json # 加载 json 模块
from abc import abstractmethod
import pygame as pg  # 为了书写方便，将 pygame 缩写为pg
from . import constants as c # 为了书写方便，将constants缩写为c

class State():
    def __init__(self):
        # 初始化当前时间
        self.current_time = 0.0
        # done 用来判断本状态是否结束
        self.done = False
        # next 表示本状态结束后要切换到的下一个状态
        self.next = None
        # game_info 保存需要在状态间传递的游戏信息
        self.game_info = {}
    
    @abstractmethod
    def startup(self, current_time, game_info):
        '''抽象函数，继承的状态类必须要实现。切换到这个状态时的启动函数'''

    def cleanup(self):
        # 状态退出时的清除函数，返回保存的游戏信息
        self.done = False
        return self.game_info
    
    @abstractmethod
    def update(self, surface, current_time, mouse_pos):
        '''抽象函数，继承的状态类必须要实现。'''

class Control():
    def __init__(self):
        # screen 会被 pygame 用来绘制图像
        self.screen = pg.display.get_surface()
        # done 用来判断主循环是否要退出，done 为 True，游戏结束
        self.done = False
        # 生成 pygame clock 对象
        self.clock = pg.time.Clock()
        # fps 60 表示 pygame 每秒钟会执行的帧数是 60
        self.fps = 60
        # 保存鼠标点击时的坐标
        self.mouse_pos = None
        # 状态类的字典
        self.state_dict = {}
        # 当前状态类的名称
        self.state_name = None
        # 当前状态类
        self.state = None
        self.current_time = 0.0
        # 初始化状态间传递的游戏信息
        self.game_info = {c.LEVEL_NUM:c.START_LEVEL_NUM}

    def setupStates(self, state_dict, start_state):
        # 设置状态类的字典，字典的 key 是状态的名称
        self.state_dict = state_dict
        # 设置游戏的当前状态名称
        self.state_name = start_state
        # 设置游戏的当前状态
        self.state = self.state_dict[self.state_name]
        # 调用状态的启动函数
        self.state.startup(self.current_time, self.game_info)

    def flipState(self):
        # 调用已结束状态的清除函数
        game_info = self.state.cleanup()
        # 获取下一个状态的名称
        self.state_name = self.state.next
        if self.state_name == c.EXIT:
            # 如果下一个状态是退出状态，主循环结束
            self.done = True
        else:
            # 切换到下一个状态
            self.state = self.state_dict[self.state_name]
            # 调用状态的启动函数
            self.state.startup(self.current_time, game_info)

    def update(self):
        '''游戏的更新函数'''
        self.current_time = pg.time.get_ticks()
        self.state.update(self.screen, self.current_time, self.mouse_pos)
        self.mouse_pos = None
        if self.state.done:
            # 当前状态结束时，进行状态切换
            self.flipState()

    def eventLoop(self):
        '''获取pygame监听到的所有事件，这里我们只关心退出按钮和鼠标点击事件'''
        for event in pg.event.get():
            if event.type == pg.QUIT:
                #当有点击退出按钮事件时，游戏退出
                self.done = True
            elif event.type == pg.MOUSEBUTTONDOWN:
                #当有鼠标点击事件时，保存鼠标的坐标
                self.mouse_pos = pg.mouse.get_pos()

    def main(self):
        # 程序主循环
        while not self.done:
            # 获取事件
            self.eventLoop()
            # 更新游戏状态
            self.update()
            # 显示图像
            pg.display.update()
            # 等待 1/self.fps 秒时间
            self.clock.tick(self.fps)

def getImage(sheet, x, y, width, height, colorkey, scale):
    # 创建一个Surface对象image
    image = pg.Surface([width, height])
    # 获取Surface对象的Rect属性
    rect = image.get_rect()
    # 将sheet绘制在image上
    image.blit(sheet, (0, 0), (x, y, width, height))
    # 设置图片的透明颜色
    image.set_colorkey(colorkey)
    # 根据参数scale值对图片进行放大或缩小
    image = pg.transform.scale(image, (int(rect.width*scale), int(rect.height*scale)))
    return image

def loadAllGraphics(directory, colorkey=c.WHITE, accept=('.png', '.jpg', '.bmp', '.gif')):
    # 创建一个graphics字典，保存所有加载的Surface对象
    graphics = {}
    # 遍历目录中的所有文件
    for pic in os.listdir(directory):
        # 分离文件的名称和后缀名，比如'tile.png'分离后变成'tile' 和'.png'
        name, ext = os.path.splitext(pic)
        if ext.lower() in accept:
            # 文件的后缀名在accept元组中
            img = pg.image.load(os.path.join(directory, pic))
            if img.get_alpha():
                img = img.convert_alpha()
            else:
                img = img.convert()
                img.set_colorkey(colorkey)
            # 将加载的image保存在graphics字典中，key是文件名称
            graphics[name] = img
    return graphics

def getMapGridImage():
    '''获取地图格子类型的图片'''
    grid_images = {}
    # image_rect_dict 是每个格子类型图片在tile图片中的位置和大小
    image_rect_dict = {c.MAP_STONE:(0, 16, 16, 16), c.MAP_GRASS:(0, 0, 16, 16)}
    for type, rect in image_rect_dict.items():
        grid_images[type] = getImage(GFX['tile'], *rect, c.WHITE, 3)
    return grid_images

def load_entiry_attr(file_path):
    attrs = {}
    f = open(file_path)
    data = json.load(f)
    f.close()
    for name, attr in data.items():
        attrs[name] = attr
    return attrs

def getMovePositions(x, y):
    if c.MAP_HEXAGON:
        # 根据当前地图格子 Y 轴的位置返回相邻的六个六边形格子位置
        if y % 2 == 0:
            offsets = [(-1, 0), (-1, -1), (0, -1), (1, 0), (-1, 1), (0, 1)]
        else:
            offsets = [(-1, 0), (0, -1), (1, -1), (1, 0), (0, 1), (1, 1)]
    else:
        # 从当前的格子可以移动到相邻的左边，上面，右边，下面四个格子
        offsets = [(-1,0), (0, -1), (1, 0), (0, 1)]
    return offsets

def getAttackPositions(x, y):
    if c.MAP_HEXAGON:
        # 六边形地图中可以攻击的相邻位置和可以移动的相邻位置是一样的
        return getMovePositions(x, y)
    else:
        return [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1),(1,0), (1,1)]

def isNextToEntity(entity1, entity2):
    # 判断两个生物是否在相邻可攻击的地图位置
    dir_list = getAttackPositions(entity1.map_x, entity1.map_y)
    for offset_x, offset_y in dir_list:
        x, y = entity1.map_x + offset_x, entity1.map_y + offset_y
        if x == entity2.map_x and y == entity2.map_y:
            return True
    return False

def getHexMapPos(x, y):
    # 根据地图格子位置返回对应的坐标值
    X_LEN = c.HEX_X_SIZE // 2
    Y_LEN = c.HEX_Y_SIZE // 2
    if y % 2 == 0:
        base_x = X_LEN * 2 * x
        base_y = Y_LEN * 3 * (y//2)
    else:
        base_x = X_LEN * 2 * x + X_LEN
        base_y = Y_LEN * 3 * (y//2) + Y_LEN//2 + Y_LEN
    return (base_x, base_y)

class Vector2d():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def minus(self, vec):
        return Vector2d(self.x - vec.x, self.y - vec.y)

    def crossProduct(self, vec):
        return (self.x * vec.y - self.y * vec.x)

def isInTriangle(x1, y1, x2, y2, x3, y3, x, y):
    # 判断坐标 (x,y) 是否在三角形中
    A = Vector2d(x1, y1)
    B = Vector2d(x2, y2)
    C = Vector2d(x3, y3)
    P = Vector2d(x, y)
    PA = A.minus(P)
    PB = B.minus(P)
    PC = C.minus(P)
    t1 = PA.crossProduct(PB)
    t2 = PB.crossProduct(PC)
    t3 = PC.crossProduct(PA)
    if (t1 * t2 >= 0) and (t1 * t3 >= 0):
        return True
    return False

def getHexMapIndex(x, y):
    # 根据坐标返回所在六边形格子的地图位置
    X_LEN = c.HEX_X_SIZE // 2
    Y_LEN = c.HEX_Y_SIZE // 2
    tmp_x, offset_x = divmod(x, c.HEX_X_SIZE)
    tmp_y, offset_y = divmod(y, Y_LEN * 3)
    map_x, map_y = 0, 0
    if offset_y <= (Y_LEN + Y_LEN//2):
        if offset_y >= Y_LEN//2:
            map_x, map_y = tmp_x, tmp_y * 2
        else:
            triangle_list = [(0, 0, 0, Y_LEN//2, X_LEN, 0),
                             (0, Y_LEN//2, X_LEN, 0, c.HEX_X_SIZE, Y_LEN//2),
                             (X_LEN, 0, c.HEX_X_SIZE, 0, c.HEX_X_SIZE, Y_LEN//2)]
            map_list = [(tmp_x - 1, tmp_y * 2 -1), (tmp_x, tmp_y * 2), (tmp_x, tmp_y * 2 -1)]
            for i, data in enumerate(triangle_list):
                if isInTriangle(*data, offset_x, offset_y):
                    map_x, map_y = map_list[i]
                    break
    elif offset_y >= c.HEX_Y_SIZE:
        if offset_x <= X_LEN:
            map_x, map_y = tmp_x - 1, tmp_y * 2 + 1
        else:
            map_x, map_y = tmp_x, tmp_y *2 + 1
    else:
        triangle_list = [(0, Y_LEN + Y_LEN//2, 0, c.HEX_Y_SIZE, X_LEN, c.HEX_Y_SIZE),
                         (0, Y_LEN + Y_LEN//2, X_LEN, c.HEX_Y_SIZE, c.HEX_X_SIZE, Y_LEN + Y_LEN//2),
                         (X_LEN, c.HEX_Y_SIZE, c.HEX_X_SIZE, Y_LEN + Y_LEN//2, c.HEX_X_SIZE, c.HEX_Y_SIZE)]
        map_list = [(tmp_x - 1, tmp_y * 2 + 1), (tmp_x, tmp_y * 2), (tmp_x, tmp_y *2 + 1)]
        for i, data in enumerate(triangle_list):
            if isInTriangle(*data, offset_x, offset_y):
                map_x, map_y = map_list[i]
                break

    return (map_x, map_y)


# pygame的初始化
pg.init()
# 设置游戏窗口的标题
pg.display.set_caption(c.ORIGINAL_CAPTION)
# 设置游戏窗口的大小（宽度和高度）
pg.display.set_mode(c.SCREEN_SIZE)

# 加载resources/graphics目录中所有的图片文件
GFX = loadAllGraphics(os.path.join("resources","graphics"))
# 获取地图格子类型的图片
GRID = getMapGridImage()
# 加载生物属性的配置文件
ATTR = load_entiry_attr(os.path.join('data', 'entity.json'))
