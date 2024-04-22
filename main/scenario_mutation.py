import json
import os
import random
import re

import numpy as np
from openai import OpenAI

from main.scenario_tree import create_scenario

api_key = ""


def request_gpt(system_prompt, user_content):

    client = OpenAI(api_key=api_key)

    file_list = os.listdir("scenario_description")
    path = "scenario_description/scenario_folder" + str(len(file_list))
    os.makedirs(path)
    scenario_list = os.listdir(path)

    for i in range(4):
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            stream=True
        )

        scenario_path = path + "/scenario_"+str(len(scenario_list)+i)

        gpt_result = ""

        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                gpt_result = gpt_result + chunk.choices[0].delta.content
            # print(chunk.choices[0].delta.content, end="")

        result = gpt_result.split("'''")
        for each in result:
            if "CreateScenario" in each:
                content = each
        with open(scenario_path, 'w') as f:
            f.write(content)

    # return scenario_path
  # print(completion.choices[0].message.content)

# from openai import OpenAI
#
# # client = OpenAI(api_key="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")
# client = OpenAI(api_key="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")
#
# stream = client.chat.completions.create(
#     model="gpt-4",
#     messages=[{"role": "user", "content": "Say this is a video"}],
#     stream=True,
# )
# for chunk in stream:
#     if chunk.choices[0].delta.content is not None:
#         print(chunk.choices[0].delta.content, end="")


def split_scenario_content(scenario):
    scenario_string = scenario.split("'''")
    return scenario_string[1]

# def first_prompt(st_name="start_prompt.txt", test_name="test_prompt_collision_v.txt"):
#     with open("prompt_content/" + st_name, "r") as f:
#       start_prompt = f.read()
#   #   with open("scenario_description/scenario_example.txt", "r") as f:
#   #     example_scenario = f.read()
#     with open("prompt_content/test_prompt/" + test_name, "r") as f:
#       test_prompt = f.read()
#
#     content = [start_prompt, test_prompt]
#     # content = start_prompt + "\n" + "\n" + feedback_prompt + "\n" + "\n" + scenario_description
#
#     return content


def first_prompt(scenario, st_name, road):
    with open("prompt_content/" + st_name, "r") as f:
      start_prompt = f.read()
    with open("prompt_content/system_prompt.txt", "r") as f:
      system_prompt = f.read()
    lane_range = ','.join([str(x) for x in road])
    starts = start_prompt.split("\n\n")
    test_prompt = starts[0] + "\n" + scenario + "\n" + starts[-1] + lane_range

    prompt_folder = "prompt_content/test_prompt"
    prompt_files = os.listdir(prompt_folder)
    with open(prompt_folder+"/prompt"+str(len(prompt_files))+".txt", "w") as f:
        f.write(test_prompt)

    return system_prompt, test_prompt


def feedback(feedback_name, file_path):
    with open("prompt_content/feedback_prompt/" + feedback_name, "r") as f:
        feedback_prompt = f.read()
    # file_list = os.listdir("scenario_description")
    # path = "scenario_description/scenario_folder"+str(len(file_list))
    # scenario_list = os.listdir(path)
    with open(file_path, "r") as f:
        scenario_description = f.read()

    scenario_description = "'''"+scenario_description+"'''"
    content = [feedback_prompt, scenario_description]

    return content


def test_prompt(path):
    with open("prompt_content/system_prompt.txt", "r") as f:
        system_prompt = f.read()
    with open(path, "r") as f:
        prompt = f.read()
    with open("prompt_content/test_prompt/constraints.txt", "r") as f:
        constraints = f.read()
    content = prompt + "\n" + constraints
    request_gpt(system_prompt, content)


# def chat_seeds(contents, file_path, feedback_name="feedback_prompt_sv.txt", test_name="test_prompt_collision_v.txt", flag="success", re_generate=None):
#     with open("prompt_content/system_prompt.txt", "r") as f:
#         system_prompt = f.read()
#     with open("prompt_content/test_prompt/constraints.txt", "r") as f:
#         constraints = f.read()
#     # if len(contents) == 0:
#     #     file_list = os.listdir("scenario_description")
#     #     path = "scenario_description/scenario_folder" + str(len(file_list)+1)
#     #     folder = os.path.exists(path)
#     #     if not folder:
#     #         os.makedirs(path)
#     #     content = first_prompt(test_name=test_name)
#     #     request_content = content[0] + "\n" + content[1] + "\n" + constraints
#     #     results = request_gpt(system_prompt, request_content)
#     #     contents.append(content[0])
#         # contents.append(content[1])
#     # else:
#     if re_generate is None:
#         feedback_content = feedback(feedback_name, file_path)
#         if len(contents) > 1:
#             with open("prompt_content/feedback_prompt/feedback_prompt_" + flag + ".txt", "r") as f:
#                 feedback_prompt = f.read()
#             contents[-2] = feedback_prompt
#     else:
#         # file_list = os.listdir("scenario_description")
#         # path = "scenario_description/scenario_folder" + str(len(file_list))
#         # scenario_list = os.listdir(path)
#         with open(file_path, "r") as f:
#             scenario_description = f.read()
#         scenario_description = "'''"+scenario_description+"'''"
#         feedback_content = [re_generate, scenario_description]
#
#     for item in feedback_content:
#         contents.append(item)
#     request_content = ""
#     for each in contents:
#         request_content = request_content + each + "\n"
#     request_content = request_content + "\n" + constraints
#     results = request_gpt(system_prompt, request_content)
#
#     return contents, results


def feedback_generation():
    prompt_folder = "prompt_content/test_prompt"
    prompt_files = os.listdir(prompt_folder)
    with open(prompt_folder + "/prompt" + str(len(prompt_files)) + ".txt", "r") as f:
        prompt = f.read()

    scenario_folder = "safe_scenario_description"
    scenario_files = os.listdir(scenario_folder)
    scenario_num = len(scenario_files)
    violation_folder = "violation_scenario_description"
    violation_files = os.listdir(violation_folder)

    prompt = prompt + "\n"
    prompt = prompt + "The following scenarios cannot challenge ego vehicle, they are not what we want:" + "\n"

    with open(scenario_folder + "/scenario_" + str(scenario_num), "r") as f:
        scenario_1 = f.read()
        prompt = prompt + "\n"
        prompt = prompt + "```"
        prompt = prompt + scenario_1 + "\n" + "```"

    for i in range(max(0, scenario_num-3), scenario_num+1):
        with open(scenario_folder + "/scenario_" + str(i), "r") as f:
            this_scenario = f.read()
        prompt = prompt + "\n"
        prompt = prompt + "```"
        prompt = prompt + this_scenario + "\n" + "```"

    prompt = prompt + "\n"
    prompt = prompt + "The ego vehicle occurred safety violations in the following scenarios, they are what we want:" + "\n"

    for i in range(max(0, len(violation_files)-3), len(violation_files)+1):
        with open(violation_folder + "/violation_" + str(i), "r") as f:
            this_scenario = f.read()
        prompt = prompt + "\n"
        prompt = prompt + "```"
        prompt = prompt + this_scenario + "\n" + "```"

    with open("prompt_content/system_prompt.txt", "r") as f:
        system_prompt = f.read()

    request_gpt(system_prompt, prompt)


def random_swap(array1, array2):
    # 获取数组的长度
    len_array1 = len(array1)
    len_array2 = len(array2)

    # 随机选择要交换的元素的索引
    index1 = np.random.randint(0, len_array1)
    index2 = np.random.randint(0, len_array2)

    # 执行交换
    array1[index1], array2[index2] = array2[index2], array1[index1]

    return array1, array2


def find_first_char_after_word(input_string, pattern):
    match = re.search(pattern, input_string)
    if match:
        start_index = match.end()
        return input_string[start_index:][0]
    else:
        return None


def has_duplicates(arr):
    return len(arr) != len(set(arr))


def crossover_scenarios(scenario1, scenario2):
    blocks_1 = scenario1.split('\n\n')
    blocks_2 = scenario2.split('\n\n')
    for i in range(len(blocks_1)):
        if '...' in blocks_1[i]:
            tmp = blocks_1[i].split('...')
            del blocks_1[i]
            for tmp_each in tmp:
                blocks_1.append(tmp_each)
    for i in range(len(blocks_2)):
        if '...' in blocks_2[i]:
            tmp = blocks_2[i].split('...')
            del blocks_2[i]
            for tmp_each in tmp:
                blocks_2.append(tmp_each)
    npcs_1, npcs_2, peds_1, peds_2 = [], [], [], []
    for block in blocks_1:
        if 'npc' in block and '->' in block:
            npcs_1.append(block)
        elif 'ped' in block and '->' in block:
            peds_1.append(block)
    for block in blocks_2:
        if 'npc' in block and '->' in block:
            npcs_2.append(block)
        elif 'ped' in block and '->' in block:
            peds_2.append(block)
    if len(npcs_1) == 1 and len(npcs_2) == 1 and len(peds_1) == 1 and len(peds_2) == 1:
        tmp = npcs_1[0]
        npcs_1[0] = npcs_2[0]
        npcs_2[0] = tmp
    else:
        if len(npcs_1) >1 or len(npcs_2) > 1:
            crossed_npc_1 = random.randint(0, len(npcs_1)-1)
            crossed_npc_2 = random.randint(0, len(npcs_2)-1)
            tmp = npcs_1[crossed_npc_1]
            npcs_1[crossed_npc_1] = npcs_2[crossed_npc_2]
            npcs_2[crossed_npc_2] = tmp
        if len(peds_1) > 1 or len(peds_2) > 1:
            crossed_ped_1 = random.randint(0, len(peds_1)-1)
            crossed_ped_2 = random.randint(0, len(peds_2)-1)
            tmp = peds_1[crossed_ped_1]
            peds_1[crossed_ped_1] = peds_2[crossed_ped_2]
            peds_2[crossed_ped_2] = tmp

    result = []
    for i in range(len(npcs_1)):
        number = find_first_char_after_word(npcs_1[i], "npc")
        if number.isdigit():
            result.append(number)
    if has_duplicates(result):
        for i in range(len(npcs_1)):
            npcs_1[i] = npcs_1[i].replace("npc"+str(result[i]), "npc"+str(i+1))

    result = []
    for i in range(len(npcs_2)):
        number = find_first_char_after_word(npcs_2[i], "npc")
        if number.isdigit():
            result.append(number)
    if has_duplicates(result):
        for i in range(len(npcs_2)):
            npcs_2[i] = npcs_2[i].replace("npc"+result[i], "npc"+str(i+1))

    result = []
    for i in range(len(peds_1)):
        number = find_first_char_after_word(peds_1[i], "ped")
        if number.isdigit():
            result.append(number)
    if has_duplicates(result):
        for i in range(len(peds_1)):
            peds_1[i] = peds_1[i].replace("ped" + result[i], "ped" + str(i + 1))

    result = []
    for i in range(len(peds_2)):
        number = find_first_char_after_word(peds_2[i], "ped")
        if number.isdigit():
            result.append(number)
    if has_duplicates(result):
        for i in range(len(peds_2)):
            peds_2[i] = peds_2[i].replace("ped" + result[i], "ped" + str(i + 1))

    scenario_1 = blocks_1[0] + "\n\n"
    scenario_2 = blocks_2[0] + "\n\n"

    for each in npcs_1:
        scenario_1 = scenario_1 + each + "\n\n"
    for each in peds_1:
        scenario_1 = scenario_1 + each + "\n\n"
    for each in blocks_1:
        if "weather" in each and "CreateScenario" not in each:
            scenario_1 = scenario_1 + each + "\n\n"
        if "CreateScenario" in each:
            scenario_1 = scenario_1 + each + "\n\n"
    for each in npcs_2:
        scenario_2 = scenario_2 + each + "\n\n"
    for each in peds_2:
        scenario_2 = scenario_2 + each + "\n\n"
    for each in blocks_2:
        if "weather" in each and "CreateScenario" not in each:
            scenario_2 = scenario_2 + each + "\n\n"
        if "CreateScenario" in each:
            scenario_2 = scenario_2 + each + "\n\n"
    # for block in blocks_1:
    #     if "ego" in block and '->' in block and scenario_1 == "":
    #         scenario_1 = block
    #     if "npc" in block and '->' in block and scenario_1 != "":
    #         scenario_1 = scenario_1 + "\n\n" + block
    #     if "ped" in block and '->' in block and scenario_1 != "":
    #         scenario_1 = scenario_1 + "\n\n" + block
    #     if "time" in block and '->' in block and scenario_1 != "":
    #         scenario_1 = scenario_1 + "\n\n" + block
    #     if "CreateScenario" in block and '->' in block and scenario_1 != "":
    #         scenario_1 = scenario_1 + "\n\n" + block
    # for block in blocks_2:
    #     if "ego" in block and '->' in block and scenario_2 == "":
    #         scenario_2 = block
    #     if "npc" in block and '->' in block and scenario_2 != "":
    #         scenario_2 = scenario_2 + "\n\n" + block
    #     if "ped" in block and '->' in block and scenario_2 != "":
    #         scenario_2 = scenario_2 + "\n\n" + block
    #     if "time" in block and '->' in block and scenario_2 != "":
    #         scenario_2 = scenario_2 + "\n\n" + block
    #     if "CreateScenario" in block and '->' in block and scenario_2 != "":
    #         scenario_2 = scenario_2 + "\n\n" + block

    return scenario_1, scenario_2


def crossover_scenario(scenario):
    blocks = scenario.split('\n\n')
    ego = blocks[0]
    weather = blocks[-2]
    create = blocks[-1]
    # for i in range(len(blocks)):
    #     if '...' in blocks[i]:
    #         tmp = blocks[i].split('...')
    #         del blocks[i]
    #         for tmp_each in tmp:
    #             blocks.append(tmp_each)
    npc_ped = create_scenario({"npcs": [], "peds": []}, scenario)
    npcs = npc_ped['npcs']
    peds = npc_ped['peds']
    crossed = False
    if len(npcs) > 1:
        # crossover = random.choice[1, 2]
        crossed_npc = random.sample(range(0, len(npcs)), 2)
        npcs[crossed_npc[0]], npcs[crossed_npc[1]] = random_swap(npcs[crossed_npc[0]], npcs[crossed_npc[1]])
        crossed = True
        # npc_ped['npcs'] = npcs

    if len(peds) > 1:
        crossed_ped = random.sample(range(0, len(peds)), 2)
        peds[crossed_ped[0]], peds[crossed_ped[1]] = random_swap(npcs[crossed_ped[0]], npcs[crossed_ped[1]])
        crossed = True
        # npc_ped['peds'] = peds

    if crossed:
        return waypoints_scenario(ego, weather, create, npc_ped)
    else:
        return None


def waypoints_scenario(ego, weather, create, waypoints):
    npcs = waypoints['npcs']
    peds = waypoints['peds']
    scenario_phases = ego + "\n\n"
    for i in range(len(npcs)):
        scenario_phases = scenario_phases + "npc"+str(i+1)+"_type = \"Sedan\"; \n npc"+str(i+1)+ "_heading = 0 deg related to ego_vehicle; \n npc"+str(i+1)+"_init_position = "
        scenario_phases = scenario_phases + "(\"lane_" + str(npcs[i][0][0]) + "\"->" + str(npcs[i][0][1]) + "); \n npc" + str(
            i + 1) + "_init_state = (npc" + str(i+1) + "_init_position, npc" + str(i+1) + "_heading," + str(npcs[i][0][2]) + "); \n"
        scenario_phases = scenario_phases + "npc" + str(i + 1) + "_waypoints = Waypoint("
        for j in range(1, len(npcs[i])-1):
            scenario_phases = scenario_phases + "(\"lane_" + str(npcs[i][j][0])+"\"->"+str(npcs[i][j][1])+", ,"+str(npcs[i][j][2])+"),"
        scenario_phases = scenario_phases + "); \n"
        scenario_phases = scenario_phases + "npc"+str(i+1)+"_destination = ( \"lane_" + str(npcs[i][-1][0])+"\"->" + str(npcs[i][-1][1]) + "); \n"
        scenario_phases = scenario_phases + "npc"+str(i+1)+"_destination_state = (npc" + str(i+1) + "_destination); \n"
        scenario_phases = scenario_phases + "npc"+str(i+1)+"=Vehicle(npc"+str(i+1)+"_init_state, npc"+str(i+1) + "_waypoints, npc" +str(i+1)+"_destination, npc"+str(i+1)+"_type); \n"
        scenario_phases = scenario_phases + "\n"

    for i in range(len(peds)):
        scenario_phases = scenario_phases + "ped"+str(i+1)+"_position =" + "(\"lane_" + str(peds[i][0][0]) + "\"->" + str(peds[i][0][1]) + "); \n"
        scenario_phases = scenario_phases + "ped" + str(i + 1) + "_init_state = (ped" +str(i+1) + "_position, , " + str(random.randint(1,3)) + "); \n"
        scenario_phases = scenario_phases + "ped" + str(i + 1) + "_waypoints = Waypoint("
        for j in range(1, len(peds[i])-1):
            scenario_phases = scenario_phases + "(\"lane_" + str(peds[i][j][0])+"\"->"+str(peds[i][j][1])+", ,"+str(random.randint(1, 3))+"),"
        scenario_phases = scenario_phases + "); \n"
        scenario_phases = scenario_phases + "ped"+str(i+1)+"_destination = ( \"lane_" + str(peds[i][-1][0])+"\"->" + str(peds[i][-1][1]) + "); \n"
        scenario_phases = scenario_phases + "ped"+str(i+1)+"_destination_state = (ped" + str(i+1) + "_destination); \n"
        scenario_phases = scenario_phases + "ped"+str(i+1)+"=Pedestrian(ped"+str(i+1)+"_init_state, npc"+str(i+1)+"_waypoints, ped"+str(i+1)+"_destination_state);\n"
        scenario_phases = scenario_phases + "\n"

    scenario_phases = scenario_phases + weather + "\n\n"
    scenario_phases = scenario_phases + create

    return scenario_phases


def combination_scenario(scenario):
    blocks = scenario.split('\n\n')
    ego = blocks[0]
    weather = blocks[-2]
    create = blocks[-1]
    # for i in range(len(blocks)):
    #     if '...' in blocks[i]:
    #         tmp = blocks[i].split('...')
    #         del blocks[i]
    #         for tmp_each in tmp:
    #             blocks.append(tmp_each)
    npc_ped = create_scenario({"npcs": [], "peds": []}, scenario)
    npcs = npc_ped['npcs']
    peds = npc_ped['peds']
    combined = False
    if len(npcs) > 1:
        # crossover = random.choice[1, 2]
        crossed_npc = random.sample(range(0, len(npcs)), 2)
        npcs[crossed_npc[0]] = insert_waypoints(npcs[crossed_npc[0]], npcs[crossed_npc[1]])
        combined = True
        # npc_ped['npcs'].append(npcs)

    if len(peds) > 1:
        crossed_ped = random.sample(range(0, len(peds)), 2)
        peds[crossed_ped[0]] = insert_waypoints(peds[crossed_ped[0]], peds[crossed_ped[1]])
        combined = True
        # npc_ped['peds'].append(peds)
    if combined:
        return ego, weather, create, npc_ped
    else:
        return None


def insert_waypoints(target_array, insert_array):
    pre_index = 0
    for i in range(len(insert_array)):
        each = insert_array[i]
        if each in target_array:
            continue
        elif i > 0:
            pre_index = target_array.index(insert_array[i-1])
        min_distance = 9999
        index = -1
        for i in range(pre_index, len(target_array)):
            distance = abs(int(target_array[i][0])-int(each[0]))
            if distance <= min_distance:
                index = i
                min_distance = distance
        if abs(int(each[0])-int(target_array[index][0])) < 4 and (int(each[1]) - int(target_array[index][1])) < 0:
            if index == 0:
                target_array = [each] + target_array
            else:
                target_array = target_array[:index] + [each] + target_array[index:]
        else:
            target_array = target_array[:index+1] + [each] + target_array[index+1:]

    return target_array


def rename_npc(npc):
    result = []
    pattern = "npc"
    if "ped" in npc[0]:
        pattern = "ped"
    for i in range(len(npc)):
        number = find_first_char_after_word(npc[i], pattern)
        # if number.isdigit():
        result.append(number)
    if has_duplicates(result):
        for i in range(len(npc)):
            if result[i].isdigit():
                npc[i] = npc[i].replace(pattern + str(result[i]), pattern + str(i + 1))
            else:
                npc[i] = npc[i].replace(pattern, pattern + str(i + 1))

    return npc


def combination_scenarios(scenario1, scenario2):
    blocks_1 = scenario1.split('\n\n')
    blocks_2 = scenario2.split('\n\n')
    for i in range(len(blocks_1)):
        if '...' in blocks_1[i]:
            tmp = blocks_1[i].split('...')
            del blocks_1[i]
            for tmp_each in tmp:
                blocks_1.append(tmp_each)
    for i in range(len(blocks_2)):
        if '...' in blocks_2[i]:
            tmp = blocks_2[i].split('...')
            del blocks_2[i]
            for tmp_each in tmp:
                blocks_2.append(tmp_each)
    npcs_1, npcs_2, peds_1, peds_2 = [], [], [], []
    for block in blocks_1:
        if 'npc' in block and '->' in block:
            npcs_1.append(block)
        elif 'ped' in block and '->' in block:
            peds_1.append(block)
    for block in blocks_2:
        if 'npc' in block and '->' in block:
            npcs_2.append(block)
        elif 'ped' in block and '->' in block:
            peds_2.append(block)

    whole_npc, whole_ped = [], []
    for each in npcs_1:
        whole_npc.append(each)
    for each in npcs_2:
        whole_npc.append(each)
    for each in peds_1:
        whole_ped.append(each)
    for each in peds_2:
        whole_ped.append(each)

    crossed_npc_1 = random.randint(0, len(npcs_1) - 1)
    crossed_npc_2 = random.randint(0, len(npcs_2) - 1)
    crossed_ped_1 = random.randint(0, len(peds_1) - 1)
    crossed_ped_2 = random.randint(0, len(peds_2) - 1)
    npcs_2.append(npcs_1[crossed_npc_1])
    npcs_1.append(npcs_2[crossed_npc_2])
    peds_2.append(peds_1[crossed_ped_1])
    peds_1.append(peds_2[crossed_ped_2])

    npcs_1 = rename_npc(npcs_1)
    npcs_2 = rename_npc(npcs_2)
    whole_npc = rename_npc(whole_npc)
    peds_1 = rename_npc(peds_1)
    peds_2 = rename_npc(peds_2)
    whole_ped = rename_npc(whole_ped)

    scenario_1 = blocks_1[0] + "\n\n"
    scenario_2 = blocks_2[0] + "\n\n"
    block_3 = random.choice([blocks_1, blocks_2])
    whole_scenario = block_3[0] + "\n\n"

    for each in npcs_1:
        scenario_1 = scenario_1 + each + "\n\n"
    for each in peds_1:
        scenario_1 = scenario_1 + each + "\n\n"
    for each in blocks_1:
        if "weather" in each and "CreateScenario" not in each:
            scenario_1 = scenario_1 + each + "\n\n"
        if "CreateScenario" in each:
            scenario_1 = scenario_1 + each + "\n\n"
    for each in npcs_2:
        scenario_2 = scenario_2 + each + "\n\n"
    for each in peds_2:
        scenario_2 = scenario_2 + each + "\n\n"
    for each in blocks_2:
        if "weather" in each and "CreateScenario" not in each:
            scenario_2 = scenario_2 + each + "\n\n"
        if "CreateScenario" in each:
            scenario_2 = scenario_2 + each + "\n\n"
    for each in whole_npc:
        whole_scenario = whole_scenario + each + "\n\n"
    for each in whole_ped:
        whole_scenario = whole_scenario + each + "\n\n"
    for each in block_3:
        if "weather" in each and "CreateScenario" not in each:
            whole_scenario = whole_scenario + each + "\n\n"
        if "CreateScenario" in each:
            whole_scenario = whole_scenario + each + "\n\n"

    return scenario_1, scenario_2, whole_scenario


def extend_scenario(scenario):
    blocks = scenario.split('\n\n')
    ego = blocks[0]
    weather = blocks[-2]
    create = blocks[-1]
    npc_ped = create_scenario({"npcs": [], "peds": []}, scenario)
    npcs = npc_ped['npcs']
    peds = npc_ped['peds']
    combined = False

    if len(npcs) > 0:
        new_npcs = []
        for each in npcs:
            new_npc = []
            for item in each:
                distance = int(item[1])
                if distance > 20:
                    new_npc.append([item[0], str(distance-20), item[-1]])
                elif distance > 10:
                    new_npc.append([item[0], str(distance - 10), item[-1]])
                else:
                    new_npc.append([item[0], str(distance - 5), item[-1]])
            new_npcs.append(new_npc)
        for new_npc in new_npcs:
            npc_ped['npcs'].append(new_npc)
            combined = True

    if len(peds) > 0:
        new_peds = []
        for each in peds:
            new_ped = []
            for item in each:
                distance = int(item[1])
                if distance > 20:
                    new_ped.append([item[0], str(distance - 20)])
                elif distance > 10:
                    new_ped.append([item[0], str(distance - 10)])
                else:
                    new_ped.append([item[0], str(distance - 5)])
            new_peds.append(new_ped)
        for new_ped in new_peds:
            npc_ped['peds'].append(new_ped)
            combined = True

    if combined:
        scenario = waypoints_scenario(ego, weather, create, npc_ped)
        return scenario
    else:
        return None


def fuzz_engine(scenarios):
    # 场景内如果只有一个npc，那就不做内部交叉

    file_list = os.listdir("local_generated_scenarios/dangerous_scenarios")
    index = random.sample(range(0, len(file_list)), 2)
    with open("scenario_description/scenario_folder1/scenario_" + str(index[0]), "r") as f:
        selected_scenario = f.read()
    selected_npc_ped = create_scenario({"npcs": [], "peds": []}, selected_scenario)
    selected_npc = selected_npc_ped['npcs']
    selected_ped = selected_npc_ped['peds']
    with open("scenario_description/scenario_folder1/scenario_" + str(index[1]), "r") as f:
        selected_scenario = f.read()
    selected_npc_ped = create_scenario({"npcs": [], "peds": []}, selected_scenario)
    selected_npc1 = selected_npc_ped['npcs']
    selected_ped1 = selected_npc_ped['peds']
    if len(selected_npc1) > len(selected_npc):
        selected_npc = selected_npc1
    if len(selected_ped1) > len(selected_ped):
        selected_ped = selected_ped1


if __name__ == '__main__':
    # system_prompt, content = first_prompt()
    # request_gpt(system_prompt, content)
    # test_prompt("prompt_content/prompt_test.txt")
    # print("finish")
    with open("scenario_description/scenario_folder1/scenario_5", "r") as f:
        scenario = f.read()
    # with open("scenario_description/scenario_folder1/scenario_3", "r") as f:
    #     scenario_2 = f.read()
    # scenarios = combination_scenarios(scenario, scenario_2)
    # scenario1, scenario2 = crossover_scenarios(scenario, scenario_2)

    scenario = extend_scenario(scenario)
    print("finish")

    # target_array = [[41, 10], [42, 20], [758, 1]]
    # insert_array = [[42, 15], [759, 1], [50, 1]]
    # target_array = [[39, 30], [759, 1], [77, 1], [77, 100]]
    # insert_array = [[39, 10], [39, 20], [40, 30], [40, 60]]
    # print(target_array[:2])
    # result = [[39, 10]] + target_array
    # result = insert_waypoints(target_array, insert_array)
    # print(result)
