import pygame as pg
from . import tool
from . import constants as c

class MainMenu(tool.State):
    def __init__(self):
        tool.State.__init__(self)
    
    def startup(self, current_time, game_info):
        # 保存游戏信息
        self.game_info = game_info
        # 创建开始按钮和退出按钮
        self.setupButtons()
        
        # 创建游戏名称
        font = pg.font.SysFont(None, 50)
        self.name_image = font.render('My Strategy Game', True, c.SKY_BLUE, c.LIGHTYELLOW)
        self.name_rect = self.name_image.get_rect()
        # 设置游戏名称图形的位置
        self.name_rect.x = 90
        self.name_rect.y = 100

    def createButton(self, text, text_color, button_color, button_height):
        # 创建一个按钮图像，参数设置按钮的文字，文字颜色，按钮颜色，按钮的高度
        font_size = button_height
        font = pg.font.SysFont(None, font_size)
        text_image = font.render(text, True, text_color, button_color)
        text_rect = text_image.get_rect()
        
        image = pg.Surface([text_rect.w + 10, button_height])
        text_rect.centerx = image.get_rect().centerx
        text_rect.centery = image.get_rect().centery
        image.fill(button_color)
        image.blit(text_image, text_rect)
        return image

    def setupButtons(self):
        # 创建开始按钮
        self.start_image = self.createButton('Start Game', (26, 173, 25), (158, 217, 157), 50)
        self.start_rect = self.start_image.get_rect()
        # 设置开始按钮图形的位置
        self.start_rect.x = 150
        self.start_rect.y = 250
        
        # 创建退出按钮
        self.quit_image = self.createButton('Quit Game', (230, 67, 64), (236, 139, 137), 50)
        self.quit_rect = self.quit_image.get_rect()
        # 设置退出按钮图形的位置
        self.quit_rect.x = 150
        self.quit_rect.y = 350

    def update(self, surface, current_time, mouse_pos):
        if mouse_pos is not None:
            # 有鼠标点击时，判断鼠标是否点击在按钮上
            x, y = mouse_pos
            if (x >= self.start_rect.x and x <= self.start_rect.right and
                y >= self.start_rect.y and y <= self.start_rect.bottom):
                # 点击开始按钮，设置下一个状态为关卡开始状态
                self.done = True
                self.next = c.LEVEL_START
            elif (x >= self.quit_rect.x and x <= self.quit_rect.right and
                y >= self.quit_rect.y and y <= self.quit_rect.bottom):
                self.done = True
                # 点击退出按钮，设置下一个状态为退出状态
                self.next = c.EXIT
        
        # 绘制主菜单界面
        surface.fill(c.LIGHTYELLOW)
        surface.blit(self.name_image, self.name_rect)
        surface.blit(self.start_image, self.start_rect)
        surface.blit(self.quit_image, self.quit_rect)

class Screen(tool.State):
    def __init__(self):
        tool.State.__init__(self)
        # 设置状态的结束定时器为 2 秒
        self.end_timer = 2000

    def startup(self, current_time, game_info):
        # 保存状态的开始时间
        self.start_time = current_time
        # 保存游戏信息
        self.game_info = game_info
        # 设置界面显示的文件图形
        self.setupTextImage()
        # 获取下一个状态
        self.next = self.getNextState()

    def setupTextImage(self):
        # 创建显示关卡信息的图形
        font = pg.font.SysFont(None, 50)
        # 根据游戏信息中的关卡值生成关卡信息
        level = 'Level - ' + str(self.game_info[c.LEVEL_NUM])
        self.level_image = font.render(level, True, c.SKY_BLUE, c.LIGHTYELLOW)
        self.level_rect = self.level_image.get_rect()
        # 设置关卡信息图形的位置
        self.level_rect.x = 170
        self.level_rect.y = 100
        
        self.text = self.getText()
        if self.text is not None:
            # 如果有文本信息，创建显示文本信息的图形
            font = pg.font.SysFont(None, 40)
            self.text_image = font.render(self.text, True, c.BLACK, c.LIGHTYELLOW)
            self.text_rect = self.text_image.get_rect()
            # 设置文本信息图形的位置
            self.text_rect.x = 180
            self.text_rect.y = 250

    def getNextState(self):
        # 返回下一个状态
        pass

    def getText(self):
        return None

    def update(self, surface, current_time, mouse_pos):
        if(current_time - self.start_time) < self.end_timer:
            # # 如果结束定时器没有超时，绘制界面
            surface.fill(c.LIGHTYELLOW)
            surface.blit(self.level_image, self.level_rect)
            if self.text is not None:
                surface.blit(self.text_image, self.text_rect)
        else:
            # 如果结束定时器超时，设置状态结束
            self.done = True

class LevelStartScreen(Screen):
    def __init__(self):
        Screen.__init__(self)

    def getNextState(self):
        return c.LEVEL

class LevelLoseScreen(Screen):
    def __init__(self):
        Screen.__init__(self)

    def getNextState(self):
        return c.MAIN_MENU

    def getText(self):
        return c.LEVEL_LOSE_INFO

class LevelWinScreen(Screen):
    def __init__(self):
        Screen.__init__(self)

    def getNextState(self):
        # 当前关卡胜利后，将关卡值加一
        self.game_info[c.LEVEL_NUM] += 1
        if self.game_info[c.LEVEL_NUM] <= c.MAX_LEVEL_NUM:
            return c.LEVEL_START
        else:
            # 如果已经是最后一个关卡了，则关卡值重设为初始关卡
            self.game_info[c.LEVEL_NUM] = c.START_LEVEL_NUM
            return c.MAIN_MENU

    def getText(self):
        return c.LEVEL_WIN_INFO
