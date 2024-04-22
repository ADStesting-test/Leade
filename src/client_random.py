import copy
import os
import select
import shutil
import signal
import sys
import time
import warnings
from pathlib import Path
from threading import Timer

import websockets
import json
import asyncio
from EXtraction import ExtractAll
from GeneticAlgorithm_hxs import GAGeneration, EncodedTestCase, DecodedTestCase
from TestCaseRandom import TestCaseRandom
from datetime import datetime
from AssertionExtraction import SingleAssertion
from map import get_map_info

import logging

# logging.basicConfig(level=level, handlers=[stdout_handler, file_handler],format='%(asctime)s, %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.FileHandler('test.log', 'a'))
# logger.addHandler(logging.StreamHandler(sys.stdout))




min_fitness_list = []
ave_fitness_list = []


def to_json(obj):
    return json.dumps(obj, default=lambda o: o.__dict__, indent=4)



async def hello(scenario_msg, single_spec, generation_number=1, population_size=3, directory=None) -> object:
    uri = "ws://localhost:6666"
    async with websockets.connect(uri, max_size=None) as websocket:
        scenario_no = len(scenario_msg)
        while True:
            prediction_msg = json.dumps({'CMD': "CMD_RESTART_PREDICTION_MODULE"})
            await websocket.send(prediction_msg)
            msg = await websocket.recv()
            msg = json.loads(msg)
            if msg['TYPE'] == 'PREDICTION_MODULE_STARTED':
                break
        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
        await websocket.send(init_msg)
        # for i in range(scenario_no):
        # logging.info('iteration: {}'.format(i))
        msg = await websocket.recv()
        msg = json.loads(msg)
        if msg['TYPE'] == 'READY_FOR_NEW_TEST' and msg['DATA']:
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            with open(directory + '/Incompleted.txt', 'a') as f:
                f.write('Time: {} \n'.format(dt_string))
            with open(directory + '/bugTestCase.txt', 'a') as f:
                f.write('Time: {} \n'.format(dt_string))
            with open(directory + '/NoTrace.txt', 'a') as f:
                f.write('Time: {} \n'.format(dt_string))
            population = []
            new_testcases = []
            init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
            await websocket.send(init_msg)
            for i in range(scenario_no):
                while True:
                    msg = await websocket.recv()
                    msg = json.loads(msg)
                    if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                        if msg['DATA']:
                            logging.info('Running Predefined Test Case: {}'.format(i))
                            send_msg = {'CMD': "CMD_NEW_TEST", 'DATA': scenario_msg[i]}
                            await websocket.send(json.dumps(send_msg))
                        else:
                            time.sleep(3)
                            init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                            await websocket.send(init_msg)
                    elif msg['TYPE'] == 'TEST_TERMINATED' or msg['TYPE'] == 'ERROR':
                        print("Try to reconnect!")
                        time.sleep(3)
                        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                        await websocket.send(init_msg)
                    elif msg['TYPE'] == 'TEST_COMPLETED':
                        output_trace = msg['DATA']
                        now = datetime.now()
                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                        file = directory + '/data/result' + dt_string + '.json'
                        with open(file, 'w') as outfile:
                            json.dump(output_trace, outfile, indent=2)
                        if not output_trace['destinationReached']:
                            logging.info("Not reach the destination")
                            with open(directory + '/Incompleted.txt', 'a') as f:
                                json.dump(scenario_msg[i], f, indent=2)
                                f.write('\n')
                        if len(output_trace['trace']) > 1:
                            encoded_testcase = EncodedTestCase(output_trace, single_spec)
                            logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                            del encoded_testcase.trace
                            if encoded_testcase.fitness < 0.0:
                                with open(directory + '/bugTestCase.txt', 'a') as bug_file:
                                    json.dump(output_trace, bug_file, indent=2)
                                    bug_file.write('\n')
                            population.append(encoded_testcase)
                        elif len(output_trace['trace']) == 1:
                            logging.info(
                                "Is reached: {}, minimal distance: {}".format(output_trace['destinationReached'],
                                                                              output_trace['minEgoObsDist']))
                            testcase = TestCaseRandom(output_trace)
                            testcase.testcase_random(1)
                            new_testcases.append(testcase.cases[-1])
                        else:
                            logging.info("No trace for the test cases")
                            with open(directory + '/NoTrace.txt', 'a') as f:
                                json.dump(scenario_msg[i], f, indent=2)
                                f.write('\n')
                            testcase = TestCaseRandom(output_trace)
                            testcase.testcase_random(1)
                            new_testcases.append(testcase.cases[-1])
                        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                        await websocket.send(init_msg)
                        break
            new_testcases = []
            test_case_number = (generation_number + 1) * population_size
            testcase = TestCaseRandom(output_trace)
            testcase.testcase_random(test_case_number)
            for i2 in range(len(testcase.cases) - 1):
                new_testcases.append(testcase.cases[i2 + 1])

            with open(directory + '/TestCase.txt', 'w') as outfile:
                for i1 in range(len(new_testcases)):
                    json.dump(new_testcases[i1], outfile, indent=2)
                    outfile.write('\n')
            for j in range(len(new_testcases)):
                    # deal with each test case
                individual_number = j % population_size
                if individual_number == 0:
                    await websocket.recv()
                    while True:
                        prediction_msg = json.dumps({'CMD': "CMD_RESTART_PREDICTION_MODULE"})
                        await websocket.send(prediction_msg)
                        msg = await websocket.recv()
                        msg = json.loads(msg)
                        if msg['TYPE'] == 'PREDICTION_MODULE_STARTED':
                            break
                    init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                    await websocket.send(init_msg)
                generation = int((j - individual_number) / population_size)
                while True:
                    msg = await websocket.recv()
                    msg = json.loads(msg)
                    print(msg['TYPE'])
                    if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                        if msg['DATA']:
                            logging.info('Running Generation: {}, Individual: {}'.format(generation, individual_number))
                            send_msg = {'CMD': "CMD_NEW_TEST", 'DATA': new_testcases[j]}
                            await websocket.send(json.dumps(send_msg))
                        else:
                            time.sleep(3)
                            init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                            await websocket.send(init_msg)
                    elif msg['TYPE'] == 'TEST_TERMINATED' or msg['TYPE'] == 'ERROR':
                        print(msg)
                        print("Try to reconnect.")
                        time.sleep(3)
                        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                        await websocket.send(init_msg)
                    elif msg['TYPE'] == 'TEST_COMPLETED':
                        output_trace = msg['DATA']
                        now = datetime.now()
                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                        file = directory + '/data/result' + dt_string + '.json'
                        with open(file, 'w') as outfile:
                            json.dump(output_trace, outfile, indent=2)
                        logging.info("The number of states in the trace is {}".format(len(output_trace['trace'])))
                        if not output_trace['destinationReached']:
                            with open(directory + '/Incompleted.txt', 'a') as f:
                                json.dump(new_testcases[j], f, indent=2)
                                f.write('\n')
                        if len(output_trace['trace']) > 1:
                            encoded_testcase = EncodedTestCase(output_trace, single_spec)
                            logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                            del encoded_testcase.trace
                            if encoded_testcase.fitness < 0.0:
                                with open(directory + '/bugTestCase.txt', 'a') as bug_file:
                                    now = datetime.now()
                                    dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                    string_index = "Time:" + dt_string + "Generation: " + str(
                                        generation) + ", Individual: " + str(individual_number) + '\n'
                                    bug_file.write(string_index)
                                    json.dump(output_trace, bug_file, indent=2)
                                    bug_file.write('\n')
                        elif len(output_trace['trace']) == 1:
                            logging.info("Only one state. Is reached: {}, minimal distance: {}".format(
                                output_trace['destinationReached'], output_trace['minEgoObsDist']))
                        else:
                            logging.info("No trace for the test cases!")
                            with open(directory + '/NoTrace.txt', 'a') as f:
                                now = datetime.now()
                                dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                f.write("Time: Generation: {}, Individual: {}".format(dt_string, generation, j))
                                json.dump(new_testcases[j], f, indent=2)
                                f.write('\n')
                        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                        await websocket.send(init_msg)
                        break



def spec_scenario(spec, testcase, generations=0, pop_size=1,file_directory=None):
    loop = asyncio.get_event_loop()
    scenario_specification = copy.deepcopy(spec)
    scenario_testcase = copy.deepcopy(testcase)
    msgs = [scenario_testcase]
    with open(file_directory + '/InitTestCase.txt', 'w') as f:
        json.dump(scenario_testcase, f, indent=2)
    loop.run_until_complete(
        asyncio.gather(hello(msgs, scenario_specification, generation_number=generations, population_size=pop_size, directory=file_directory)))


def test_scenario(direct, item):
    file = direct + item
    log_direct = "random_5/" + Path(item).stem
    if not os.path.exists(log_direct):
        os.makedirs(log_direct)
    else:
        shutil.rmtree(log_direct)

    if not os.path.exists(log_direct + '/data'):
        os.makedirs(log_direct + '/data')

    logging_file = log_direct + '/test.log'
    file_handler = logging.FileHandler(logging_file, mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(level=logging.INFO, handlers=[stdout_handler, file_handler], format='%(asctime)s, %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    logging.info("Current Test Case: {}".format(item))
    isGroundTruth = True
    extracted_data = ExtractAll(file, isGroundTruth)
    testcases = extracted_data.Get_TestCastINJsonList()
    all_specifications = extracted_data.Get_Specifications()
    maps = extracted_data.Get_AllMaps()

    for i in range(len(testcases)):
        test_case = testcases[i]
        scenario_name = test_case['ScenarioName']
        # logging.info("Current scenario is {}.\n".format(scenario_name))
        try:
            specifications_in_scenario = all_specifications[scenario_name]
            current_map = maps[scenario_name]
            ego_init_start = test_case['ego']['start']
            map_info = get_map_info(current_map)
            if "lane_position" in ego_init_start.keys():
                lane_position = ego_init_start['lane_position']
                ego_position = map_info.get_position([lane_position['lane'], lane_position['offset']])
            else:
                ego_position = (ego_init_start['position']['x'], ego_init_start['position']['y'], ego_init_start['position']['z'])
            for spec_index in range(len(specifications_in_scenario)):
                first_specification = specifications_in_scenario[spec_index]
                single_specification = SingleAssertion(first_specification, current_map, ego_position)
                logging.info("\n Evaluate Scenario {} with Assertion {}: {} \n ".format(scenario_name, spec_index, single_specification.specification))
                spec_scenario(spec=single_specification, testcase=test_case, generations=25, pop_size=20, file_directory=log_direct)
        except KeyError:
            spec_scenario(spec={}, testcase=test_case)



if __name__ == "__main__":
    direct = 'test_cases/final/'
    arr = os.listdir(direct)
    arr = sorted(arr)
    # arr = ['intersection5.txt', 'lanechange1.txt', 'lanechange2.txt', 'lanechange3.txt', 'overtaking1.txt']
    for item in arr:
        test_scenario(direct, item)
    # test_scenario("test_cases/", "input-test.txt")
    # items = ['change02.txt', 'change03.txt', 'change04.txt']
    # for item in items:
    #     test_scenario(direct, item)
    # file = 'test_cases/input-test.txt'
    # file = 'test_cases/lane_changing/change04.txt'
    # file = 'test_cases/overtaking/overtaking0.txt'
    # direct = 'test_cases/intersection/'
    # arr = os.listdir(direct)
    # arr = sorted(arr)
    # # arr = ['intersection3.txt', 'intersection4.txt', 'intersection5.txt']
    # for item in arr:
    #     # file = 'test_cases/intersection/intersection4.txt'
    #     # file = 'test_cases/lane_following/following31.txt'
    #     # item = "intersection1.txt"
    #     logging.info("Current Test Case: {}".format(item))
    #     file = direct + item
    #     log_direct = file_name = Path(item).stem
    #     if not os.path.exists(log_direct):
    #         os.makedirs(log_direct)
    #     if not os.path.exists(log_direct + '/data'):
    #         os.makedirs(log_direct + '/data')
    #     isGroundTruth = True
    #     extracted_data = ExtractAll(file, isGroundTruth)
    #     testcases = extracted_data.Get_TestCastINJsonList()
    #     all_specifications = extracted_data.Get_Specifications()
    #     maps = extracted_data.Get_AllMaps()
    #
    #     # # demo
    #     # test_case = testcases[0]
    #     # scenario_name = test_case['ScenarioName']
    #     # specifications_in_scenario = all_specifications[scenario_name]
    #     # current_map = maps[scenario_name]
    #     # ego_init_start = test_case['ego']['start']
    #     # map_info = get_map_info(current_map)
    #     # if "lane_position" in ego_init_start.keys():
    #     #     lane_position = ego_init_start['lane_position']
    #     #     ego_position = map_info.get_position([lane_position['lane'], lane_position['offset']])
    #     # else:
    #     #     ego_position = (ego_init_start['position']['x'], ego_init_start['position']['y'], ego_init_start['position']['z'])
    #     # # for spec_index in range(len(specifications_in_scenario)):
    #     # spec_index = 5
    #     # first_specification = specifications_in_scenario[spec_index]
    #     # single_specification = SingleAssertion(first_specification, current_map, ego_position)
    #     # logging.info("\n Evaluate Scenario {} with Assertion {}: {}\n".format(scenario_name, spec_index, single_specification.specification))
    #     # spec_scenario(spec=single_specification, testcase=test_case, generations=2, pop_size=3)
    #
    #     for i in range(len(testcases)):
    #         test_case = testcases[i]
    #         scenario_name = test_case['ScenarioName']
    #         # logging.info("Current scenario is {}.\n".format(scenario_name))
    #         try:
    #             specifications_in_scenario = all_specifications[scenario_name]
    #             current_map = maps[scenario_name]
    #             ego_init_start = test_case['ego']['start']
    #             map_info = get_map_info(current_map)
    #             if "lane_position" in ego_init_start.keys():
    #                 lane_position = ego_init_start['lane_position']
    #                 ego_position = map_info.get_position([lane_position['lane'], lane_position['offset']])
    #             else:
    #                 ego_position = (ego_init_start['position']['x'], ego_init_start['position']['y'], ego_init_start['position']['z'])
    #             for spec_index in range(len(specifications_in_scenario)):
    #                 first_specification = specifications_in_scenario[spec_index]
    #                 single_specification = SingleAssertion(first_specification, current_map, ego_position)
    #                 logging.info("\n Evaluate Scenario {} with Assertion {}: {}\n".format(scenario_name, spec_index, single_specification.specification))
    #                 spec_scenario(spec=single_specification, testcase=test_case, generations=25, pop_size=20, file_directory=log_direct)
    #         except KeyError:
    #             spec_scenario(spec={}, testcase=test_case)



