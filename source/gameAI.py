from . import map
from . import tool, aStarSearch

class EnemyInfo():
    def __init__(self, entity, enemy, location, distance, damage_half):
        # 保存敌方生物
        self.enemy = enemy
        # 保存目的位置
        self.location = location
        # 保存到目的位置的路径距离
        self.distance = distance
        # 要经过几轮行动攻击到敌方生物
        if distance == 0:
            self.round_num = 0
        else:
            self.round_num = (distance - 1) // entity.attr.distance
        # 敌方生物要攻击几次才会死亡
        hurt = entity.attr.getHurt(enemy.attr, damage_half)
        self.kill_time = (enemy.health-1) // hurt       
        # 敌方生物是否是远程生物
        self.remote = enemy.attr.remote
         
def getAction(entity, map, enemy_group):
    def getDestination(entity, map, enemy):
        # 获取敌方生物相邻的可攻击地图位置中和行动生物距离最近的地图位置
        dir_list = tool.getAttackPositions(enemy.map_x, enemy.map_y)
        best_pos = None
        min_dis = 0
        for offset_x, offset_y in dir_list:
            x, y = enemy.map_x + offset_x, enemy.map_y + offset_y
            if map.isValid(x, y) and map.isMovable(x, y):
                # 这个相邻地图位置是有效且可移动，获取和行动生物的路径距离
                distance = aStarSearch.getAStarDistance(map, (entity.map_x, entity.map_y), (x, y))
                if distance is None:
                    # distance 为 None，表示这个相邻位置不可到达
                    continue
                if best_pos is None:
                    best_pos = (x, y)
                    min_dis =  distance
                elif distance < min_dis:
                    # 保存路径距离最近的相邻地图位置
                    best_pos = (x, y)
                    min_dis =  distance
        return best_pos
    
    # 创建敌方生物信息列表
    info_list = []
    # 保存最佳的敌方生物
    best_info = None
    # 行动生物是否可以进行远程攻击
    remote_attack = entity.canRemoteAttack(map)
    
    # 遍历敌方生物组中每一个生物，检查生物的地图位置
    for enemy in enemy_group:
        if remote_attack:
            location = None
            distance = 0
        else:
            if tool.isNextToEntity(entity, enemy):
                # 如果敌方生物在相邻的地图格子，不用移动就可以攻击到
                destination = (entity.map_x, entity.map_y)       
            else:
                # 否则找到敌方生物的相邻地图格子中和行动生物距离最近的格子位置
                destination = getDestination(entity, map, enemy)
            
            if destination is None:
                # 表示不能行走到这个敌方生物的相邻可攻击的地图位置
                continue

            # 获取路径对象 location 和路径距离 distance
            location = aStarSearch.AStarSearch(map, (entity.map_x, entity.map_y), destination)
            _, _, distance = aStarSearch.getFirstStepAndDistance(location)
        
        # 判断基础伤害是否要减半
        if entity.attr.remote and not remote_attack:
            # 如果是远程生物且进行近战攻击，基础伤害减半
            damage_half = True
        else:
            damage_half = False
        # 创建 EnemyInfo 类对象
        enemyinfo = EnemyInfo(entity, enemy, location, distance, damage_half)
        # 添加到敌方生物信息列表
        info_list.append(enemyinfo)

    # 遍历可以攻击到的敌方生物信息列表，按照设定的策略选择最佳的敌方生物
    for info in info_list:
        if best_info == None:
            best_info = info
        else:
            if info.round_num < best_info.round_num:
                # 选择攻击前需要行动轮数较小的敌方生物
                best_info = info
            elif info.round_num == best_info.round_num:
                # 攻击前需要行动轮数相同时，比较其他属性
                if info.round_num == 0:
                    # 如果本轮行动可以攻击到
                    if info.kill_time < best_info.kill_time:
                        # 选择杀死敌方生物需要的攻击次数最少的
                        best_info = info
                    elif info.kill_time == best_info.kill_time:
                        # 如果杀死敌方生物需要的攻击次数相同
                        if info.remote == True and best_info.remote == False:
                            # 优先选择敌方的远程生物
                            best_info = info
                        elif info.distance < best_info.distance:
                            # 优先选择距离更近的敌方生物
                            best_info = info
                else:
                    # 如果至少下一轮行动才能攻击到敌方生物时
                    if info.distance < best_info.distance:
                        # 优先选择距离更近的敌方生物
                        best_info = info
    
    # 根据最佳敌方生物的行动轮数，选择行动策略
    if best_info.round_num == 0:
        # 本轮行动可以攻击到
        if best_info.location is None:
            # 目的位置为 None, 表示行动生物进行远程攻击
            return (None, best_info.enemy)
        else:
            # 目的位置不为 None, 表示行动生物进行近战攻击
            return ((best_info.location.x, best_info.location.y), best_info.enemy)
    elif best_info.round_num == 1:
        # 下一轮行动可以攻击到，本轮行走的距离，正好使下一轮能攻击到敌方生物
        distance = entity.attr.distance
        x, y = aStarSearch.getPosByDistance(best_info.location, distance)
        return ((x, y), None)
    else:
        # 至少二轮行动才能攻击到敌方生物时，本轮行走最大的距离
        distance = best_info.distance - entity.attr.distance
        x, y = aStarSearch.getPosByDistance(best_info.location, distance)
        return ((x, y), None)
