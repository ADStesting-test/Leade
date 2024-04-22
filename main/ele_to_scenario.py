import json
import math
import os
import random

vehicle_dic = list()
vehicle_behavior_dic = list()
pedestrian_dic = list()
pedestrian_behavior_dic = list()
road_dic = list()
position_dic = list()
with open("configuration/dict/vehicle.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        vehicle_dic.append(line.strip())
with open("configuration/dict/vehicle_behavior.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        vehicle_behavior_dic.append(line.strip())
with open("configuration/dict/pedestrian_behavior.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        pedestrian_behavior_dic.append(line.strip())
with open("configuration/dict/pedestrian.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        pedestrian_dic.append(line.strip())
with open("configuration/dict/road.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        road_dic.append(line.strip())
with open("configuration/dict/position.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        position_dic.append(line.strip())
path = "configuration/map/map_lanes"
f = open(path, encoding='utf-8')
map_json = json.load(f)
f.close()


def custom_random(num):
    if num == 2:
        return 0
    else:
        return random.randint(0, num/2-1)
# def custom_random(num):
#     probabilities = []
#     if num == 2:
#         return random.choice([0, 1])
#     else:
#         rate = 0.8/(num-2)
#         probabilities.append(0.1)
#         for i in range(num-2):
#             probabilities.append(rate)
#         probabilities.append(0.1)
#
#     rand_num = random.random()
#     total = 0
#     for i in range(num):
#         total = total + probabilities[i]
#         if rand_num < total:
#             return i

vertical = 99
parallel = 79


def pics_to_scenario_program(abs):
    # abs = parse_pic_string(gpt_response)
    vehicles = abs[1]
    pedestrians = abs[2]
    weather = abs[0]
    road = abs[3]
    sign = abs[4]
    pitched = False
    lanes = []
    ego_dest = []
    ego_dest_length = random.randint(vertical-10, vertical)
    if len(road) == 0:
        this_road = "N"
        map_lanes = map_json["straight"]
        ego_road = random.choice(map_lanes)
        lane_index = custom_random(len(ego_road))
        lanes = ego_road
        ego_lane = ego_road[lane_index]
        for j in range(int(len(ego_road)/2)):
            ego_dest.append(ego_road[j])
    else:
        for i in range(len(road)):
            if road[i] in ["intersection", "t - junction", "t-junction", "junction", "crossing", "turnaround", "turning"]:
                pitched = True
                this_road = road[i]
                map_lanes = map_json["intersection"]
                lanes = random.choice(map_lanes)
                ego_road = lanes[0]
                lane_index = custom_random(len(ego_road))
                ego_lane = ego_road[lane_index]
                for j in range(int(len(lanes[2])/2)):
                    ego_dest.append(lanes[2][j])
                for j in range(int(len(lanes[-1])/2)):
                    ego_dest.append(lanes[2][j])
                for j in range(int(len(lanes[1])/2), len(lanes[1])):
                    ego_dest.append(lanes[2][j])
                ego_dest_length = random.randint(min(vertical, parallel) - 10, min(vertical, parallel))
                break
            else:
                if i == len(road) - 1:
                    this_road = road[0]
                    map_lanes = map_json["straight"]
                    ego_road = random.choice(map_lanes)
                    lane_index = custom_random(len(ego_road))
                    lanes = ego_road
                    ego_lane = ego_road[lane_index]
                    for j in range(int(len(ego_road) / 2)):
                        ego_dest.append(ego_road[j])
                else:
                    continue

    ego_dest = random.choice(ego_dest)
    npcs = "{"
    peds = "{"

    scenario_string = "map_name = \"san_francisco\"; \n\n"
    scenario_string = scenario_string + "car_model = \"Lincoln MKZ 2017\";\n"
    scenario_string = scenario_string + "ego_init_position = \"lane_" + str(ego_lane) + "\"->" +str(random.randint(5, 25)) + ";\n"
    scenario_string = scenario_string + "ego_init_state = (ego_init_position);\n"
    scenario_string = scenario_string + "ego_target_position = \"lane_" + str(ego_dest) + "\"->" +str(ego_dest_length) + ";\n"
    scenario_string = scenario_string + "ego_target_state = (ego_target_position);\n"
    scenario_string = scenario_string + "vehicle_type = (car_model);\n"
    scenario_string = scenario_string + "ego_vehicle = AV(ego_init_state, ego_target_state,vehicle_type);"
    scenario_phases_1 = scenario_string + "\n\n"
    scenario_phases_2 = scenario_string + "\n\n"
    for i in range(len(vehicles)):
        lanes_1, lanes_2 = [], []
        this_position, this_behaviors, this_direction = [], [], []
        vehicle_json = vehicles[i]
        vehicle_type = get_vehicle_type(vehicle_json['vehicles'][0])
        vehicle_position = vehicle_json['position']
        vehicle_direction = vehicle_json['direction']
        vehicle_behaviors = vehicle_json['behaviors']
        for each in vehicle_position:
            if each[0] in position_dic:
                this_position.append(each[0])
        for each in vehicle_behaviors:
            this_behaviors.append(each[0])
        for each in vehicle_direction:
            if each[0] in position_dic:
                this_direction.append(each[0])
        tmp_position, tmp_direction = "N", "N"
        waypoints_1, waypoints_2 = [], []
        speed_1, speed_2 = [], []
        if pitched:
            degree = 90
        else:
            degree = 0
        if len(this_position) > 0:
            tmp_position = this_position[0]
        if len(this_direction) > 0:
            tmp_direction = this_direction[0]
        this_lanes = get_vehicle_lane(this_road, lanes, lane_index, this_behaviors[0], tmp_position, tmp_direction)
        lanes_1.append(this_lanes[0])
        lanes_1.append(this_lanes[1])
        lanes_2.append(this_lanes[2])
        lanes_2.append(this_lanes[3])
        if this_behaviors[0] in ["wait", "stop", "park"]:
            if this_road in ["intersection", "t - junction", "t-junction", "junction", "crossing", "turnaround", "turning"]:
                if -1 > lanes_1[0] > -11:
                    # right
                    selector = random.choice([1,2])
                    if selector == 1:
                        lanes_1[0] = lanes[-1][random.randint(0, int(len(lanes[-1])/2) - 1)]
                        waypoints_1.append(random.randint(0,20))
                    else:
                        lanes_1[0] = lanes[-1][random.randint(int(len(lanes[-1])/2), len(lanes[-1])-1)]
                        waypoints_1.append(random.randint(parallel-10, parallel))
                    waypoints_1.append(waypoints_1[-1])
                    lanes_1[1] = lanes_1[0]
                    waypoints_2.append(random.randint(int(vertical/2), vertical))
                    waypoints_2.append(waypoints_2[-1])
                elif lanes_1[0] < -99:
                    # left
                    selector = random.choice([1, 2])
                    if selector == 1:
                        lanes_1[0] = lanes[1][random.randint(0, int(len(lanes[-1]) / 2) - 1)]
                        waypoints_1.append(random.randint(vertical-10, vertical))
                    else:
                        lanes_1[0] = lanes[1][random.randint(int(len(lanes[-1]) / 2), len(lanes[-1]) - 1)]
                        waypoints_1.append(random.randint(0, 15))
                    waypoints_1.append(waypoints_1[-1])
                    lanes_1[1] = lanes_1[0]
                    waypoints_2.append(random.randint(int(vertical/2), vertical))
                    waypoints_2.append(waypoints_2[-1])
                elif lanes_1[0] in lanes[2]:
                    for n in range(int(len(lanes[2])/2)):
                        if lanes_1[0] == lanes[2][n]:
                            waypoints_1.append(random.randint(0, 10))
                            waypoints_1.append(waypoints_1[-1])
                    # opposite
                        if lanes_2[0] == lanes[2][n]:
                            waypoints_2.append(random.randint(0, 10))
                            waypoints_2.append(waypoints_2[-1])
                    for n in range(int(len(lanes[2])/2), len(lanes[2])):
                        if lanes_1[0] == lanes[2][n]:
                            waypoints_1.append(random.randint(vertical-10, vertical))
                            waypoints_1.append(waypoints_1[-1])
                    # opposite
                        if lanes_2[0] == lanes[2][n]:
                            waypoints_2.append(random.randint(vertical-10, vertical))
                            waypoints_2.append(waypoints_2[-1])
                else:
                    waypoints_1.append(random.randint(int(vertical/2), vertical))
                    waypoints_1.append(waypoints_1[-1])
                    waypoints_2.append(random.randint(int(vertical/2), vertical))
                    waypoints_2.append(waypoints_2[-1])
            else:
                waypoints_1.append(random.randint(int(vertical/2), vertical))
                waypoints_1.append(waypoints_1[-1])
                waypoints_2.append(random.randint(int(vertical/2), vertical))
                waypoints_2.append(waypoints_2[-1])
            speed_1.append(0)
            speed_1.append(0)
            speed_2.append(0)
            speed_2.append(0)
        else:
            waypoints_1.append(random.randint(25, 35))
            waypoints_1.append(waypoints_1[-1] + random.randint(5, 25))
            waypoints_2.append(random.randint(25, 35))
            waypoints_2.append(waypoints_2[-1] + random.randint(5, 25))
            speed_1.append(random.randint(6,10))
            speed_1.append(random.randint(6,10))
            speed_2.append(random.randint(6,10))
            speed_2.append(random.randint(6,10))
        for j in range(1, len(this_behaviors)):
            if len(this_position) > j:
                tmp_position = this_position[j]
            if len(this_direction) > j:
                tmp_direction = this_direction[j]
            this_lanes_1 = get_vehicle_next_lane(lanes, lanes_1, this_road, this_behaviors[j], tmp_direction)
            this_lanes_2 = get_vehicle_next_lane(lanes, lanes_2, this_road, this_behaviors[j], tmp_direction)
            lanes_1.append(this_lanes_1)
            lanes_2.append(this_lanes_2)

        if len(lanes_1) > 2:
            for count in range(2, len(lanes_1)):
                if this_behaviors[count-1] in ["wait", "stop", "park"]:
                    speed_1.append(0)
                    waypoints_1.append(waypoints_1[-1] + 5)
                else:
                    speed_1.append(random.randint(4,10))
                    waypoints_1.append(waypoints_1[-1]+random.randint(5, 25))
        if len(lanes_2) > 2:
            for count in range(2, len(lanes_2)):
                if this_behaviors[count - 1] in ["wait", "stop", "park"]:
                    speed_2.append(0)
                    waypoints_2.append(waypoints_2[-1] + 5)
                else:
                    speed_2.append(random.randint(4, 10))
                    waypoints_2.append(waypoints_2[-1] + random.randint(5, 25))

        scenario_phases_1 = scenario_phases_1 + "npc" + str(i + 1) + "_type = \"" + vehicle_type + "\";\n"
        scenario_phases_2 = scenario_phases_2 + "npc" + str(i + 1) + "_type = \"" + vehicle_type + "\";\n"
        scenario_phases_1 = scenario_phases_1 + "npc" + str(i + 1) + "_heading = " + str(degree) + " deg related to ego_vehicle;\n" + "npc" + str(i + 1) + "_init_position = "
        scenario_phases_1 = scenario_phases_1 + "(\"lane_" + str(lanes_1[0]) + "\"->" + str(waypoints_1[0]) + ");\n" + "npc" + str(
            i + 1) + "_init_state = (npc" + str(i + 1) + "_init_position, npc" + str(i + 1) + "_heading," + str(speed_1[0]) + ");\n"
        scenario_phases_1 = scenario_phases_1 + "npc" + str(i + 1) + "_waypoints = Waypoint("
        scenario_phases_1 = scenario_phases_1 + "(\"lane_" + str(lanes_1[0]) + "\"->" + str(waypoints_1[0]) + ", ," + str(speed_1[0]) + "),"
        for j in range(1, len(lanes_1)):
            scenario_phases_1 = scenario_phases_1 + "(\"lane_" + str(lanes_1[j]) + "\"->" + str(waypoints_1[j]) + ", ," + str(speed_1[j]) + "),"
        scenario_phases_1 = scenario_phases_1 + ");\n"
        scenario_phases_1 = scenario_phases_1 + "npc" + str(i + 1) + "_destination = (\"lane_" + str(
            lanes_1[-1]) + "\"->" + str(waypoints_1[-1]) + ");\n"
        scenario_phases_1 = scenario_phases_1 + "npc" + str(i + 1) + "_destination_state = (npc" + str(
            i + 1) + "_destination);\n"
        scenario_phases_1 = scenario_phases_1 + "npc" + str(i + 1) + "=Vehicle(npc" + str(i + 1) + "_init_state, npc" + str(
            i + 1) + "_waypoints, npc" + str(i + 1) + "_destination, npc" + str(i + 1) + "_type); \n\n"

        scenario_phases_2 = scenario_phases_2 + "npc" + str(i + 1) + "_heading = " + str(
            0) + " deg related to ego_vehicle;\n"+"npc" + str(i + 1) + "_init_position = "
        scenario_phases_2 = scenario_phases_2 + "(\"lane_" + str(lanes_2[0]) + "\"->" + str(
            waypoints_2[0]) + "); \n" + "npc" + str(
            i + 1) + "_init_state = (npc" + str(i + 1) + "_init_position, npc" + str(i + 1) + "_heading," + str(speed_2[0]) + "); \n"
        scenario_phases_2 = scenario_phases_2 + "npc" + str(i + 1) + "_waypoints = Waypoint("
        scenario_phases_2 = scenario_phases_2 + "(\"lane_" + str(lanes_2[0]) + "\"->" + str(waypoints_2[0]) + ", ," + str(speed_2[0]) + "),"
        for j in range(1, len(lanes_2)):
            scenario_phases_2 = scenario_phases_2 + "(\"lane_" + str(lanes_2[j]) + "\"->" + str(
                waypoints_1[j]) + ", ," + str(speed_2[j]) + "),"
        scenario_phases_2 = scenario_phases_2 + "); \n"
        scenario_phases_2 = scenario_phases_2 + "npc" + str(i + 1) + "_destination = (\"lane_" + str(
            lanes_2[-1]) + "\"->" + str(waypoints_2[-1]) + "); \n"
        scenario_phases_2 = scenario_phases_2 + "npc" + str(i + 1) + "_destination_state = (npc" + str(
            i + 1) + "_destination); \n"
        scenario_phases_2 = scenario_phases_2 + "npc" + str(i + 1) + "=Vehicle(npc" + str(
            i + 1) + "_init_state, npc" + str(
            i + 1) + "_waypoints, npc" + str(i + 1) + "_destination, npc" + str(i + 1) + "_type); \n\n"
        npcs = npcs + "npc" + str(i+1) + ","

    npcs = npcs + "}; "

    for i in range(len(pedestrians)):
        lanes_1, lanes_2 = [], []
        this_position, this_behaviors, this_direction = [], [], []
        pedestrian_json = vehicles[i]
        pedestrian_position = pedestrian_json['position']
        pedestrian_direction = pedestrian_json['direction']
        pedestrian_behaviors = pedestrian_json['behaviors']
        for each in pedestrian_position:
            if each[0] in position_dic:
                this_position.append(each[0])
        for each in pedestrian_behaviors:
            this_behaviors.append(each[0])
        for each in pedestrian_direction:
            if each[0] in position_dic:
                this_direction.append(each[0])
        tmp_position, tmp_direction = "N", "N"
        waypoints_1, waypoints_2 = [], []
        speed_1, speed_2 = [], []
        if len(this_position) > 0:
            tmp_position = this_position[0]
        if len(this_direction) > 0:
            tmp_direction = this_direction[0]
        this_lanes = get_ped_lane(this_road, lanes, lane_index, this_behaviors[0], tmp_position, tmp_direction)
        lanes_1.append(this_lanes[0])
        lanes_1.append(this_lanes[1])
        lanes_2.append(this_lanes[2])
        lanes_2.append(this_lanes[3])
        for w in this_lanes[4]:
            waypoints_1.append(w)
        for w in this_lanes[5]:
            waypoints_2.append(w)
        if this_behaviors[0] in ["wait", "stop", "look", "stand"]:
            speed_1.append(0)
            speed_1.append(0)
            speed_2.append(0)
            speed_2.append(0)
        else:
            speed_1.append(random.randint(1,3))
            speed_1.append(random.randint(1,3))
            speed_2.append(random.randint(1,3))
            speed_2.append(random.randint(1,3))
        for j in range(1, len(this_behaviors)):
            if len(this_position) > j:
                tmp_position = this_position[j]
            if len(this_direction) > j:
                tmp_direction = this_direction[j]
            this_lanes_1, this_waypoint_1 = get_ped_lane_next(lanes, lanes_1, this_road, this_behaviors[j], tmp_direction)
            this_lanes_2, this_waypoint_2 = get_ped_lane_next(lanes, lanes_2, this_road, this_behaviors[j], tmp_direction)
            lanes_1.append(this_lanes_1)
            lanes_2.append(this_lanes_2)
            if this_waypoint_1 == -1:
                waypoints_1.append(waypoints_1[-1])
            else:
                waypoints_1.append(this_waypoint_1)
            if this_waypoint_2 == -1:
                waypoints_2.append(waypoints_2[-1])
            else:
                waypoints_2.append(this_waypoint_2)

        if len(lanes_1) > 2:
            for count in range(2, len(lanes_1)):
                if this_behaviors[count-1] in ["wait", "stop", "look", "stand"]:
                    waypoints_1[-1] = waypoints_1[-1] + 1
                    speed_1.append(0)
                else:
                    speed_1.append(random.randint(1,3))
        if len(lanes_2) > 2:
            for count in range(2, len(lanes_2)):
                if this_behaviors[count - 1] in ["wait", "stop", "look", "stand"]:
                    waypoints_2[-1] = waypoints_2[-1] + 1
                    speed_2.append(0)
                else:
                    speed_2.append(random.randint(1,3))

        scenario_phases_1 = scenario_phases_1 + "ped" + str(i + 1) + "_position = \"lane_" + str(lanes_1[0]) + "\"->" + str(waypoints_1[0]) + ";\n"
        scenario_phases_1 = scenario_phases_1 + "ped" + str(i+1) + "_init_state= (ped_position, , " + str(speed_1[0]) + ");\n"
        scenario_phases_1 = scenario_phases_1 + "ped" + str(i + 1) + "_waypoints = Waypoint("
        scenario_phases_1 = scenario_phases_1 + "(\"lane_" + str(lanes_1[0]) + "\"->" + str(waypoints_1[0]) + ", ," + str(speed_1[0]) + "),"
        for j in range(1, len(lanes_1)):
            scenario_phases_1 = scenario_phases_1 + "(\"lane_" + str(lanes_1[j]) + "\"->" + str(waypoints_1[j]) + ", ," + str(speed_1[j]) + "),"
        scenario_phases_1 = scenario_phases_1 + "); \n"
        scenario_phases_1 = scenario_phases_1 + "ped" + str(i + 1) + "_destination_state = (\"lane_" + str(
            lanes_1[-1]) + "\"->" + str(waypoints_1[-1]) + "); \n"
        scenario_phases_1 = scenario_phases_1 + "ped" + str(i + 1) + "=Pedestrian(ped" + str(i + 1) + "_init_state, ped" + str(
            i + 1) + "_waypoints, ped" + str(i + 1) + "_destination_state); \n\n"

        scenario_phases_2 = scenario_phases_2 + "ped" + str(i + 1) + "_position = \"lane_" + str(
            lanes_2[0]) + "\"->" + str(waypoints_2[0]) + ";\n"
        scenario_phases_2 = scenario_phases_2 + "ped" + str(i+1) + "_init_state= (ped_position, , " + str(speed_2[0]) + ");\n"
        scenario_phases_2 = scenario_phases_2 + "ped" + str(i + 1) + "_waypoints = Waypoint("
        scenario_phases_2 = scenario_phases_2 + "(\"lane_" + str(lanes_2[0]) + "\"->" + str(waypoints_2[0]+1) + ", ," + str(speed_2[0]) + "),"
        for j in range(1, len(lanes_2)):
            scenario_phases_2 = scenario_phases_2 + "(\"lane_" + str(lanes_2[j]) + "\"->" + str(
                waypoints_2[j]) + ", ," + str(speed_2[j]) + "),"
        scenario_phases_2 = scenario_phases_2 + "); \n"
        scenario_phases_2 = scenario_phases_2 + "ped" + str(i + 1) + "_destination_state = (\"lane_" + str(
            lanes_2[-1]) + "\"->" + str(waypoints_2[-1]) + "); \n"
        scenario_phases_2 = scenario_phases_2 + "ped" + str(i + 1) + "=Pedestrian(ped" + str(
            i + 1) + "_init_state, ped" + str(
            i + 1) + "_waypoints, ped" + str(i + 1) + "_destination_state); \n\n"
        peds = peds + "ped" + str(i + 1) + ","

    peds = peds + "}; "

    whole_weather = ""
    for each in weather:
        whole_weather = whole_weather + each + " "
    results = check_fog(whole_weather)
    if True in results:
        fog = round(random.uniform(0.5,1.0), 1)
    else:
        fog = round(random.uniform(0.0, 0.3), 1)
    results = check_cloud(whole_weather)
    if True in results:
        cloud = round(random.uniform(0.5, 1.0), 1)
    else:
        cloud = round(random.uniform(0.0, 0.3), 1)
    results = check_sun(whole_weather)
    if True in results:
        fog = 0.0
        cloud = 0.0
        sun = round(random.uniform(0.5, 1.0), 1)
    else:
        sun = round(random.uniform(0.1, 0.3), 1)
    results = check_wet(whole_weather)
    if True in results:
        wet = round(random.uniform(0.5, 1.0), 1)
    else:
        wet = 0.0
    results = check_rain(whole_weather)
    if True in results:
        rain = round(random.uniform(0.5,1.0), 1)
    else:
        rain = round(random.uniform(0.0, 0.3), 1)

    scenario_phases_1 = scenario_phases_1 + "time = 9:00; \n"
    scenario_phases_1 = scenario_phases_1 + "weather = {rain:" + str(rain) + ", fog:" + str(fog) + ", wetness:" + str(wet) + ", sunny:" + str(sun) + ", cloudiness:" + str(cloud) + "}; \n"
    scenario_phases_1 = scenario_phases_1 + "evn = Environment(time, weather); \n\n"
    scenario_phases_1 = scenario_phases_1 + "scenario0 = CreateScenario{load(map_name); ego_vehicle; " + npcs + peds + " {}; evn};"
    scenario_phases_2 = scenario_phases_2 + "time = 9:00; \n"
    scenario_phases_2 = scenario_phases_2 + "weather = {rain:" + str(rain) + ", fog:" + str(fog) + ", wetness:" + str(wet) + ", sunny:" + str(sun) + ", cloudiness:" + str(cloud) + "}; \n"
    scenario_phases_2 = scenario_phases_2 + "evn = Environment(time, weather); \n\n"
    scenario_phases_2 = scenario_phases_2 + "scenario0 = CreateScenario{load(map_name); ego_vehicle; " + npcs + peds + " {}; evn};"

    # scenario_1 = add_specifications(scenario_phases_1)
    # scenario_2 = add_specifications(scenario_phases_2)

    scenario_folders = os.listdir("scenario_description")
    folder_path = "scenario_description/scenario_folder" + str(len(scenario_folders)+1)
    os.makedirs(folder_path)
    with open(folder_path+"/scenario_1.txt", 'w') as f:
        f.write(scenario_phases_1)
    with open(folder_path+"/scenario_2.txt", 'w') as f:
        f.write(scenario_phases_2)

    return scenario_phases_1, scenario_phases_2, lanes

def add_specifications(scenario):
    scenario = scenario + "\n" + "Trace trace = EXE(scenario0);" + "\n\n"
    scenario = scenario + "ego_vehicle_state= trace[ego];" + "\n\n"
    scenario = scenario + "dis_target = dis(ego_vehicle_state, ego_target_position);" + "\n\n"
    statement = 0
    vehicle_num = scenario.count("Vehicle")
    ped_num = scenario.count("Pedestrian")
    for i in range(1, vehicle_num+1):
        statement = statement + 1
        scenario = scenario + "npc_vehicle"+str(i)+"= trace[perception][npc;"+str(i)+"];" + "\n"
        scenario = scenario + "npc_vehicle" + str(i) + "_truth= trace[truth][npc;" + str(i) + "];" + "\n"
        scenario = scenario + "dis" + str(statement) + "= dis(ego_vehicle_state, npc_vehicle"+str(i) + ");" + "\n"
        scenario = scenario + "statement" + str(statement) + "= dis" + str(i) + ">= 0.5;" + "\n"

    for i in range(1, ped_num+1):
        statement = statement + 1
        scenario = scenario + "pedestrian"+str(i)+"= trace[perception][ped;"+str(i)+"];" + "\n"
        scenario = scenario + "pedestrian" + str(i) + "_truth= trace[truth][ped;" + str(i) + "];" + "\n"
        scenario = scenario + "dis" + str(statement) + "= dis(ego_vehicle_state, pedestrian"+str(i) + ");" + "\n"
        scenario = scenario + "statement" + str(statement) + "= dis" + str(i) + ">= 0.5;" + "\n"

    scenario = scenario + "\n" + "trace |= (G(statement1"
    for j in range(2, statement+1):
        scenario = scenario + " & statement" + str(j)
    scenario = scenario + ")) & (F dis_target <= 2.0);"

    return scenario


def check_fog(external_string):
    strings = ["fog", "foggy", "ice fog", "ground fog", "dust", "dusty"]
    results = []
    for string in strings:
        if string in external_string:
            results.append(True)
        else:
            results.append(False)
    return results


def check_rain(external_string):
    strings = ["rain", "rainy", "snow", "snowy"]
    results = []
    for string in strings:
        if string in external_string:
            results.append(True)
        else:
            results.append(False)
    return results


def check_wet(external_string):
    strings = ["precipitation", "ice crystals", "ice pellets", "snowy", "snowy", "rainy", "rain", "ice"]
    results = []
    for string in strings:
        if string in external_string:
            results.append(True)
        else:
            results.append(False)
    return results


def check_sun(external_string):
    strings = ["sun", "sunny"]
    results = []
    for string in strings:
        if string in external_string:
            results.append(True)
        else:
            results.append(False)
    return results


def check_cloud(external_string):
    strings = ["cloud", "cloudy", "cloudiness"]
    results = []
    for string in strings:
        if string in external_string:
            results.append(True)
        else:
            results.append(False)
    return results


def get_vehicle_type(vehicle):
    if vehicle in ["truck", "bus", "van"]:
        return "SchoolBus"
    elif vehicle in ["suv"]:
        return "SUV"
    else:
        return "Sedan"


def get_vehicle_lane(road_type, lanes, lane_index, behavior, position, direction):
    initial_lane_1, dest_lane_1, initial_lane_2, dest_lane_2 = -1, -1, -1, -1
    candidate_lanes_1, candidate_dest_1, candidate_lanes_2, candidate_dest_2 = [], [], [], []
    if road_type in ["intersection", "t - junction", "t-junction", "junction", "crossing", "turnaround", "turning", "residential", "sidewalk", "crosswalk", "living area"]:
        road_index = 0
        ego_lane = lanes[0][lane_index]
        # for i in range(len(lanes)):
        #     if ego_lane not in lanes[i]:
        #         continue
        #     else:
        #         road_index = i
        #         for j in range(len(lanes[i])):
        #             if lanes[i][j] == ego_lane:
        #                 lane_index = j
        #                 break
        #         break
        if behavior in ["park", "stop", "wait"]:
            if position in ["left"]:
                candidate_lanes_1.append(random.randint(-120, -100))
                # for j in range(lanes[1]):
                #     candidate_lanes_1.append(lanes[1][j])
                if lane_index == len(lanes[road_index])/2-1:
                    candidate_lanes_2.append(lanes[road_index][int(len(lanes[road_index])/2)-1])
                else:
                    for j in range(lane_index+1, int(len(lanes[road_index])/2)):
                        candidate_lanes_2.append(lanes[road_index][j])
            elif position in ["right"]:
                candidate_lanes_1.append(random.randint(-10, -2))
                # for j in range(len(lanes[-1])):
                #     candidate_lanes_1.append(lanes[-1][j])
                if lane_index == 0:
                    candidate_lanes_2.append(lanes[road_index][0])
                else:
                    for j in range(0, lane_index):
                        candidate_lanes_2.append(lanes[road_index][j])
            elif position in ["opposite"]:
                for j in range(len(lanes[road_index])):
                    candidate_lanes_1.append(lanes[2][j])
                    candidate_lanes_2.append(lanes[2][j])
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
            candidate_dest_1, candidate_dest_2 = -1, -1
        elif behavior in ["cross", "across", "pass"] or direction in ["opposite"]:
            if position in ["left"]:
                for i in range(int(len(lanes[1])/2)):
                    candidate_lanes_1.append(lanes[1][i])
                for j in range(int(len(lanes[-1])/2)):
                    candidate_dest_1.append(lanes[-1][j])
                index_array = []
                if lane_index == len(lanes[road_index])/2-1:
                    index_array.append(int(len(lanes[road_index])/2)-1)
                else:
                    for j in range(lane_index+1, int(len(lanes[road_index])/2)):
                        index_array.append(j)
                candidate_index = random.choice(index_array)
                initial_lane_2 = lanes[road_index][candidate_index]
                index_array.append(lane_index)
                candidate_index = random.choice(index_array)
                dest_lane_2 = lanes[2][candidate_index]
            elif position in ["right"]:
                for i in range(int(len(lanes[-1])/2), len(lanes[-1])):
                    candidate_lanes_1.append(lanes[-1][i])
                for j in range(int(len(lanes[1])/2), len(lanes[1])):
                    candidate_dest_1.append(lanes[1][j])
                index_array = []
                if lane_index == 0:
                    index_array.append(0)
                else:
                    for j in range(lane_index):
                        index_array.append(j)
                candidate_index = random.choice(index_array)
                initial_lane_2 = lanes[road_index][candidate_index]
                index_array.append(lane_index)
                dest_lane_2 = lanes[2][random.choice(index_array)]
            elif position in ["opposite"]:
                for i in range(int(len(lanes[2])/2), len(lanes[2])):
                    candidate_lanes_1.append(lanes[2][i])
                    candidate_lanes_2.append(lanes[2][i])
                for j in range(int(len(lanes[0])/2), len(lanes[0])):
                    candidate_dest_1.append(lanes[0][j])
                    candidate_dest_2.append(lanes[0][j])
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
                for j in range(int(len(lanes[2])/2)):
                    candidate_dest_1.append(lanes[2][j])
                    candidate_dest_2.append(lanes[2][j])
                # dest_lane_1, dest_lane_2 = lanes[2][lane_index], lanes[2][lane_index]
        elif behavior in ["turn"]:
            if position in ["left"]:
                for i in range(int(len(lanes[1])/2)):
                    candidate_lanes_1.append(lanes[1][i])
                if lane_index == len(lanes[0])/2-1:
                    candidate_lanes_2.append(lanes[road_index][int(len(lanes[1])/2)-1])
                else:
                    for j in range(lane_index+1, int(len(lanes[1])/2)):
                        candidate_lanes_2.append(lanes[road_index][j])
                if direction in ["left"]:
                    for j in range(int(len(lanes[2])/2)):
                        candidate_dest_1.append(lanes[2][j])
                    for j in range(int(len(lanes[1])/2), len(lanes[1])):
                        candidate_dest_2.append(lanes[1][j])
                elif direction in ["right"]:
                    for j in range(int(len(lanes[0])/2), len(lanes[0])):
                        candidate_dest_1.append(lanes[0][j])
                    for j in range(int(len(lanes[3])/2)):
                        candidate_dest_2.append(lanes[3][j])
                else:
                    for j in range(int(len(lanes[0])/2), len(lanes[0])):
                        candidate_dest_1.append(lanes[0][j])
                    for j in range(int(len(lanes[2])/2)):
                        candidate_dest_1.append(lanes[2][j])
                    for j in range(int(len(lanes[1])/2), len(lanes[1])):
                        candidate_dest_2.append(lanes[1][j])
                    for j in range(int(len(lanes[3])/2)):
                        candidate_dest_2.append(lanes[3][j])
            elif position in ["right"]:
                for i in range(int(len(lanes[-1])/2), len(lanes[-1])):
                    candidate_lanes_1.append(lanes[3][i])
                if lane_index == 0:
                    candidate_lanes_2.append(lanes[road_index][0])
                else:
                    for j in range(lane_index):
                        candidate_lanes_2.append(lanes[road_index][j])
                if direction in ["left"]:
                    for j in range(int(len(lanes[0])/2), len(lanes[0])):
                        candidate_dest_1.append(lanes[0][j])
                    for j in range(int(len(lanes[1])/2), len(lanes[1])):
                        candidate_dest_2.append(lanes[1][j])
                elif direction in ["right"]:
                    for j in range(int(len(lanes[2])/2)):
                        candidate_dest_1.append(lanes[2][j])
                    for j in range(int(len(lanes[3])/2)):
                        candidate_dest_2.append(lanes[3][j])
                else:
                    for j in range(int(len(lanes[0])/2), len(lanes[0])):
                        candidate_dest_1.append(lanes[0][j])
                    for j in range(int(len(lanes[2])/2)):
                        candidate_dest_1.append(lanes[2][j])
                    for j in range(int(len(lanes[1])/2), len(lanes[1])):
                        candidate_dest_2.append(lanes[1][j])
                    for j in range(int(len(lanes[3])/2)):
                        candidate_dest_2.append(lanes[3][j])
            elif position in ["opposite"]:
                for i in range(int(len(lanes[2])/2), len(lanes[2])):
                    candidate_lanes_1.append(lanes[2][i])
                    candidate_lanes_2.append(lanes[2][i])
                if direction in ["left"]:
                    for j in range(int(len(lanes[3])/2)):
                        candidate_dest_1.append(lanes[3][j])
                        candidate_dest_2.append(lanes[3][j])
                elif direction in ["right"]:
                    for j in range(int(len(lanes[1])/2), len(lanes[1])):
                        candidate_dest_1.append(lanes[1][j])
                        candidate_dest_2.append(lanes[1][j])
                else:
                    for j in range(int(len(lanes[1])/2), len(lanes[1])):
                        candidate_dest_1.append(lanes[1][j])
                        candidate_dest_2.append(lanes[1][j])
                    for j in range(int(len(lanes[3])/2)):
                        candidate_dest_1.append(lanes[3][j])
                        candidate_dest_2.append(lanes[1][j])
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
                if direction in ["left"]:
                    for j in range(int(len(lanes[1])/2), len(lanes[1])):
                        candidate_dest_1.append(lanes[1][j])
                        candidate_dest_2.append(lanes[1][j])
                elif direction in ["right"]:
                    for j in range(int(len(lanes[3])/2)):
                        candidate_dest_1.append(lanes[3][j])
                        candidate_dest_2.append(lanes[3][j])
                elif direction in ["opposite"]:
                    for j in range(int(len(lanes[2])/2)):
                        candidate_dest_1.append(lanes[2][j])
                        candidate_dest_2.append(lanes[2][j])
                else:
                    for j in range(int(len(lanes[1])/2), len(lanes[1])):
                        candidate_dest_1.append(lanes[1][j])
                        candidate_dest_2.append(lanes[1][j])
                    for j in range(int(len(lanes[3])/2)):
                        candidate_dest_1.append(lanes[3][j])
                        candidate_dest_2.append(lanes[3][j])
        else:
            if position in ["left"]:
                if lane_index == len(lanes[0])/2-1:
                    candidate_lanes_1.append(lanes[road_index][int(len(lanes[0])/2)-1])
                    candidate_lanes_2.append(lanes[road_index][int(len(lanes[0])/2)-1])
                else:
                    for j in range(lane_index+1, int(len(lanes[0])/2)):
                        candidate_lanes_1.append(lanes[road_index][j])
                        candidate_lanes_2.append(lanes[road_index][j])
                if direction in ["right"]:
                    if lane_index == 0:
                        candidate_dest_1.append(lanes[road_index][0])
                        candidate_dest_2.append(lanes[road_index][0])
                    else:
                        for j in range(lane_index):
                            candidate_dest_1.append(lanes[road_index][j])
                            candidate_dest_2.append(lanes[road_index][j])
                elif "change" in behavior:
                    dest_lane_1, dest_lane_2 = ego_lane, ego_lane
                else:
                    candidate_dest_1, candidate_dest_2 = -1, -1
            elif position in ["right"]:
                if lane_index == 0:
                    candidate_lanes_1.append(lanes[road_index][0])
                    candidate_lanes_2.append(lanes[road_index][0])
                else:
                    for j in range(lane_index):
                        candidate_lanes_1.append(lanes[road_index][j])
                        candidate_lanes_2.append(lanes[road_index][j])
                if direction in ["left"]:
                    if lane_index == len(lanes[0])/2-1:
                        candidate_dest_1.append(lanes[road_index][int(len(lanes[0])/2)-1])
                        candidate_dest_2.append(lanes[road_index][int(len(lanes[0])/2)-1])
                    else:
                        for j in range(lane_index+1, int(len(lanes[0])/2)):
                            candidate_dest_1.append(lanes[road_index][j])
                            candidate_dest_2.append(lanes[road_index][j])
                elif "change" in behavior:
                    dest_lane_1, dest_lane_2 = ego_lane, ego_lane
                else:
                    candidate_dest_1, candidate_dest_2 = -1, -1
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
                if direction in ["left"]:
                    if lane_index == len(lanes[0])/2-1:
                        candidate_dest_1.append(lanes[road_index][int(len(lanes[0])/2)-1])
                        candidate_dest_2.append(lanes[road_index][int(len(lanes[0])/2)-1])
                    else:
                        for j in range(lane_index+1, int(len(lanes[0])/2)-1):
                            candidate_dest_1.append(lanes[road_index][j])
                            candidate_dest_2.append(lanes[road_index][j])
                elif direction in ["right"]:
                    if lane_index == 0:
                        candidate_dest_1.append(lanes[road_index][0])
                        candidate_dest_2.append(lanes[road_index][0])
                    else:
                        for j in range(lane_index):
                            candidate_dest_1.append(lanes[road_index][j])
                            candidate_dest_2.append(lanes[road_index][j])
                elif "change" in behavior:
                    for j in range(lane_index):
                        candidate_dest_1.append(lanes[road_index][j])
                        candidate_dest_2.append(lanes[road_index][j])
                    for j in range(lane_index + 1, int(len(lanes[road_index])/2)):
                        candidate_dest_1.append(lanes[road_index][j])
                        candidate_dest_2.append(lanes[road_index][j])
                else:
                    candidate_dest_1, candidate_dest_2 = -1, -1

    else:
        index = lane_index
        ego_lane = lanes[lane_index]
        # for i in range(len(lanes)):
        #     if lanes[i] == ego_lane:
        #         index = i
        #         break
        if behavior in ["park", "stop", "wait"]:
            if position in ["left"]:
                if index == len(lanes)/2-1:
                    candidate_lanes_1.append(lanes[int(len(lanes)/2)-1])
                    candidate_lanes_2.append(lanes[int(len(lanes)/2)-1])
                else:
                    for j in range(index+1, int(len(lanes)/2)):
                        candidate_lanes_1.append(lanes[j])
                        candidate_lanes_2.append(lanes[j])
            elif position in ["right"]:
                if index == 0:
                    candidate_lanes_1.append(lanes[0])
                    candidate_lanes_2.append(lanes[0])
                else:
                    for j in range(index):
                        candidate_lanes_1.append(lanes[j])
                        candidate_lanes_2.append(lanes[j])
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
            candidate_dest_1, candidate_dest_2 = -1, -1
        else:
            if position in ["left"]:
                if index == len(lanes)/2-1:
                    candidate_lanes_1.append(lanes[int(len(lanes)/2)-1])
                    candidate_lanes_2.append(lanes[int(len(lanes)/2)-1])
                else:
                    for j in range(index+1, int(len(lanes)/2)):
                        candidate_lanes_1.append(lanes[j])
                        candidate_lanes_2.append(lanes[j])
                if direction in ["right"]:
                    if index == 0:
                        candidate_dest_1.append(lanes[0])
                        candidate_dest_2.append(lanes[0])
                    else:
                        for j in range(index):
                            candidate_dest_1.append(lanes[j])
                            candidate_dest_2.append(lanes[j])
                elif "change" in behavior:
                    dest_lane_1, dest_lane_2 = ego_lane, ego_lane
                else:
                    candidate_dest_1 = -1
            elif position in ["right"]:
                if index == 0:
                    candidate_lanes_1.append(lanes[0])
                    candidate_lanes_2.append(lanes[0])
                else:
                    for j in range(index):
                        candidate_lanes_1.append(lanes[j])
                        candidate_lanes_2.append(lanes[j])
                if direction in ["left"]:
                    if index == len(lanes)/2-1:
                        candidate_dest_1.append(lanes[int(len(lanes)/2)-1])
                        candidate_dest_2.append(lanes[int(len(lanes)/2)-1])
                    else:
                        for j in range(index+1, int(len(lanes)/2)):
                            candidate_dest_1.append(lanes[j])
                            candidate_dest_2.append(lanes[j])
                elif "change" in behavior:
                    dest_lane_1, dest_lane_2 = ego_lane, ego_lane
                else:
                    candidate_dest_1, candidate_dest_2 = -1, -1
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
                if direction in ["left"]:
                    if index == len(lanes)/2-1:
                        candidate_dest_1.append(lanes[int(len(lanes)/2)-1])
                        candidate_dest_2.append(lanes[int(len(lanes)/2)-1])
                    else:
                        for j in range(index+1, int(len(lanes)/2)):
                            candidate_dest_1.append(lanes[j])
                            candidate_dest_2.append(lanes[j])
                elif direction in ["right"]:
                    if index == 0:
                        candidate_dest_1.append(lanes[0])
                        candidate_dest_2.append(lanes[0])
                    else:
                        for j in range(index):
                            candidate_dest_1.append(lanes[j])
                            candidate_dest_2.append(lanes[j])
                elif "change" in behavior:
                    for j in range(index):
                        candidate_dest_1.append(lanes[j])
                        candidate_dest_2.append(lanes[j])
                    for j in range(index + 1, int(len(lanes)/2)):
                        candidate_dest_1.append(lanes[j])
                        candidate_dest_2.append(lanes[j])
                else:
                    candidate_dest_1, candidate_dest_2 = -1, -1

    if isinstance(initial_lane_1, int) and initial_lane_1 != -1:
        initial_lane_1 = initial_lane_1
    else:
        initial_lane_1 = random.choice(candidate_lanes_1)
    if candidate_dest_1 == -1:
        dest_lane_1 = initial_lane_1
    elif isinstance(dest_lane_1, int) and dest_lane_1 != -1:
        dest_lane_1 = dest_lane_1
    else:
        dest_lane_1 = random.choice(candidate_dest_1)

    if isinstance(initial_lane_2, int) and initial_lane_2 != -1:
        initial_lane_2 = initial_lane_2
    else:
        initial_lane_2 = random.choice(candidate_lanes_2)
    if candidate_dest_2 == -1:
        dest_lane_2 = initial_lane_2
    elif isinstance(dest_lane_2, int) and dest_lane_2 != -1:
        dest_lane_2 = dest_lane_2
    else:
        dest_lane_2 = random.choice(candidate_dest_2)

    return initial_lane_1, dest_lane_1, initial_lane_2, dest_lane_2


def get_ped_lane(road_type, lanes, lane_index, behavior, position, direction):
    initial_lane_1, dest_lane_1, initial_lane_2, dest_lane_2 = -1, -1, -1, -1
    candidate_lanes_1, candidate_dest_1, candidate_lanes_2, candidate_dest_2 = [], [], [], []
    waypoints_1, waypoints_2 = [], []
    if road_type in ["intersection", "t - junction", "t-junction", "junction", "crossing", "turnaround", "turning"]:
        road_index = 0
        ego_lane = lanes[0][lane_index]
        # for i in range(len(lanes)):
        #     if ego_lane not in lanes[i]:
        #         continue
        #     else:
        #         road_index = i
        #         for j in range(len(lanes[i])):
        #             if lanes[i][j] == ego_lane:
        #                 lane_index = j
        #                 break
        #         break
        if behavior in ["wait", "stop", "look", "stand"]:
            if position in ["left"]:
                selector = random.choice([0,1])
                if selector == 0:
                    initial_lane_1 = lanes[1][0]
                    waypoints_1.append(random.randint(parallel-10,parallel))
                    waypoints_1.append(waypoints_1[-1])
                else:
                    initial_lane_1 = lanes[1][-1]
                    waypoints_1.append(random.randint(0, 20))
                    waypoints_1.append(waypoints_1[-1])
                # candidate_lanes_1.append(random.randint(-120, -100))
                initial_lane_2 = lanes[road_index][-1]
                waypoints_2.append(random.randint(0,20))
                waypoints_2.append(waypoints_2[-1])
            elif position in ["right"]:
                selector = random.choice([0, 1])
                if selector == 0:
                    initial_lane_1 = lanes[-1][0]
                    waypoints_1.append(random.randint(0, 20))
                    waypoints_1.append(waypoints_1[-1])
                else:
                    initial_lane_1 = lanes[1][-1]
                    waypoints_1.append(random.randint(parallel-10,parallel))
                    waypoints_1.append(waypoints_1[-1])
                # candidate_lanes_1.append(random.randint(-10, -2))
                initial_lane_2 = lanes[road_index][0]
                waypoints_2.append(random.randint(int(vertical/2), vertical))
                waypoints_2.append(waypoints_2[-1])
            elif position in ["opposite"]:
                initial_lane_1 = lanes[2][0]
                waypoints_1.append(random.randint(0,10))
                waypoints_1.append(waypoints_1[-1])
                initial_lane_2 = lanes[2][-1]
                waypoints_2.append(random.randint(vertical-10,vertical))
                waypoints_2.append(waypoints_2[-1])
            else:
                initial_lane_1 = lanes[road_index][lane_index]
                initial_lane_2 = lanes[road_index][lane_index]
                waypoints_1.append(random.randint(int(vertical/2), vertical))
                waypoints_1.append(waypoints_1[-1])
                waypoints_2.append(random.randint(int(vertical/2), vertical))
                waypoints_2.append(waypoints_2[-1])
            candidate_dest_1, candidate_dest_2 = -1, -1
        elif behavior in ["cross", "across", "pass"] or direction in ["opposite"]:
            if position in ["left"]:
                selector = random.choice([0,1])
                if selector == 0:
                    initial_lane_1 = lanes[1][0]
                    waypoints_1.append(random.randint(parallel-10,parallel))
                else:
                    initial_lane_1 = lanes[1][-1]
                    waypoints_1.append(random.randint(0, 10))
                selector_2 = random.choice([0,1])
                if selector_2 == 0:
                    dest_lane_1 = lanes[-1][0]
                    waypoints_1.append(random.randint(0,10))
                else:
                    dest_lane_1 = lanes[-1][-1]
                    waypoints_1.append(random.randint(parallel-10, parallel))
                initial_lane_2 = lanes[road_index][-1]
                s = random.choice([0, -1])
                dest_lane_2 = lanes[2][s]
                if s == 0:
                    waypoints_2.append(random.randint(0,10))
                else:
                    waypoints_2.append(random.randint(vertical-10, vertical))
            elif position in ["right"]:
                selector = random.choice([0,1])
                if selector == 0:
                    initial_lane_1 = lanes[-1][0]
                    waypoints_1.append(random.randint(0, 10))
                else:
                    initial_lane_1 = lanes[-1][-1]
                    waypoints_1.append(random.randint(parallel-10, parallel))
                selector_2 = random.choice([0, 1])
                if selector_2 == 0:
                    dest_lane_1 = lanes[1][0]
                    waypoints_1.append(random.randint(parallel-10, parallel))
                else:
                    dest_lane_1 = lanes[1][-1]
                    waypoints_1.append(random.randint(0, 10))
                initial_lane_2 = lanes[road_index][0]
                s = random.choice([0, -1])
                dest_lane_2 = lanes[2][s]
                if s == 0:
                    waypoints_2.append(random.randint(0, 10))
                else:
                    waypoints_2.append(random.randint(vertical-10, vertical))
            elif position in ["opposite"]:
                initial_lane_1 = lanes[2][0]
                waypoints_1.append(random.randint(0,10))
                initial_lane_2 = lanes[2][-1]
                waypoints_1.append(random.randint(vertical-10, vertical))
                s = random.choice([0, -1])
                if s == 0:
                    dest_lane_1 = lanes[0][0]
                    waypoints_1.append(random.randint(vertical-10,vertical))
                    dest_lane_2 = lanes[0][-1]
                    waypoints_2.append(random.randint(0, 10))
                else:
                    dest_lane_1 = lanes[0][-1]
                    waypoints_2.append(random.randint(vertical-10, vertical))
                    dest_lane_2 = lanes[0][0]
                    waypoints_1.append(random.randint(0, 10))
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
                waypoints_1.append(random.randint(int(vertical/2), vertical))
                waypoints_2.append(random.randint(int(vertical/2), vertical))
                s = random.choice([0, -1])
                if s == 0:
                    dest_lane_1 = lanes[2][-1]
                    waypoints_1.append(random.randint(vertical-10, vertical))
                    dest_lane_2 = lanes[2][0]
                    waypoints_2.append(random.randint(0, 10))
                else:
                    dest_lane_1 = lanes[2][0]
                    waypoints_2.append(random.randint(vertical-10, vertical))
                    dest_lane_2 = lanes[2][-1]
                    waypoints_1.append(random.randint(0, 10))
        elif behavior in ["turn", "along"]:
            if position in ["left"]:
                selector = random.choice([0,1])
                if selector == 0:
                    initial_lane_1 = lanes[1][0]
                    waypoints_1.append(random.randint(vertical-10, vertical))
                else:
                    initial_lane_1 = lanes[1][-1]
                    waypoints_1.append(random.randint(0,10))
                initial_lane_2 = lanes[road_index][-1]
                waypoints_2.append(random.randint(0, 10))
                if direction in ["left"]:
                    s = random.choice([0, -1])
                    if s == 0:
                        dest_lane_1 = lanes[2][-1]
                        waypoints_1.append(random.randint(vertical-10, vertical))
                        dest_lane_2 = lanes[1][-1]
                        waypoints_2.append(random.randint(0, 10))
                    else:
                        dest_lane_1 = lanes[2][0]
                        waypoints_2.append(random.randint(parallel-10, parallel))
                        dest_lane_2 = lanes[1][0]
                        waypoints_1.append(random.randint(0, 10))
                else:
                    s = random.choice([0, -1])
                    if s == 0:
                        dest_lane_1 = lanes[0][0]
                        waypoints_1.append(random.randint(vertical-10, vertical))
                        dest_lane_2 = lanes[-1][0]
                        waypoints_2.append(random.randint(0, 10))
                    else:
                        dest_lane_1 = lanes[0][-1]
                        waypoints_2.append(random.randint(parallel-1, parallel))
                        dest_lane_2 = lanes[-1][-1]
                        waypoints_1.append(random.randint(0, 10))
            elif position in ["right"]:
                selector = random.choice([0, 1])
                if selector == 0:
                    initial_lane_1 = lanes[-1][-1]
                    waypoints_1.append(random.randint(vertical - 10, vertical))
                else:
                    initial_lane_1 = lanes[-1][0]
                    waypoints_1.append(random.randint(0, 10))
                initial_lane_2 = lanes[road_index][0]
                waypoints_2.append(random.randint(int((vertical + 1) / 2), vertical))
                if direction in ["left"]:
                    s = random.choice([0, -1])
                    if s == 0:
                        dest_lane_1 = lanes[0][0]
                        waypoints_1.append(random.randint(vertical - 10, vertical))
                        dest_lane_2 = lanes[1][-1]
                        waypoints_2.append(random.randint(0, 10))
                    else:
                        dest_lane_1 = lanes[0][-1]
                        waypoints_2.append(random.randint(parallel - 1, parallel))
                        dest_lane_2 = lanes[1][0]
                        waypoints_1.append(random.randint(0, 10))
                else:
                    s = random.choice([0, -1])
                    if s == 0:
                        dest_lane_1 = lanes[2][-1]
                        waypoints_1.append(random.randint(vertical - 10, vertical))
                        dest_lane_2 = lanes[-1][0]
                        waypoints_2.append(random.randint(0, 10))
                    else:
                        dest_lane_1 = lanes[2][0]
                        waypoints_2.append(random.randint(parallel - 10, parallel))
                        dest_lane_2 = lanes[-1][-1]
                        waypoints_1.append(random.randint(0, 10))
            elif position in ["opposite"]:
                initial_lane_1 = lanes[2][0]
                waypoints_1.append(random.randint[0,10])
                initial_lane_2 = lanes[2][-1]
                waypoints_2.append(random.randint[vertical-10, vertical])
                direct = random.choice([0,1])
                if direct == 0:
                    s = random.choice([0, -1])
                    if s == 0:
                        dest_lane_1 = lanes[1][0]
                        waypoints_1.append(random.randint(vertical - 10, vertical))
                        dest_lane_2 = lanes[-1][0]
                        waypoints_2.append(random.randint(0, 10))
                    else:
                        dest_lane_1 = lanes[1][-1]
                        waypoints_2.append(random.randint(parallel - 10, parallel))
                        dest_lane_2 = lanes[-1][-1]
                        waypoints_1.append(random.randint(0, 10))
                else:
                    s = random.choice([0, -1])
                    if s == 0:
                        dest_lane_2 = lanes[1][0]
                        waypoints_2.append(random.randint(vertical - 10, vertical))
                        dest_lane_1 = lanes[-1][0]
                        waypoints_1.append(random.randint(0, 10))
                    else:
                        dest_lane_2 = lanes[1][-1]
                        waypoints_1.append(random.randint(parallel - 10, parallel))
                        dest_lane_1 = lanes[-1][-1]
                        waypoints_2.append(random.randint(0, 10))
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
                waypoints_1.append(random.randint(int(vertical/2), vertical))
                waypoints_2.append(random.randint(int(vertical/2), vertical))
                if direction in ["left"]:
                    s = random.choice([0, -1])
                    if s == 0:
                        dest_lane_1 = lanes[1][0]
                        waypoints_1.append(random.randint(vertical - 10, vertical))
                        dest_lane_2 = lanes[1][-1]
                        waypoints_2.append(random.randint(0, 10))
                    else:
                        dest_lane_1 = lanes[1][-1]
                        waypoints_2.append(random.randint(parallel - 10, parallel))
                        dest_lane_2 = lanes[1][0]
                        waypoints_1.append(random.randint(0, 10))
                else:
                    s = random.choice([0, -1])
                    if s == 0:
                        dest_lane_1 = lanes[-1][-1]
                        waypoints_1.append(random.randint(vertical - 10, vertical))
                        dest_lane_2 = lanes[-1][0]
                        waypoints_2.append(random.randint(0, 10))
                    else:
                        dest_lane_1 = lanes[-1][0]
                        waypoints_2.append(random.randint(parallel - 10, parallel))
                        dest_lane_2 = lanes[-1][-1]
                        waypoints_1.append(random.randint(0, 10))
        else:
            if position in ["left"]:
                initial_lane_1, initial_lane_2 = lanes[road_index][-1], lanes[road_index][-1]
                waypoints_1.append(random.randint(10, int(vertical/2)))
                waypoints_2.append(random.randint(10, int(vertical/2)))
                if direction in ["right"]:
                    dest_lane_1, dest_lane_2 = lanes[road_index][0], lanes[road_index][0]
                    waypoints_1.append(random.randint(int(vertical / 2), vertical))
                    waypoints_2.append(random.randint(int(vertical / 2), vertical))
                else:
                    candidate_dest_1, candidate_dest_2 = -1, -1
                    waypoints_1.append(0)
                    waypoints_2.append(0)
            elif position in ["right"]:
                initial_lane_1, initial_lane_2 = lanes[road_index][0], lanes[road_index][0]
                waypoints_1.append(random.randint(int(vertical / 2), vertical))
                waypoints_2.append(random.randint(int(vertical / 2), vertical))
                if direction in ["left"]:
                    dest_lane_1, dest_lane_2 = lanes[road_index][-1], lanes[road_index][-1]
                    waypoints_1.append(random.randint(0, int(vertical / 2)))
                    waypoints_2.append(random.randint(0, int(vertical / 2)))
                else:
                    candidate_dest_1, candidate_dest_2 = -1, -1
                    waypoints_1.append(vertical)
                    waypoints_2.append(vertical)
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
                waypoints_1.append(random.randint(int(vertical/2), vertical))
                waypoints_2.append(random.randint(int(vertical/2), vertical))
                if direction in ["left"]:
                    dest_lane_1, dest_lane_2 = lanes[road_index][-1], lanes[road_index][-1]
                    waypoints_1.append(random.randint(0, int(vertical/2)))
                    waypoints_2.append(random.randint(0, int(vertical/2)))
                else:
                    dest_lane_1, dest_lane_2 = lanes[road_index][0], lanes[road_index][0]
                    waypoints_1.append(random.randint(int(vertical / 2), vertical))
                    waypoints_2.append(random.randint(int(vertical / 2), vertical))
                # else:
                #     dest_lane_1, dest_lane_2 = lanes[road_index][random.choice([0,-1])], lanes[road_index][random.choice([0,-1])]
    else:
        index = lane_index
        ego_lane = lanes[lane_index]
        # for i in range(len(lanes)):
        #     if lanes[i] == ego_lane:
        #         index = i
        #         break
        if behavior in ["wait", "stop", "look", "stand"]:
            if position in ["left"]:
                initial_lane_1, initial_lane_2 = lanes[-1], lanes[-1]
                waypoints_1.append(random.randint(0,10))
                waypoints_2.append(random.randint(0, 10))
            elif position in ["right"]:
                initial_lane_1, initial_lane_2 = lanes[0], lanes[0]
                waypoints_1.append(random.randint(int(vertical/2), vertical))
                waypoints_2.append(random.randint(int(vertical/2), vertical))
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
                waypoints_1.append(random.randint(int(vertical / 2), vertical))
                waypoints_2.append(random.randint(int(vertical / 2), vertical))
            waypoints_1.append(waypoints_1[-1])
            waypoints_2.append(waypoints_2[-1])
            candidate_dest_1, candidate_dest_2 = -1, -1
        if behavior in ["cross", "across", "pass"] or direction in ["opposite"]:
            if position in ["left"]:
                initial_lane_1, initial_lane_2 = lanes[-1], lanes[-1]
                waypoints_1.append(random.randint(0, int(vertical/2)))
                waypoints_2.append(random.randint(0, int(vertical/2)))
                dest_lane_1, dest_lane_2 = lanes[0], lanes[0]
                waypoints_1.append(random.randint(int(vertical/2), vertical))
                waypoints_2.append(random.randint(0, int(vertical/2)))
            elif position in ["right"]:
                initial_lane_1, initial_lane_2 = lanes[0], lanes[0]
                waypoints_1.append(random.randint(int(vertical / 2), vertical))
                waypoints_2.append(random.randint(int(vertical / 2), vertical))
                dest_lane_1, dest_lane_2 = lanes[-1], lanes[-1]
                waypoints_1.append(random.randint(0, int(vertical/2)))
                waypoints_2.append(random.randint(0, int(vertical/2)))
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
                waypoints_1.append(random.randint(int(vertical / 2), vertical))
                waypoints_2.append(random.randint(int(vertical / 2), vertical))
                dest_lane_1, dest_lane_2 = lanes[0], lanes[-1]
                waypoints_2.append(random.randint(0, int(vertical / 2)))
                waypoints_1.append(random.randint(int(vertical / 2), vertical))
        else:
            if position in ["left"]:
                initial_lane_1, initial_lane_2 = lanes[-1], lanes[-1]
                waypoints_1.append(random.randint(10, int(vertical/2)))
                waypoints_2.append(random.randint(10, int(vertical/2)))
                if direction in ["right"]:
                    dest_lane_1, dest_lane_2 = lanes[0], lanes[0]
                    waypoints_1.append(random.randint(int(vertical / 2), vertical))
                    waypoints_2.append(random.randint(int(vertical / 2), vertical))
                else:
                    candidate_dest_1, candidate_dest_2 = -1, -1
                    waypoints_1.append(random.randint(0, 5))
                    waypoints_2.append(random.randint(0, 5))
            elif position in ["right"]:
                initial_lane_1, initial_lane_2 = lanes[0], lanes[0]
                waypoints_1.append(random.randint(int(vertical / 2), vertical-10))
                waypoints_2.append(random.randint(int(vertical / 2), vertical-10))
                if direction in ["left"]:
                    dest_lane_1, dest_lane_2 = lanes[-1], lanes[-1]
                    waypoints_1.append(random.randint(0, int(vertical / 2)))
                    waypoints_2.append(random.randint(0, int(vertical / 2)))
                else:
                    candidate_dest_1, candidate_dest_2 = -1, -1
                    waypoints_1.append(random.randint(vertical-5, vertical))
                    waypoints_2.append(random.randint(vertical-5, vertical))
            else:
                initial_lane_1, initial_lane_2 = ego_lane, ego_lane
                waypoints_1.append(random.randint(int(vertical / 2), vertical-10))
                waypoints_2.append(random.randint(int(vertical / 2), vertical-10))
                if direction in ["left"]:
                    dest_lane_1, dest_lane_2 = lanes[-1], lanes[-1]
                    dest_lane_1, dest_lane_2 = lanes[-1], lanes[-1]
                    waypoints_1.append(random.randint(0, int(vertical / 2)))
                    waypoints_2.append(random.randint(0, int(vertical / 2)))
                else:
                    dest_lane_1, dest_lane_2 = lanes[0], lanes[0]
                    waypoints_1.append(random.randint(vertical - 5, vertical))
                    waypoints_2.append(random.randint(vertical - 5, vertical))

    if isinstance(initial_lane_1, int) and initial_lane_1 != -1:
        initial_lane_1 = initial_lane_1
    else:
        initial_lane_1 = random.choice(candidate_lanes_1)
    if candidate_dest_1 == -1:
        dest_lane_1 = initial_lane_1
    elif isinstance(dest_lane_1, int) and dest_lane_1 != -1:
        dest_lane_1 = dest_lane_1
    else:
        dest_lane_1 = random.choice(candidate_dest_1)

    if isinstance(initial_lane_2, int) and initial_lane_2 != -1:
        initial_lane_2 = initial_lane_2
    else:
        initial_lane_2 = random.choice(candidate_lanes_2)
    if candidate_dest_2 == -1:
        dest_lane_2 = initial_lane_2
    elif isinstance(dest_lane_2, int) and dest_lane_2 != -1:
        dest_lane_2 = dest_lane_2
    else:
        dest_lane_2 = random.choice(candidate_dest_2)

    return initial_lane_1, dest_lane_1, initial_lane_2, dest_lane_2, waypoints_1, waypoints_2


def get_vehicle_next_lane(lanes, pre_lanes, road_type, behavior, direction):
    initial_lane_1 = pre_lanes[-1]
    dest_lane_1 = -1
    candidate_dest_1 = []
    if road_type in ["intersection", "t - junction", "t-junction", "junction", "crossing", "turnaround", "turning"]:
        road_index, lane_index = None, None
        for i in range(len(lanes)):
            if initial_lane_1 not in lanes[i]:
                continue
            else:
                road_index = i
                for j in range(len(lanes[i])):
                    if lanes[i][j] == initial_lane_1:
                        lane_index = j
                        break
                break
        if behavior in ["park", "stop", "wait"]:
            dest_lane_1 = initial_lane_1
        elif behavior in ["cross", "across", "pass"] or direction in ["opposite"]:
            if road_index == 0:
                dest_lane_1 = lanes[2][lane_index]
            elif road_index == 1:
                dest_lane_1 = lanes[3][lane_index]
            elif road_index == 2:
                dest_lane_1 = lanes[0][lane_index]
            elif road_index == 3:
                dest_lane_1 = lanes[1][lane_index]
        elif behavior in ["turn"]:
            if road_index == 0:
                if direction in ["left"]:
                    for j in range(int(len(lanes[1])/2), len(lanes[1])):
                        candidate_dest_1.append(lanes[1][j])
                else:
                    for j in range(int(len(lanes[-1])/2)):
                        candidate_dest_1.append(lanes[-1][j])
            elif road_index == 1:
                if direction in ["left"]:
                    for j in range(int(len(lanes[2])/2)):
                        candidate_dest_1.append(lanes[2][j])
                else:
                    for j in range(int(len(lanes[0])/2), len(lanes[0])):
                        candidate_dest_1.append(lanes[0][j])
            elif road_index == 2:
                if direction in ["left"]:
                    for j in range(int(len(lanes[-1])/2)):
                        candidate_dest_1.append(lanes[-1][j])
                else:
                    for j in range(int(len(lanes[1])/2), len(lanes[1])):
                        candidate_dest_1.append(lanes[1][j])
            elif road_index == 3:
                if direction in ["left"]:
                    for j in range(int(len(lanes[0])/2), len(lanes[0])):
                        candidate_dest_1.append(lanes[0][j])
                else:
                    for j in range(int(len(lanes[2])/2)):
                        candidate_dest_1.append(lanes[2][j])
        else:
            if direction in ["left"]:
                if lane_index == len(lanes[road_index])/2-1:
                    dest_lane_1 = lanes[road_index][int(len(lanes[road_index])/2)-1]
                else:
                    for j in range(lane_index+1, int(len(lanes[road_index])/2)):
                        candidate_dest_1.append(lanes[road_index][j])
            elif direction in ["right"]:
                if lane_index == len(lanes[road_index]) / 2 - 1:
                    dest_lane_1 = lanes[road_index][0]
                else:
                    for j in range(lane_index):
                        candidate_dest_1.append(lanes[road_index][j])
            elif "change" in behavior:
                for j in range(lane_index):
                    candidate_dest_1.append(lanes[road_index][j])
                for j in range(lane_index+1, int(len(lanes[road_index])/2)):
                    candidate_dest_1.append(lanes[road_index][j])
            else:
                dest_lane_1 = initial_lane_1

    else:
        index = None
        for i in range(len(lanes)):
            if lanes[i] == initial_lane_1:
                index = i
                break
        if behavior in ["park", "stop", "wait"]:
            dest_lane_1 = initial_lane_1
        else:
            if direction in ["left"]:
                if index == len(lanes)/2-1:
                    dest_lane_1 = lanes[int(len(lanes)/2)-1]
                else:
                    for j in range(index+1, int(len(lanes)/2)):
                        candidate_dest_1.append(lanes[j])
            elif direction in ["right"]:
                if index == 0:
                    dest_lane_1 = lanes[0]
                else:
                    for j in range(index):
                        candidate_dest_1.append(lanes[j])
            elif "change" in behavior:
                for j in range(index):
                    candidate_dest_1.append(lanes[j])
                for j in range(index+1, int(len(lanes)/2)):
                    candidate_dest_1.append(lanes[j])
            else:
                dest_lane_1 = initial_lane_1

    if candidate_dest_1 == -1:
        dest_lane_1 = initial_lane_1
    elif isinstance(dest_lane_1, int) and dest_lane_1 != -1:
        dest_lane_1 = dest_lane_1
    else:
        dest_lane_1 = random.choice(candidate_dest_1)

    return dest_lane_1


def get_ped_lane_next(road_type, pre_lanes, lanes, behavior, direction):
    initial_lane_1 = pre_lanes[-1]
    dest_lane_1 = -1
    candidate_dest_1 = []
    waypoint = -1
    if road_type in ["intersection", "t - junction", "t-junction", "junction", "crossing", "turnaround", "turning"]:
        road_index, lane_index = None, None
        for i in range(len(lanes)):
            if initial_lane_1 not in lanes[i]:
                continue
            else:
                road_index = i
                for j in range(len(lanes[i])):
                    if lanes[i][j] == initial_lane_1:
                        lane_index = j
                        break
                break
        if behavior in ["wait", "stop", "look", "stand"]:
            dest_lane_1 = initial_lane_1
        elif behavior in ["cross", "across", "pass"] or direction in ["opposite"]:
            if road_index == 0:
                selector = random.choice([0,1])
                if selector == 0:
                    dest_lane_1 = lanes[2][0]
                    waypoint = random.randint(0,10)
                else:
                    dest_lane_1 = lanes[2][-1]
                    waypoint = random.randint(vertical-10, vertical)
            elif road_index == 1:
                selector = random.choice([0, 1])
                if selector == 0:
                    dest_lane_1 = lanes[3][0]
                    waypoint = random.randint(0, 10)
                else:
                    dest_lane_1 = lanes[3][-1]
                    waypoint = random.randint(parallel - 10, parallel)
            elif road_index == 2:
                selector = random.choice([0, 1])
                if selector == 0:
                    dest_lane_1 = lanes[0][-1]
                    waypoint = random.randint(0, 10)
                else:
                    dest_lane_1 = lanes[0][0]
                    waypoint = random.randint(vertical - 10, vertical)
            elif road_index == 3:
                selector = random.choice([0, 1])
                if selector == 0:
                    dest_lane_1 = lanes[1][-1]
                    waypoint = random.randint(0, 10)
                else:
                    dest_lane_1 = lanes[1][0]
                    waypoint = random.randint(parallel - 10, parallel)
        elif behavior in ["turn", "along"]:
            if road_index == 0:
                if direction in ["left"]:
                    selector = random.choice([0, 1])
                    if selector == 0:
                        dest_lane_1 = lanes[1][-1]
                        waypoint = random.randint(0, 10)
                    else:
                        dest_lane_1 = lanes[1][0]
                        waypoint = random.randint(parallel - 10, parallel)
                else:
                    selector = random.choice([0, 1])
                    if selector == 0:
                        dest_lane_1 = lanes[3][0]
                        waypoint = random.randint(0, 10)
                    else:
                        dest_lane_1 = lanes[3][-1]
                        waypoint = random.randint(parallel - 10, parallel)
            elif road_index == 1:
                if direction in ["left"]:
                    selector = random.choice([0, 1])
                    if selector == 0:
                        dest_lane_1 = lanes[2][0]
                        waypoint = random.randint(0, 10)
                    else:
                        dest_lane_1 = lanes[2][-1]
                        waypoint = random.randint(vertical - 10, vertical)
                else:
                    selector = random.choice([0, 1])
                    if selector == 0:
                        dest_lane_1 = lanes[0][-1]
                        waypoint = random.randint(0, 10)
                    else:
                        dest_lane_1 = lanes[0][0]
                        waypoint = random.randint(vertical - 10, vertical)
            elif road_index == 2:
                direct = random.choice([0,1])
                if direct == 0:
                    selector = random.choice([0,1])
                    if selector == 0:
                        dest_lane_1 = lanes[1][-1]
                        waypoint = random.randint(0, 10)
                    else:
                        dest_lane_1 = lanes[1][0]
                        waypoint = random.randint(parallel - 10, parallel)
                else:
                    selector = random.choice([0, 1])
                    if selector == 0:
                        dest_lane_1 = lanes[-1][0]
                        waypoint = random.randint(0, 10)
                    else:
                        dest_lane_1 = lanes[-1][-1]
                        waypoint = random.randint(parallel - 10, parallel)
            elif road_index == 3:
                if direction in ["left"]:
                    selector = random.choice([0, 1])
                    if selector == 0:
                        dest_lane_1 = lanes[0][-1]
                        waypoint = random.randint(0, 10)
                    else:
                        dest_lane_1 = lanes[0][0]
                        waypoint = random.randint(vertical - 10, vertical)
                else:
                    selector = random.choice([0, 1])
                    if selector == 0:
                        dest_lane_1 = lanes[2][0]
                        waypoint = random.randint(0, 10)
                    else:
                        dest_lane_1 = lanes[2][-1]
                        waypoint = random.randint(vertical - 10, vertical)
        else:
            if road_index == 0:
                if direction in ["left"]:
                    dest_lane_1 = lanes[road_index][-1]
                    waypoint = random.randint(0,10)
                else:
                    dest_lane_1 = lanes[road_index][0]
                    waypoint = random.randint(vertical - 10, vertical)
            elif road_index == 1:
                if direction in ["left"]:
                    dest_lane_1 = lanes[road_index][-1]
                    waypoint = random.randint(0, 10)
                else:
                    dest_lane_1 = lanes[road_index][0]
                    waypoint = random.randint(parallel - 10, parallel)
            elif road_index == 2:
                if direction in ["left"]:
                    dest_lane_1 = lanes[road_index][0]
                    waypoint = random.randint(0, 10)
                else:
                    dest_lane_1 = lanes[road_index][-1]
                    waypoint = random.randint(vertical - 10, vertical)
            else:
                if direction in ["left"]:
                    dest_lane_1 = lanes[road_index][0]
                    waypoint = random.randint(0, 10)
                else:
                    dest_lane_1 = lanes[road_index][-1]
                    waypoint = random.randint(parallel - 10, parallel)
    else:
        index = None
        for i in range(len(lanes)):
            if lanes[i] == initial_lane_1:
                index = i
                break
        if behavior in ["wait", "stop", "look", "stand"]:
            dest_lane_1 = initial_lane_1
        else:
            if direction in ["left"]:
                dest_lane_1 = lanes[-1]
                waypoint = random.randint(0, 10)
            elif direction in ["right"]:
                dest_lane_1 = lanes[0]
                waypoint = random.randint(vertical - 10, vertical)
            else:
                dest_lane_1 = initial_lane_1
                waypoint = random.randint(vertical - 10, vertical)

    if candidate_dest_1 == -1:
        dest_lane_1 = initial_lane_1
    elif isinstance(dest_lane_1, int) and dest_lane_1 != -1:
        dest_lane_1 = dest_lane_1
    else:
        dest_lane_1 = random.choice(candidate_dest_1)

    return dest_lane_1, waypoint


def get_closet_lane(lane_index, length):
    if length-1-lane_index > lane_index:
        return 0
    else:
        return length-1


def get_npc_speed(behavior, num):
    speed = []
    if behavior in ["stop", "wait", "park"]:
        for i in range(num):
            speed.append(0)
    elif behavior in ["decelerate", "slow down"]:
        initial = random.randint(10, 15)
        speed.append(initial)
        for i in range(1, num):
            tmp = max((initial - random.randint(5, 8)*i), 2)
            speed.append(tmp)
    elif behavior in ["accelerate", "speed up"]:
        initial = random.randint(5, 8)
        speed.append(initial)
        for i in range(1, num):
            tmp = initial + random.randint(5, 8) * i
            speed.append(tmp)
    else:
        initial = random.randint(8, 12)
        for i in range(num):
            speed.append(initial)

    return speed


if __name__ == '__main__':
    ele_array = [['rainy', 'cloudy'], [{'vehicles': ['vehicle'], 'position': [['left']], 'behaviors': [['drive', 3]],
                                        'direction': [['right', 'roadside']]}],
                 [{'pedestrian': ['cyclist'], 'position': [['intersection'], ['left', 'lane']],
                   'behaviors': [['cross', 7], ['move', 13, 'slowly']], 'direction': []}], ['intersection'],
                 ['traffic light']]
    ele_array = [['rainy', 'cloudy'], [{'vehicles': ['vehicle'], 'position': [['left']], 'behaviors': [['park', 3]], 'direction': []}, {'vehicles': ['vehicle'], 'position': [['left']], 'behaviors': [['drive', 3]], 'direction': [['right', 'roadside']]},
                                       {'vehicles': ['vehicle'], 'position': [], 'behaviors': [['stop', 5, 'slowly'], ['move', 7], ['wait', 11], ['pass', 16]], 'direction': []}],
                [{'pedestrian': ['cyclist'], 'position': [['intersection'], ['left', 'lane']], 'behaviors': [['cross', 7], ['move', 13, 'slowly']], 'direction': []},
                {'pedestrian': ['cyclist'], 'position': [], 'behaviors': [['move', 7], ['wait', 11], ['pass', 16]], 'direction': []}],
                ['intersection'], ['traffic light']]
    array = [['rain', 'rain'], [{'vehicles': ['sedan'], 'position': [], 'behaviors': [['across', 25]], 'direction': []}, {'vehicles': ['truck'], 'position': [], 'behaviors': [['across', 25]], 'direction': []}, {'vehicles': ['van'], 'position': [], 'behaviors': [['across', 25]], 'direction': []}, {'vehicles': ['vehicle'], 'position': [], 'behaviors': [['park', 10]], 'direction': [['along']]}], [], ['residential', 'sidewalk'], []]
    pics_to_scenario_program(ele_array)