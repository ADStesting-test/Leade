import os
import json

import inflect


class ScenarioNode:
    def __init__(self, lane_id, distance):
        self.lane = lane_id
        self.dist = distance
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)


def traverse_tree(node):
    print(node.value)
    for child in node.children:
        traverse_tree(child)


def record_trees(tree):
    file_list = os.listdir("trees")
    path = "trees/tree" + str(len(file_list)+1)
    with open(path, 'w') as f:
        f.write(json.dumps(tree))


def rewrite_trees(tree):
    file_list = os.listdir("trees")
    path = "trees/tree" + str(len(file_list))
    with open(path, 'w') as f:
        f.write(json.dumps(tree))


def read_trees():
    file_list = os.listdir("trees")
    path = "trees/tree" + str(len(file_list))
    with open(path, 'r') as f:
        trees = f.read()
        trees = json.loads(trees)
        return trees


def refresh_trees(tree):
    trees = read_trees()
    npcs = trees['npcs']
    peds = trees['peds']
    new_npcs = tree['npcs']
    new_peds = tree['peds']
    for each in new_npcs:
        npcs.append(each)
    for item in new_peds:
        peds.append(item)
    trees['npcs'] = npcs
    trees['peds'] = peds
    rewrite_trees(trees)


# def create_scenario(scenario_trees, scenario_string):
#     npcs = scenario_trees['npcs']
#     peds = scenario_trees['peds']
#     blocks = scenario_string.split('\n\n')
#     for i in range(len(blocks)):
#         if '...' in blocks[i]:
#             tmp = blocks[i].split('...')
#             del blocks[i]
#             for tmp_each in tmp:
#                 blocks.append(tmp_each)
#     for block in blocks:
#         if 'npc' in block:
#             seg_points = find_all('->', block)
#             if len(seg_points) > 0:
#                 npc = []
#                 target_character = "_"
#                 for each in seg_points:
#                     result_char, dis = find_nearest_char(block, target_character, each)
#                     lane_id = block[each - dis + 1: each - 1]
#                     num = ""
#                     for i in range(each + 2, len(block)):
#                         if block[i].isdigit():
#                             num = num + block[i]
#                             continue
#                         else:
#                             break
#                     distance = num
#                     npc.append([lane_id, distance])
#                 npcs.append(npc)
#         elif 'ped' in block:
#             seg_points = find_all('->', block)
#             if len(seg_points) > 0:
#                 ped = []
#                 target_character = "_"
#                 for each in seg_points:
#                     result_char, dis = find_nearest_char(block, target_character, each)
#                     lane_id = block[each - dis + 1: each - 1]
#                     num = ""
#                     for i in range(each + 2, len(block)):
#                         if block[i].isdigit():
#                             num = num + block[i]
#                             continue
#                         else:
#                             break
#                     distance = num
#                     ped.append([lane_id, distance])
#                 peds.append(ped)
#
#     scenario_trees['npcs'] = npcs
#     scenario_trees['peds'] = peds
#
#     return scenario_trees


def create_scenario(scenario_trees, scenario_string):
    npcs = scenario_trees['npcs']
    peds = scenario_trees['peds']
    blocks = scenario_string.split('\n\n')
    for i in range(len(blocks)):
        if '...' in blocks[i]:
            tmp = blocks[i].split('...')
            del blocks[i]
            for tmp_each in tmp:
                blocks.append(tmp_each)
    for block in blocks:
        if 'npc' in block:
            seg_points = find_all('->', block)
            if len(seg_points) > 0:
                npc = []
                target_character = "_"
                for j in range(len(seg_points)):
                    each = seg_points[j]
                    result_char, dis = find_nearest_char(block, target_character, each)
                    lane_id = block[each - dis + 1: each - 1]
                    num = ""
                    for i in range(each + 2, len(block)):
                        if block[i].isdigit():
                            num = num + block[i]
                            continue
                        else:
                            break
                    distance = num
                    if j == len(seg_points)-1:
                        speed = 0
                    else:
                        result_char1, dis1 = find_nearest_char(block, ")", each)
                        speed_str = block[each + 1: each + dis1]
                        speed_str_array = speed_str.split(",")
                        for i in range(len(speed_str_array)):
                            if is_number(speed_str_array[len(speed_str_array) - 1]):
                                speed = speed_str_array[len(speed_str_array) - 1]
                                break
                    npc.append([lane_id, distance, speed])
                npcs.append(npc)
        elif 'ped' in block:
            seg_points = find_all('->', block)
            if len(seg_points) > 0:
                ped = []
                target_character = "_"
                for each in seg_points:
                    result_char, dis = find_nearest_char(block, target_character, each)
                    lane_id = block[each - dis + 1: each - 1]
                    num = ""
                    for i in range(each + 2, len(block)):
                        if block[i].isdigit():
                            num = num + block[i]
                            continue
                        else:
                            break
                    distance = num
                    ped.append([lane_id, distance])
                peds.append(ped)

    scenario_trees['npcs'] = npcs
    scenario_trees['peds'] = peds

    return scenario_trees


def is_number(s):
    try:  # 如果能运行float(s)语句，返回True（字符串s是浮点数）
        float(s)
        return True
    except ValueError:  # ValueError为Python的一种标准异常，表示"传入无效的参数"
        pass  # 如果引发了ValueError这种异常，不做任何事情（pass：不做任何事情，一般用做占位语句）
    try:
        import unicodedata  # 处理ASCii码的包
        unicodedata.numeric(s)  # 把一个表示数字的字符串转换为浮点数返回的函数
        return True
    except (TypeError, ValueError):
        pass
    return False


def find_all(sub, s):
    index_list = []
    index = s.find(sub)
    while index != -1:
        index_list.append(index)
        index = s.find(sub, index + 1)

    if len(index_list) > 0:
        return index_list
    else:
        return []


def find_nearest_char_to_char(input_str, target_char, search_char):
    positions = [pos for pos, char in enumerate(input_str) if char == target_char]

    if not positions:
        return None  # 如果目标字符不存在，返回 None

    result = {}
    for char_pos in positions:
        distance = min(abs(char_pos - i) for i, char in enumerate(input_str) if char == search_char)
        result[char_pos] = distance

    nearest_pos = min(result, key=result.get)
    nearest_distance = result[nearest_pos]

    return nearest_pos+1, nearest_distance


def find_nearest_char(s, target_char, position):
    min_distance = float('inf')
    nearest_char = None

    for i, char in enumerate(s):
        distance = abs(i - position)

        if char == target_char and distance < min_distance:
            min_distance = distance
            nearest_char = char

    return nearest_char, min_distance


def check_waypoints(tree):
    trees = read_trees()
    npcs = trees['npcs']
    peds = trees['peds']
    npc_lanes, ped_lanes = [], []
    for each in npcs:
        npc_lane = [npc[0] for npc in each]
        npc_lanes.append(npc_lane)
    for each in peds:
        ped_lane = [ped[0] for ped in each]
        ped_lanes.append(ped_lane)

    new_npcs = tree['npcs']
    new_peds = tree['peds']
    new_npc_lanes, new_ped_lanes = [], []
    npc_repeated, ped_repeated = [], []
    for each in new_npcs:
        new_npc_lane = [new_npc[0] for new_npc in each]
        repeated = False
        for i in npc_lanes:
            if new_npc_lane == i:
                npc_repeated.append(True)
                repeated = True
                break
        if not repeated:
            npc_repeated.append(False)
    for each in new_peds:
        new_ped_lane = [new_ped[0] for new_ped in each]
        repeated = False
        for i in ped_lanes:
            if new_ped_lane == i:
                ped_repeated.append(True)
                repeated = True
                break
        if not repeated:
            ped_repeated.append(False)

    feedback_repeated_npc, feedback_repeated_ped = [], []
    p = inflect.engine()
    for i in range(len(npc_repeated)):
        if npc_repeated[i]:
            # ordinal = p.number_to_words(i+1, ordinal=True)
            ordinal = p.ordinal(i+1)
            feedback_repeated_npc.append(ordinal)
    for i in range(len(ped_repeated)):
        if ped_repeated[i]:
            ordinal = p.ordinal(i+1)
            feedback_repeated_ped.append(ordinal)
    feedback_string = "The "
    if len(feedback_repeated_npc) > 0:
        npc_ordinal = ""
        for each in feedback_repeated_npc:
            npc_ordinal = npc_ordinal + each + " "
        feedback_string = feedback_string + npc_ordinal + "npc's waypoints in the following scenario are similar to some npc in previously generated scenarios. Please generate distinct waypoints for the " + npc_ordinal + "npc to generate a new scenario and can make egoVehicle collide with npc. "
    if len(feedback_repeated_ped) > 0:
        npc_ordinal = ""
        for each in feedback_repeated_ped:
            npc_ordinal = npc_ordinal + each + " "
        feedback_string = feedback_string + npc_ordinal + "ped's waypoints in the following scenario are similar to some ped in previously generated scenarios. Please generate distinct waypoints for the  " + npc_ordinal + "ped to generate a new scenario and can make egoVehicle collide with ped."
    if len(feedback_repeated_npc) > 0 or len(feedback_repeated_ped) > 0:
        return feedback_string
    else:
        return None
    # else:
        # map_path = "configuration/map/SanFrancisco.xodr"
        # network = Network.fromFile(map_path)
        #
        # ego_init_lane = network.laneAt(Vector(-12.5, -54.5))
        # ego_init_road = network.roadAt(Vector(-12.5, -54.5))

    # print("finish")
    # lane如果属于同一个road，则可以；若不属于同一个road，需要中间存在连接道路


if __name__ == '__main__':
    # with open("scenario_description/scenario_folder1/scenario_3", "r") as f:
    #     scenario = f.read()
    # trees = create_scenario({"npcs": [], "peds": []}, scenario)
    # record_trees(trees)
    with open("scenario_description/scenario_folder1/scenario_9", "r") as f:
        scenario = f.read()
    new_tree = create_scenario({"npcs": [], "peds": []}, scenario)
    # feedback = check_waypoints(trees)
    # if feedback is None:
    #     refresh_trees(new_tree)
    print("video")

