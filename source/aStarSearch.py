from . import tool
from . import map

class SearchEntry():
    def __init__(self, x, y, g_cost, f_cost=0, pre_entry=None):
        # Store the node location
        
        self.x = x
        self.y = y
        # Store the G and F vals
        self.g_cost = g_cost
        self.f_cost = f_cost
        # Store the node's parent which named pre_entry
        self.pre_entry = pre_entry
    
    def getPos(self):
        # return entry vals
        return (self.x, self.y)


def AStarSearch(map, source, dest):
    def getNewPosition(map, locatioin, offset):
        # 位置 (x, y) 表示 location 节点的一个相邻节点
        x,y = (location.x + offset[0], location.y + offset[1])
        if not map.isValid(x, y) or not map.isMovable(x, y):
            # 如果位置 (x, y) 所在的地图格子是无效的或不可移动的，返回 None
            return None
        return (x, y)
        
    def getPositions(map, location):
        # 获取 location 节点所有的相邻节点
        offsets = tool.getMovePositions(location.x, location.y)
        poslist = []
        for offset in offsets:
            # 如果这个相邻节点是无效的或不可移动地，pos 值为 None
            pos = getNewPosition(map, location, offset)
            if pos is not None:
                poslist.append(pos)
        # 返回 location 节点所有有效且可移动的相邻节点列表
        return poslist

    def calHeuristic(map, pos, dest):
        # 返回从 pos 节点到 pos 节点的估计距离
        return map.calHeuristicDistance(dest.x, dest.y, pos[0], pos[1])

    def getMoveCost(location, pos):
        # 从 location 节点移动到 pos 节点的距离
        if location.x != pos[0] and location.y != pos[1]:
            return 1.4
        else:
            return 1

    def isInDict(d, pos):
        # 判断一个节点位置是否在字典中
        if pos in d:
            return d[pos]
        return None

    def addAdjacentPositions(map, location, dest, open_dict, closed_dict):
        # 获取 location 节点所有可移动的相邻位置
        poslist = getPositions(map, location)
        for pos in poslist:
            # 如果 pos 位置已经在 closed_dict 字典中，不用添加
            if isInDict(closed_dict, pos) is None:
                # 查看 pos 位置是否在 open_dict 字典中 
                findEntry = isInDict(open_dict, pos)
                h_cost = calHeuristic(map, pos, dest)
                # 计算从 location 节点所在位置移动到 pos 位置的 g_cost
                g_cost = location.g_cost + getMoveCost(location, pos)
                if findEntry is None :
                    # 如果 pos 位置不在 open_dict 字典中，创建一个节点对象添加到 open_dict 字典中
                    open_dict[pos] = SearchEntry(pos[0], pos[1], g_cost, g_cost + h_cost, location)
                elif findEntry.g_cost > g_cost:
                    # 如果 pos 位置在 open_dict 字典中，并且 findEntry 节点的 g_cost 
                    # 大于从 location 节点移动过来计算出的 g_cost
                    findEntry.g_cost = g_cost
                    findEntry.f_cost = g_cost + h_cost
                    # 更新 findEntry 节点的父节点为 location 节点
                    findEntry.pre_entry = location
    
    def getFastPosition(open_dict):
        # 初始化 fast 值为 None
        fast = None
        for entry in open_dict.values():
            # 在 open_dict 中找到一个 f_cost 值最小的节点
            if fast is None:
                fast = entry
            elif fast.f_cost > entry.f_cost:
                fast = entry
        # 如果 openlist 列表为空，返回 None
        return fast

    # open_dict 和 closed_dict 字典的 key 是节点在地图上的位置（x, y）
    open_dict = {}
    closed_dict = {}
    # 创建开始位置的节点对象
    location = SearchEntry(source[0], source[1], 0.0)
    # 创建终点位置的节点对象
    dest = SearchEntry(dest[0], dest[1], 0.0)
    # 将开始节点对象添加到 open_dict 字典中
    open_dict[source] = location

    while True:
        # 从 open_dict 字典中找到一个 f_cost 值最小的节点
        location = getFastPosition(open_dict)
        if location is None:
            # location 为 None，表示没有找到从开始位置到终点位置的路线
            print("can't find valid path")
            break;
        
        if location.x == dest.x and location.y == dest.y:
            # location 位置和终点位置一样，表示找到路线
            break
        
        # 将 location 节点添加到 closed_dict 字典中
        closed_dict[location.getPos()] = location
        # 将 location 节点从 open_dict 字典中删除
        open_dict.pop(location.getPos())
        # 添加 location 节点的相邻节点
        addAdjacentPositions(map, location, dest, open_dict, closed_dict)

    return location

def getFirstStepAndDistance(location):
    # 获取路径中开始位置的下一步位置和路径的距离
    distance = 0
    tmp = location
    while location.pre_entry is not None:
        distance += 1
        tmp = location
        location = location.pre_entry
    return (tmp.x, tmp.y, distance)

def getAStarDistance(map, source, dest):
    # 获取 source 位置到 dest 位置的路径距离。如果找不到路径，返回 None
    location = AStarSearch(map, source, dest)
    if location is not None:
        _, _, distance = getFirstStepAndDistance(location)
    else:
        distance = None
    return distance

def getPath(map, source, dest):
    # source 位置和 dest 位置相同时，返回 None
    if source[0] == dest[0] and source[1] == dest[1]:
        return None
    
    # 如果找到路径，返回 source 位置到 dest 位置的路径每一步的列表
    path = None
    location = AStarSearch(map, source, dest)
    if location is not None:
        path = []
        # location 节点起始时是 dest 位置
        while location.pre_entry is not None:
            # 按照从 dest 位置反方向添加到路径列表，最后一个是 source 的下一个位置
            path.append(location)
            location = location.pre_entry
        # 将路径列表反转，变成从source 的下一个位置到 dest 位置的路径列表
        path = path[::-1]
    return path

def getPosByDistance(location, distance):
    # 从路径的目的位置往前指定的距离 distance，返回得到的地图位置
    tmp = location
    while location.pre_entry is not None:
        if distance == 0:
            break
        location = location.pre_entry
        tmp = location
        distance -= 1
        
    return (tmp.x, tmp.y)