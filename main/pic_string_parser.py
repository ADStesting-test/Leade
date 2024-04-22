import copy
import re

import spacy
from spacy.matcher import PhraseMatcher
from stanfordcorenlp import StanfordCoreNLP


def match_weather(text):
    nlp = spacy.load("en_core_web_sm")
    user_dictionary = list()
    with open("configuration/dict/weather_properties.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            user_dictionary.append(line.strip())

    matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp(term) for term in user_dictionary]
    matcher.add("UserDefinedTerms", None, *patterns)

    doc = nlp(text)
    lemmas = [(token.text, token.lemma_) for token in doc]
    word = ''
    for item in lemmas:
        item = item[1] + " "
        word += item

    doc = nlp(word.strip())
    matches = matcher(doc)
    weather = list()
    level = list()
    for match_id, start, end in matches:
        ap = True
        span = doc[start:end]
        last_token_before_span = doc[max(start - 1, 0)]
        if len(weather) > 0:
            for each in weather:
                if span.text in each:
                    ap = False
            if ap:
                weather.append(span.text)
                level.append(last_token_before_span.text)
        else:
            weather.append(span.text)
            level.append(last_token_before_span.text)
        # print(f"Found match: '{span.text}' at positions {start}-{end}")
        # print(last_token_before_span)
    return weather, level


def match_level(level):
    user_dictionary = list()
    with open("configuration/dict/weather_level.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            user_dictionary.append(line.strip())
    for i in range(len(level)):
        if level[i] in user_dictionary:
            continue
        else:
            level[i] = ''

    return level


def extract_vehicle(text):
    standfordnlp = StanfordCoreNLP('stanford-corenlp-4.5.5/stanford-corenlp-4.5.5')
    parse_sentence = standfordnlp.dependency_parse(text)
    # print(parse_sentence)
    standfordnlp.close()
    # 与车辆、行为存在关系的，匹配方向、位置、快慢
    # 五元组方式，match文本中的车辆&行人的行为信息：类型+数量+位置+动作+方向
    relation = ['acomp', 'compound', 'advcl', 'advmod', 'nmod', 'agent', 'amod', 'csubjpass', 'dobj', 'obj', 'obl', 'iobj', 'nsubj', 'nsubjpass', 'num', 'number', 'ref', 'xcomp', 'xsubj', 'case']
    vehicle = list()
    vehicle_behavior = list()
    direction = list()
    position = list()
    sp = list()
    road = list()
    nlp = spacy.load("en_core_web_sm")

    with open("configuration/dict/vehicle.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            vehicle.append(line.strip())
    with open("configuration/dict/vehicle_behavior.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            vehicle_behavior.append(line.strip())
    # with open("dict/direction.txt", "r") as f:
    #     lines = f.readlines()
    #     for line in lines:
    #         direction.append(line.strip())
    with open("configuration/dict/position.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            position.append(line.strip())
    with open("configuration/dict/sp.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            sp.append(line.strip())
    with open("configuration/dict/rp.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            road.append(line.strip())

    vehicle_matcher = PhraseMatcher(nlp.vocab)
    vehicle_behavior_matcher = PhraseMatcher(nlp.vocab)
    # direction_matcher = PhraseMatcher(nlp.vocab)
    position_matcher = PhraseMatcher(nlp.vocab)
    road_matcher = PhraseMatcher(nlp.vocab)
    sp_matcher = PhraseMatcher(nlp.vocab)

    vehicle_patterns = [nlp(term) for term in vehicle]
    vehicle_behavior_pattern = [nlp(term) for term in vehicle_behavior]
    direction_patterns = [nlp(term) for term in direction]
    position_patterns = [nlp(term) for term in position]
    road_patterns = [nlp(term) for term in road]
    sp_patterns = [nlp(term) for term in sp]

    vehicle_matcher.add("UserDefinedTerms", None, *vehicle_patterns)
    vehicle_behavior_matcher.add("UserDefinedTerms", None, *vehicle_behavior_pattern)
    # direction_matcher.add("UserDefinedTerms", None, *direction_patterns)
    position_matcher.add("UserDefinedTerms", None, *position_patterns)
    road_matcher.add("UserDefinedTerms", None, *road_patterns)
    sp_matcher.add("UserDefinedTerms", None, *sp_patterns)

    doc = nlp(text)

    # tokens = [token.text for token in doc]
    lemmas = [(token.text, token.lemma_) for token in doc]
    word = ''
    for item in lemmas:
        item = item[1] + " "
        word += item

    doc = nlp(word.strip())
    vehicle_matches = vehicle_matcher(doc)
    vehicle_behavior_matches = vehicle_behavior_matcher(doc)
    road_matches = road_matcher(doc)
    # direction_matches = direction_matcher(doc)
    position_matches = position_matcher(doc)
    sp_matches = sp_matcher(doc)
    # extracted_vehicle = list()
    # extracted_vehicle_behavior = list()
    # if len(vehicle_matches) > 0:
    vehicle_tuple = {'vehicles':[], 'position':[], 'behaviors':[], 'direction':[]}
    for match_id, start, end in vehicle_matches:
        span = doc[start:end]
        # item = [span.text, start+1]
        vehicle_tuple['vehicles'].append(span.text)

    for match_id, start, end in vehicle_behavior_matches:
        span = doc[start:end]
        item = [span.text, start + 1]
        vehicle_tuple['behaviors'].append(item)
        # for i in range(len(vehicles)):
        #     for each in parse_sentence:
        #         if (each[0] in relation) and ((each[1]==vehicles[i][1] and each[2]==(start+1)) or (each[2]==vehicles[i][1] and each[1]==(start+1))):
        #             item = [span.text, start+1]
        #             vehicle_tuple['behaviors'].append(item)

    # for match_id, start, end in direction_matches:
    #     span = doc[start:end]
    #     behaviors = vehicle_tuple['behaviors']
    #     for i in range(len(behaviors)):
    #         for each in parse_sentence:
    #             if (each[0] in relation) and ((each[1]==behaviors[i][1] and each[2]==(start+1)) or (each[2]==behaviors[i][1] and each[1]==(start+1))):
    #                 # item = [span.text, start+1]
    #                 vehicle_tuple['direction'].append(span.text)

    # for match_id, start, end in position_matches:
    #     span = doc[start:end]
    #     vehicles = vehicle_tuple['vehicles']
    #     for i in range(len(vehicles)):
    #         for each in parse_sentence:
    #             if (each[0] in relation) and ((each[1]==vehicles[i][1] and each[2]==(start+1)) or (each[2]==vehicles[i][1] and each[1]==(start+1))):
    #                 item = [span.text, start+1]
    #                 vehicle_tuple['position'].append(item)

    # extracted_sp = list()
    for match_id, start, end in sp_matches:
        span = doc[start:end]
        # extracted_sp.append(span.text)
        behaviors = vehicle_tuple['behaviors']
        for i in range(len(behaviors)):
            for each in parse_sentence:
                if (each[0] in relation) and ((each[1]==behaviors[i][1] and each[2]==(start+1)) or (each[2]==behaviors[i][1] and each[1]==(start+1))):
                    vehicle_tuple['behaviors'][i].append(span.text)
    # vehicle_tuple['behaviors'].append(extracted_sp)

    for match_id, start, end in road_matches:
        p = doc[start:end]
        po = True
        flag = True
        for i in range(0, start+1):
            tmp = doc[max(0, (start-i)):(start+1-i)]
            if tmp.text in ['on', 'in', 'at', 'from']:
                po = False
                for id, st, ed in position_matches:
                    r = doc[st:ed]
                    for each in parse_sentence:
                        if (each[0] in relation) and ((each[1]==(start+1) and each[2]==(st+1)) or (each[2]==(start+1) and each[1]==(st+1))):
                            vehicle_tuple['position'].append([r.text, p.text])
                            flag = False
                if flag:
                    vehicle_tuple['position'].append([p.text])
                break
            elif tmp.text in ['to', 'towards', 'along']:
                po = False
                for id, st, ed in position_matches:
                    r = doc[st:ed]
                    for each in parse_sentence:
                        if (each[0] in relation) and ((each[1] == (start + 1) and each[2] == (st + 1)) or (each[2] == (start + 1) and each[1] == (st + 1))):
                            vehicle_tuple['direction'].append([r.text, p.text])
                            flag = False
                if flag:
                    vehicle_tuple['direction'].append([p.text])
                break
        if po:
            vehicle_tuple['position'].append([p.text])

    positions = vehicle_tuple['position']
    directions = vehicle_tuple['direction']
    if len(positions) > 1:
        for i in range(len(positions)-1):
            if (len(positions[i]) == 1) and (len(positions[i + 1]) > 1):
                for each in positions[i+1]:
                    if positions[i][0] == each:
                        del positions[i]
                        break
    vehicle_tuple['position'] = positions
    if len(directions) > 1:
        for i in range(len(directions)-1):
            if (len(directions[i]) == 1) and (len(directions[i + 1]) > 1):
                for each in directions[i + 1]:
                    if directions[i][0] == each:
                        del directions[i]
                        break
    vehicle_tuple['direction'] = directions

    return vehicle_tuple


def extract_pedestrian(text):
    standfordnlp = StanfordCoreNLP('stanford-corenlp-4.5.5/stanford-corenlp-4.5.5')
    parse_sentence = standfordnlp.dependency_parse(text)
    # print(parse_sentence)
    standfordnlp.close()
    # 与车辆、行为存在关系的，匹配方向、位置、快慢
    # 五元组方式，match文本中的车辆&行人的行为信息：类型+数量+位置+动作+方向
    relation = ['acomp', 'compound', 'advcl', 'advmod', 'nmod', 'agent', 'amod', 'csubjpass', 'dobj', 'obj', 'obl', 'iobj', 'nsubj', 'nsubjpass', 'num', 'number', 'ref', 'xcomp', 'xsubj', 'case']
    pedestrian = list()
    pedestrian_behavior = list()
    direction = list()
    position = list()
    sp = list()
    road = list()
    nlp = spacy.load("en_core_web_sm")

    with open("configuration/dict/pedestrian.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            pedestrian.append(line.strip())
    with open("configuration/dict/pedestrian_behavior.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            pedestrian_behavior.append(line.strip())
    # with open("dict/direction.txt", "r") as f:
    #     lines = f.readlines()
    #     for line in lines:
    #         direction.append(line.strip())
    with open("configuration/dict/position.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            position.append(line.strip())
    with open("configuration/dict/sp.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            sp.append(line.strip())
    with open("configuration/dict/rp.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            road.append(line.strip())

    pedestrian_matcher = PhraseMatcher(nlp.vocab)
    pedestrian_behavior_matcher = PhraseMatcher(nlp.vocab)
    # direction_matcher = PhraseMatcher(nlp.vocab)
    position_matcher = PhraseMatcher(nlp.vocab)
    road_matcher = PhraseMatcher(nlp.vocab)
    sp_matcher = PhraseMatcher(nlp.vocab)

    pedestrian_patterns = [nlp(term) for term in pedestrian]
    pedestrian_behavior_pattern = [nlp(term) for term in pedestrian_behavior]
    direction_patterns = [nlp(term) for term in direction]
    position_patterns = [nlp(term) for term in position]
    road_patterns = [nlp(term) for term in road]
    sp_patterns = [nlp(term) for term in sp]

    pedestrian_matcher.add("UserDefinedTerms", None, *pedestrian_patterns)
    pedestrian_behavior_matcher.add("UserDefinedTerms", None, *pedestrian_behavior_pattern)
    # direction_matcher.add("UserDefinedTerms", None, *direction_patterns)
    position_matcher.add("UserDefinedTerms", None, *position_patterns)
    road_matcher.add("UserDefinedTerms", None, *road_patterns)
    sp_matcher.add("UserDefinedTerms", None, *sp_patterns)

    doc = nlp(text)

    # tokens = [token.text for token in doc]
    lemmas = [(token.text, token.lemma_) for token in doc]
    word = ''
    for item in lemmas:
        item = item[1] + " "
        word += item

    doc = nlp(word.strip())
    pedestrian_matches = pedestrian_matcher(doc)
    pedestrian_behavior_matches = pedestrian_behavior_matcher(doc)
    road_matches = road_matcher(doc)
    # direction_matches = direction_matcher(doc)
    position_matches = position_matcher(doc)
    sp_matches = sp_matcher(doc)
    # extracted_vehicle = list()
    # extracted_vehicle_behavior = list()
    # if len(vehicle_matches) > 0:
    pedestrian_tuple = {'pedestrian':[], 'position':[], 'behaviors':[], 'direction':[]}
    for match_id, start, end in pedestrian_matches:
        span = doc[start:end]
        # item = [span.text, start+1]
        pedestrian_tuple['pedestrian'].append(span.text)

    for match_id, start, end in pedestrian_behavior_matches:
        span = doc[start:end]
        item = [span.text, start + 1]
        pedestrian_tuple['behaviors'].append(item)
        # for i in range(len(pedestrian_tuple['pedestrian'])):
        #     for each in parse_sentence:
        #         if (each[0] in relation) and ((each[1]==pedestrian[i][1] and each[2]==(start+1)) or (each[2]==pedestrian[i][1] and each[1]==(start+1))):
        #             item = [span.text, start+1]
        #             pedestrian_tuple['behaviors'].append(item)
    # extracted_sp = list()
    for match_id, start, end in sp_matches:
        span = doc[start:end]
        # extracted_sp.append(span.text)
        behaviors = pedestrian_tuple['behaviors']
        for i in range(len(behaviors)):
            for each in parse_sentence:
                if (each[0] in relation) and ((each[1]==behaviors[i][1] and each[2]==(start+1)) or (each[2]==behaviors[i][1] and each[1]==(start+1))):
                    pedestrian_tuple['behaviors'][i].append(span.text)
    # pedestrian_tuple['behaviors'].append(extracted_sp)

    for match_id, start, end in road_matches:
        p = doc[start:end]
        po = True
        flag = True
        for i in range(0, start + 1):
            tmp = doc[max(0, (start - i)):(start + 1 - i)]
            if tmp.text in ['on', 'in', 'at', 'from']:
                po = False
                for id, st, ed in position_matches:
                    r = doc[st:ed]
                    for each in parse_sentence:
                        if (each[0] in relation) and ((each[1]==(start+1) and each[2]==(st+1)) or (each[2]==(start+1) and each[1]==(st+1))):
                            pedestrian_tuple['position'].append([r.text, p.text])
                            flag = False
                if flag:
                    pedestrian_tuple['position'].append([p.text])
                break
            elif tmp.text in ['to', 'towards', 'along']:
                po = False
                for id, st, ed in position_matches:
                    r = doc[st:ed]
                    for each in parse_sentence:
                        if (each[0] in relation) and ((each[1] == (start + 1) and each[2] == (st + 1)) or (each[2] == (start + 1) and each[1] == (st + 1))):
                            pedestrian_tuple['direction'].append([r.text, p.text])
                            flag = False
                if flag:
                    pedestrian_tuple['direction'].append([p.text])
                break
        if po:
            # print("here")
            pedestrian_tuple['position'].append([p.text])

    positions = pedestrian_tuple['position']
    directions = pedestrian_tuple['direction']
    if len(positions) > 1:
        for i in range(len(positions) - 1):
            if (len(positions[i]) == 1) and (len(positions[i + 1]) > 1):
                for each in positions[i + 1]:
                    if positions[i][0] == each:
                        del positions[i]
                        break
    pedestrian_tuple['position'] = positions
    if len(directions) > 1:
        for i in range(len(directions) - 1):
            if (len(directions[i]) == 1) and (len(directions[i + 1]) > 1):
                for each in directions[i + 1]:
                    if directions[i][0] == each:
                        del directions[i]
                        break
    pedestrian_tuple['direction'] = directions

    return pedestrian_tuple


def extract_road(text):
    nlp = spacy.load("en_core_web_sm")
    user_dictionary = list()
    with open("configuration/dict/road.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            user_dictionary.append(line.strip())

    matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp(term) for term in user_dictionary]
    matcher.add("UserDefinedTerms", None, *patterns)

    doc = nlp(text)
    lemmas = [(token.text, token.lemma_) for token in doc]
    word = ''
    for item in lemmas:
        item = item[1] + " "
        word += item

    doc = nlp(word.strip())
    matches = matcher(doc)
    road = list()
    for match_id, start, end in matches:
        span = doc[start:end]
        road.append(span.text)

    return road


def extract_traffic_sign(text):
    nlp = spacy.load("en_core_web_sm")
    user_dictionary = list()
    with open("configuration/dict/traffic_sign.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            user_dictionary.append(line.strip())

    matcher = PhraseMatcher(nlp.vocab)
    patterns = [nlp(term) for term in user_dictionary]
    matcher.add("UserDefinedTerms", None, *patterns)

    doc = nlp(text)
    lemmas = [(token.text, token.lemma_) for token in doc]
    word = ''
    for item in lemmas:
        item = item[1] + " "
        word += item

    doc = nlp(word.strip())
    matches = matcher(doc)
    traffic_sign = list()
    for match_id, start, end in matches:
        span = doc[start:end]
        traffic_sign.append(span.text)

    return traffic_sign


def parse_pic_string(text):
    text = text.lower()
    text = text.strip()
    if "_" in text:
        text = text.replace("_", " ")
        text = text.replace("-", " ")
    text = re.split(r'[.]', text)
    weather, vehicle, pedestrian, road, traffic_sign = [], [], [], [], []
    pedestrian_dic = list()
    vehicle_dic = list()
    nlp = spacy.load("en_core_web_sm")
    with open("configuration/dict/pedestrian.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            pedestrian_dic.append(line.strip())
    with open("configuration/dict/vehicle.txt", "r") as f:
        lines = f.readlines()
        for line in lines:
            vehicle_dic.append(line.strip())
    pedestrian_matcher = PhraseMatcher(nlp.vocab)
    vehicle_matcher = PhraseMatcher(nlp.vocab)
    pedestrian_patterns = [nlp(term) for term in pedestrian_dic]
    vehicle_patterns = [nlp(term) for term in vehicle_dic]
    pedestrian_matcher.add("UserDefinedTerms", None, *pedestrian_patterns)
    vehicle_matcher.add("UserDefinedTerms", None, *vehicle_patterns)

    for each in text:
        if each == '':
            continue
        else:
            w, l = match_weather(each)
            if len(w) > 0:
                level = match_level(l)
                if len(level) > 0:
                    for i in range(len(w)):
                        w[i] = level[i] + " " + w[i]
                        w[i] = w[i].strip()
                for each in w:
                    weather.append(each)
                continue
            else:
                doc = nlp(each)
                lemmas = [(token.text, token.lemma_) for token in doc]
                word = ''
                for item in lemmas:
                    item = item[1] + " "
                    word += item

                doc = nlp(word.strip())
                pedestrian_matches = pedestrian_matcher(doc)
                vehicle_matches = vehicle_matcher(doc)
                if len(vehicle_matches) > 0:
                    extracted_vehicle = extract_vehicle(each)
                    if len(extracted_vehicle['behaviors']) > 0:
                        vehicle.append(extracted_vehicle)
                if len(pedestrian_matches) > 0:
                    extracted_pedestrian = extract_pedestrian(each)
                    if len(extracted_pedestrian['behaviors']) > 0:
                        pedestrian.append(extracted_pedestrian)
                if len(pedestrian_matches) == 0 and len(vehicle_matches) == 0:
                    extracted_road = extract_road(each)
                    if 'road' in extracted_road:
                        extracted_road.remove('road')
                    extracted_traffic_sign = extract_traffic_sign(each)
                    for item in extracted_road:
                        road.append(item)
                    for item in extracted_traffic_sign:
                        traffic_sign.append(item)

    new_vehicle = []
    for count in range(len(vehicle)):
        each = vehicle[count]
        vehicles = each['vehicles']
        tmp_vehicles = []
        if len(vehicles) > 1:
            for i in vehicles:
                if i != 'vehicle':
                    tmp_vehicles.append(i)
            if len(tmp_vehicles) == 0:
                tmp_vehicles.append('vehicle')
        else:
            tmp_vehicles.append(vehicles[0])
        for j in tmp_vehicles:
            tmp_item = copy.deepcopy(vehicle[count])
            tmp_item['vehicles'] = [j]
            new_vehicle.append(tmp_item)

    return [weather, new_vehicle, pedestrian, road, traffic_sign]
    # for match_id, start, end in matches:
    #     span = doc[start:end]
    #     last_token_before_span = doc[max(start-1, 0)]
    #     print(f"Found match: '{span.text}' at positions {start}-{end}")
    #     print(last_token_before_span)

# 环境（天气、交通信号灯），行人，车辆，道路
# 提取出的参与者信息，记录为五元组
if __name__ == '__main__':
    # sentence = "The road is an intersection. There is a traffic light at the crossing. The truck moves on the left road slowly. The boy walks along the street. A driver drives to the left lane before the traffic light."
    # sentence = "The weather is slightly rainy and cloudy. The road is an T-junction with a traffic light. One vehicle drives from the left to the right side. Two cyclists are visible on the road, one crossing the intersection and another one moving slowly on the left lane."
    # sentence = sentence + " The vehicle is either stopped or moving very slowly, waiting for the cyclists to pass before proceeding through the security checkpoint."
    with open("test/result", "r") as f:
        lines = f.read()
    print(parse_pic_string(lines))

