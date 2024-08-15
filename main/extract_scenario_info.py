import base64
import os
import cv2

import requests
from openai import OpenAI

import base64
import requests
import numpy as np


def open_sensor_data(file_path):
    # 使用numpy加载.npy文件
    loaded_array = np.load(file_path)

    # 现在，loaded_array 中包含了.npy文件中保存的数组数据，你可以使用它进行进一步的处理
    return loaded_array


def split_video_to_images(video_path, output_folder, interval_seconds):
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)

    # 确保视频文件被成功打开
    if not cap.isOpened():
        print("Error: 无法打开视频文件")
        return

    # 获取视频的帧率
    fps = cap.get(cv2.CAP_PROP_FPS)

    # 计算每隔多少帧截取一张图片
    interval_frames = int(fps * interval_seconds)

    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)

    # 读取视频帧并保存为图片
    frame_count = 0
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if frame_count % interval_frames == 0:
            # 构造输出文件路径
            output_path = os.path.join(output_folder, f"frame_{frame_count // interval_frames}.png")

            # 保存帧为图片
            cv2.imwrite(output_path, frame)

        frame_count += 1

    # 释放视频文件
    cap.release()

    print(f"成功将视频分割成图片，共 {frame_count // interval_frames} 张图片")


def video_to_pics(path, output):
    video_path = path  # 替换为你的视频文件路径
    output_folder = output  # 替换为你想保存图片的文件夹路径
    interval_seconds = 2  # 指定截取图片的时间间隔（秒）
    split_video_to_images(video_path, output_folder, interval_seconds)


# OpenAI API Key
api_key = ""


# Function to encode the image
def encode_image(image_path):
    pictures_path = os.listdir(image_path)
    file_ls = []
    for each in pictures_path:
        item = image_path + "/" + each
        file_ls.append(item)
    # file_ls = [os.path.join(image_path, file) for file in pictures_path]
    pictures = []
    for each in file_ls:
        with open(each, "rb") as image_file:
            pictures.append(base64.b64encode(image_file.read()).decode('utf-8'))
    return pictures


def extract_pic(path):
    base64_image = encode_image(path)

    # # Path to your image
    # image_path = "path_to_your_image.jpg"
    #
    # # Getting the base64 string
    # base64_image = encode_image(image_path)

    headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {api_key}"
    }

    with open("prompt_content/extract_prompt.txt", "r") as f:
        test_prompt = f.read()

    payload = {
      "model": "gpt-4-turbo",
      # "model": "gpt-4-vision-preview",
      "messages": [
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": test_prompt
            },
            {
              "type": "image_url",
              "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image[0]}",
              }
            }
          ]
        }
      ],
      "max_tokens": 300
    }

    for each in range(1, len(base64_image)):
        each_value = {"type": "image_url",
                      "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image[each]}",
                        }}
        payload["messages"][0]["content"].append(each_value)

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_json = response.json()
    response_content = response_json['choices'][0]['message']
    result = response_content['content']

    return result

def generate_concrete_scenarios(array, road):
    vehicles = array[1]
    vehicle_count = len(vehicles)
    pedestrian = array[2]
    pedestrian_count = len(pedestrian)
    prompt_path = "prompt_content/understanding_prompt.txt"
    with open(prompt_path, 'r') as f:
        prompt = f.read()
    prompts = prompt.split("\" \"")
    vehicle_behaviors = []
    for each in vehicles:
        behavior = ""
        if len(each['behaviors']) > 1:
            for item in each['behaviors']:
                if item[0] == "across":
                    item[0] = "traverse the road"
                behavior = behavior + item[0] + "+"
            behavior = behavior[:-1]
        else:
            if len(each['behaviors'][0]) == 0:
                behavior = "park"
            else:
                if each['behaviors'][0][0] == "across":
                    behavior = "traverse the road"
                else:
                    behavior = each['behaviors'][0][0]
        vehicle_behaviors.append(behavior)

    new_prompt = prompts[0]+str(vehicle_count)+prompts[1]
    for each in vehicle_behaviors:
        new_prompt = new_prompt + "\"" + each + "\", "
    new_prompt = new_prompt + "\""
    if pedestrian_count > 0:
        new_prompt = new_prompt + "\n"
        new_prompt = new_prompt + "There are " + str(pedestrian_count) + " pedestrians in each scenario. And their behaviors are \"walk across\" or \"walk along the lane\". \n"
    new_prompt = new_prompt + prompts[-1]
    new_prompts = new_prompt.split("'''")

    map_path = "test/road/" + road
    file_list = os.listdir(map_path)
    segment = random.randint(1, len(file_list)/2)
    road_picture = map_path + "/" + str(segment) + ".png"
    scenario_path = map_path + "/" + str(segment) + ".txt"
    with open(scenario_path, 'r') as f:
        scenario_example = f.read()
    whole_prompt = new_prompts[0] + "\n '''" + scenario_example + "\n" +new_prompts[-1]

    base64_image = encode_one_pic(road_picture)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # with open("prompt_content/extract_prompt.txt", "r") as f:
    #     test_prompt = f.read()

    payload = {
        "model": "gpt-4-turbo",
        # "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": whole_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image[0]}",
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    for each in range(1, len(base64_image)):
        each_value = {"type": "image_url",
                      "image_url": {
                          "url": f"data:image/jpeg;base64,{base64_image[each]}",
                      }}
        payload["messages"][0]["content"].append(each_value)

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_json = response.json()
    response_content = response_json['choices'][0]['message']
    result = response_content['content']

    results = result.split("------")

    scenario_path = "scenario_description/scenario_folder" + str(len(file_list))
    scenario_list = os.listdir(scenario_path)
    write_path1 = scenario_path + "/scenario_" + str(len(scenario_list)+1) + ".txt"
    write_path2 = scenario_path + "/scenario_" + str(len(scenario_list) + 2) + ".txt"
    with open(write_path1, 'w') as f:
        f.write(results[0])
    with open(write_path2, 'w') as f:
        f.write(results[1])

    return result

if __name__ == '__main__':
    # video_to_pics("video/test.mp4")
    result = extract_pic("video/output_images/0")
    print(result)