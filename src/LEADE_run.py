import os
import random

from main.ele_to_scenario import pics_to_scenario_program
from main.extract_scenario_info import video_to_pics, extract_pic
from main.pic_string_parser import parse_pic_string
from main.scenario_mutation import first_prompt, request_gpt
from client_1 import adp_evolution


def run(path):
    pic_folders = os.listdir("../main/video/output_images")
    pic_path = "video/output_images_"+str(len(pic_folders)-1)
    # video_to_pics(path, pic_path)
    result = extract_pic(pic_path)
    abstract_scenario = parse_pic_string(result)
    scenario1, scenario2, road = pics_to_scenario_program(abstract_scenario)
    system_prompt, content = first_prompt(random.choice([scenario1, scenario2]), "start_prompt.txt", road)
    request_gpt(system_prompt, content)
    adp_evolution(6)

if __name__ == '__main__':
    run("../main/video/test.mp4")