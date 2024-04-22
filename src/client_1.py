import copy
import os
import random

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
from main.ele_to_scenario import add_specifications
from main.scenario_mutation import feedback_generation, crossover_scenario, crossover_scenarios
from map import get_map_info

import logging
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# logging.basicConfig(level=level, handlers=[stdout_handler, file_handler],format='%(asctime)s, %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.FileHandler('test.log', 'a'))
# logger.addHandler(logging.StreamHandler(sys.stdout))




min_fitness_list = []
ave_fitness_list = []


def to_json(obj):
    return json.dumps(obj, default=lambda o: o.__dict__, indent=4)

def get_file_storage(directory, file_name):
    folder_path = directory + "/" + file_name
    folder = os.path.exists(folder_path)
    if not folder:
        os.makedirs(folder_path)
    file_list = os.listdir(folder_path)
    return folder_path + "/" + str(len(file_list)) + ".txt"

async def hello(file, scenario_msg, single_spec, generation_number=1, population_size=3, directory=None) -> object:
    print("here")
    uri = "ws://localhost:6666"
    violation_path = "../main/violation_scenario_description"
    scenario_path = "../main/safe_scenario_description"
    violation = False
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
            with open(get_file_storage(directory, 'Incompleted'), 'a', encoding="utf-8") as f:
                f.write('Time: {} \n'.format(dt_string))
            tmp_path = directory
            fileList = os.listdir(tmp_path)
            tmp_path = tmp_path + '/violation_scenario_' + str(len(fileList)+1) + ".txt"
            with open(tmp_path, 'a', encoding="utf-8") as f:
                f.write('Time: {} \n'.format(dt_string))
            with open(directory + '/NoTrace.txt', 'a', encoding="utf-8") as f:
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
                            print(scenario_msg[i])
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
                        if not output_trace['destinationReached']:
                            logging.info("Not reach the destination")
                            with open(directory + '/Incompleted.txt', 'a', encoding="utf-8") as f:
                                json.dump(scenario_msg[i], f, indent=2)
                                f.write('\n')
                        if len(output_trace['trace']) > 1:
                            encoded_testcase = EncodedTestCase(output_trace, single_spec)
                            output_trace['fitness'] = encoded_testcase.fitness
                            logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                            del encoded_testcase.trace
                            if encoded_testcase.fitness < 0.0:
                                tmp_path = directory
                                fileList = os.listdir(tmp_path)
                                tmp_path = tmp_path + '/violation_scenario_' + str(len(fileList)) + ".txt"
                                with open(tmp_path, 'a', encoding="utf-8") as bug_file:
                                    json.dump(output_trace, bug_file, indent=2)
                                    bug_file.write('\n')
                                msg_path = directory
                                fileList = os.listdir(msg_path)
                                msg_path = msg_path + '/violation_msg_' + str(len(fileList))
                                with open(msg_path, 'w') as msg_file:
                                    msg_file.write(json.dumps(msg['DATA']))
                                violation = True
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
                            with open(directory + '/NoTrace.txt', 'a', encoding="utf-8") as f:
                                json.dump(scenario_msg[i], f, indent=2)
                                f.write('\n')
                            testcase = TestCaseRandom(output_trace)
                            testcase.testcase_random(1)
                            new_testcases.append(testcase.cases[-1])
                        now = datetime.now()
                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                        file = directory + '/data/result' + dt_string + '.json'
                        with open(file, 'w', encoding="utf-8") as outfile:
                            json.dump(output_trace, outfile, indent=2)
                        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                        await websocket.send(init_msg)
                        break
                    # while True:
                    #     msg_valid = await websocket.recv()
                    #     msg_valid = json.loads(msg_valid)
                    #     # print("Received Message: " + msg_valid['TYPE'])
                    #     # if msg_valid['TYPE'] == 'ERROR' or 'TEST_STARTED':
                    #     #     print(msg_valid)
                    #     if msg_valid['TYPE'] == 'TEST_TERMINATED' or msg_valid['TYPE'] == 'ERROR':
                    #         print("Try to reconnect!")
                    #         init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                    #         await websocket.send(init_msg)
                    #         time.sleep(3)
                    #         msg = await websocket.recv()
                    #         msg = json.loads(msg)
                    #         if msg['TYPE'] == 'READY_FOR_NEW_TEST' and msg['DATA']:
                    #             send_msg = {'CMD': "CMD_NEW_TEST", 'DATA': scenario_msg[i]}
                    #             await websocket.send(json.dumps(send_msg))
                    #         continue
                    #     elif msg_valid['TYPE'] == 'TEST_COMPLETED':
                    #         output_trace = msg_valid['DATA']
                    #         now = datetime.now()
                    #         dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                    #         file = directory + '/data/result' + dt_string + '.json'
                    #         with open(file, 'w') as outfile:
                    #             json.dump(output_trace, outfile, indent=2)
                    #         if not output_trace['destinationReached']:
                    #             logging.info("Not reach the destination")
                    #             with open(directory + '/Incompleted.txt', 'a') as f:
                    #                 json.dump(scenario_msg[i], f, indent=2)
                    #                 f.write('\n')
                    #         if len(output_trace['trace']) > 1:
                    #             encoded_testcase = EncodedTestCase(output_trace, single_spec)
                    #             logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                    #             del encoded_testcase.trace
                    #             if encoded_testcase.fitness < 0.0:
                    #                 with open(directory + '/bugTestCase.txt', 'a') as bug_file:
                    #                     json.dump(output_trace, bug_file, indent=2)
                    #                     bug_file.write('\n')
                    #             population.append(encoded_testcase)
                    #         elif len(output_trace['trace']) == 1:
                    #             logging.info("Is reached: {}, minimal distance: {}".format(output_trace['destinationReached'], output_trace['minEgoObsDist']))
                    #             testcase = TestCaseRandom(output_trace)
                    #             testcase.testcase_random(1)
                    #             new_testcases.append(testcase.cases[-1])
                    #         else:
                    #             logging.info("No trace for the test cases")
                    #             with open(directory + '/NoTrace.txt', 'a') as f:
                    #                 json.dump(scenario_msg[i], f, indent=2)
                    #                 f.write('\n')
                    #             testcase = TestCaseRandom(output_trace)
                    #             testcase.testcase_random(1)
                    #             new_testcases.append(testcase.cases[-1])
                    #         init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                    #         await websocket.send(init_msg)
                    #         break
            # new_population_obj = ga.GAGeneration(population)
            if generation_number:
                if len(population):
                    decoder = DecodedTestCase(population)
                    new_testcases = decoder.decoding()

                if len(new_testcases) < population_size:
                    testcase = TestCaseRandom(output_trace)
                    testcase.testcase_random(population_size - scenario_no)
                    for i2 in range(len(testcase.cases) - 1):
                        new_testcases.append(testcase.cases[i2 + 1])
                with open(directory + '/TestCase.txt', 'w', encoding="utf-8") as outfile:
                    for i1 in range(len(new_testcases)):
                        json.dump(new_testcases[i1], outfile, indent=2)
                        outfile.write('\n')
            # Begin GA
                for generation in range(generation_number-1):
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
                    generation_fitness = float('inf')
                    ave_fitness = 0
                    if len(new_testcases) < population_size:
                        logging.info('Test case decreases')
                    population = []
                    next_new_testcases = []
                    for j in range(len(new_testcases)):
                        # deal with each test case
                        while True:
                            msg = await websocket.recv()
                            msg = json.loads(msg)
                            print(msg['TYPE'])
                            if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                                if msg['DATA']:
                                    logging.info('Running Generation: {}, Individual: {}'.format(generation, j + 1))
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
                                with open(file, 'w', encoding="utf-8") as outfile:
                                    json.dump(output_trace, outfile, indent=2)
                                logging.info("The number of states in the trace is {}".format(len(output_trace['trace'])))
                                if not output_trace['destinationReached']:
                                    with open(directory + '/Incompleted.txt', 'a', encoding="utf-8") as f:
                                        json.dump(new_testcases[j], f, indent=2)
                                        f.write('\n')
                                if len(output_trace['trace']) > 1:
                                    encoded_testcase = EncodedTestCase(output_trace, single_spec)
                                    logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                                    ave_fitness += encoded_testcase.fitness
                                    if encoded_testcase.fitness < generation_fitness:
                                        generation_fitness = encoded_testcase.fitness
                                    del encoded_testcase.trace
                                    if encoded_testcase.fitness < 0.0:
                                        tmp_path = directory
                                        fileList = os.listdir(tmp_path)
                                        tmp_path = tmp_path + '/violation_scenario_' + str(len(fileList)+1) + ".txt"
                                        with open(tmp_path, 'a', encoding="utf-8") as bug_file:
                                            now = datetime.now()
                                            dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                            string_index = "Time:" + dt_string + "Generation: " + str(generation) + ", Individual: " + str(j+1) + '\n'
                                            bug_file.write(string_index)
                                            json.dump(output_trace, bug_file, indent=2)
                                            bug_file.write('\n')
                                        msg_path = directory
                                        fileList = os.listdir(msg_path)
                                        msg_path = msg_path + '/violation_msg_' + str(len(fileList))
                                        with open(msg_path, 'w') as msg_file:
                                            msg_file.write(json.dumps(msg['DATA']))
                                        violation = True
                                    population.append(encoded_testcase)
                                elif len(output_trace['trace']) == 1:
                                    logging.info("Only one state. Is reached: {}, minimal distance: {}".format(output_trace['destinationReached'], output_trace['minEgoObsDist']))
                                    testcase = TestCaseRandom(output_trace)
                                    testcase.testcase_random(1)
                                    next_new_testcases.append(testcase.cases[-1])
                                else:
                                    testcase = TestCaseRandom(output_trace)
                                    testcase.testcase_random(1)
                                    next_new_testcases.append(testcase.cases[-1])
                                    logging.info("No trace for the test cases!")
                                    with open(directory + '/NoTrace.txt', 'a', encoding="utf-8") as f:
                                        now = datetime.now()
                                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                        f.write("Time: Generation: {}, Individual: {}".format(dt_string, generation, j))
                                        json.dump(new_testcases[j], f, indent=2)
                                        f.write('\n')
                                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                                await websocket.send(init_msg)
                                break
                        # logging.info('Running Generation: {}, Individual: {}'.format(generation, j+1))
                        # send_msg = {'CMD': "CMD_NEW_TEST", 'DATA': new_testcases[j]}
                        # await websocket.send(json.dumps(send_msg))
                        # while True:
                        #     msg_valid = await websocket.recv()
                        #     msg_valid = json.loads(msg_valid)
                        #     # print("Received Message: " + msg_valid['TYPE'])
                        #     # if msg_valid['TYPE'] == 'ERROR' or 'TEST_STARTED':
                        #     #     print(msg_valid)
                        #     if msg_valid['TYPE'] == 'TEST_TERMINATED' or msg_valid['TYPE'] == 'ERROR':
                        #         print(msg_valid)
                        #         print("Try to reconnect.")
                        #         time.sleep(3)
                        #         init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                        #         await websocket.send(init_msg)
                        #         msg = await websocket.recv()
                        #         msg = json.loads(msg)
                        #         if msg['TYPE'] == 'READY_FOR_NEW_TEST' and msg['DATA']:
                        #             send_msg = {'CMD': "CMD_NEW_TEST", 'DATA': new_testcases[j]}
                        #             await websocket.send(json.dumps(send_msg))
                        #         continue
                        #     elif msg_valid['TYPE'] == 'TEST_COMPLETED':
                        #         output_trace = msg_valid['DATA']
                        #         now = datetime.now()
                        #         dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                        #         file = directory + '/data/result' + dt_string + '.json'
                        #         with open(file, 'w') as outfile:
                        #             json.dump(output_trace, outfile, indent=2)
                        #         loggGAing.info("The number of states in the trace is {}".format(len(output_trace['trace'])))
                        #         if not output_trace['destinationReached']:
                        #             with open(directory + '/Incompleted.txt', 'a') as f:
                        #                 json.dump(new_testcases[j], f, indent=2)
                        #                 f.write('\n')
                        #         if len(output_trace['trace']) > 1:
                        #             encoded_testcase = EncodedTestCase(output_trace, single_spec)
                        #             logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                        #             ave_fitness += encoded_testcase.fitness
                        #             if encoded_testcase.fitness < generation_fitness:
                        #                 generation_fitness = encoded_testcase.fitness
                        #             del encoded_testcase.trace
                        #             if encoded_testcase.fitness < 0.0:
                        #                 with open(directory + '/bugTestCase.txt', 'a') as bug_file:
                        #                     now = datetime.now()
                        #                     dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                        #                     string_index = "Time:" + dt_string + "Generation: " + str(generation) + ", Individual: " + str(j+1) + '\n'
                        #                     bug_file.write(string_index)
                        #                     json.dump(output_trace, bug_file, indent=2)
                        #                     bug_file.write('\n')
                        #             population.append(encoded_testcase)
                        #         elif len(output_trace['trace']) == 1:
                        #             logging.info("Only one state. Is reached: {}, minimal distance: {}".format(output_trace['destinationReached'], output_trace['minEgoObsDist']))
                        #             testcase = TestCaseRandom(output_trace)
                        #             testcase.testcase_random(1)
                        #             next_new_testcases.append(testcase.cases[-1])
                        #         else:
                        #             testcase = TestCaseRandom(output_trace)
                        #             testcase.testcase_random(1)
                        #             next_new_testcases.append(testcase.cases[-1])
                        #             logging.info("No trace for the test cases!")
                        #             with open(directory + '/NoTrace.txt', 'a') as f:
                        #                 now = datetime.now()
                        #                 dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                        #                 f.write("Time: Generation: {}, Individual: {}".format(dt_string, generation, j))
                        #                 json.dump(new_testcases[j], f, indent=2)
                        #                 f.write('\n')
                        #         break
                    min_fitness_list.append(generation_fitness)
                    ave_fitness_list.append(ave_fitness/population_size)
                    logging.info("The minimal fitness in generation {} is {}.".format(generation, generation_fitness))
                    logging.info("The average fitness in generation {} is {}.".format(generation, ave_fitness/population_size))
                    if len(population):
                        new_population_obj = GAGeneration(population)
                        new_population = new_population_obj.one_generation()                        
                        decoder = DecodedTestCase(new_population)
                        ga_new_testcases = decoder.decoding()
                        next_new_testcases.extend(ga_new_testcases)
                    new_testcases = copy.deepcopy(next_new_testcases)
                    with open(directory + '/TestCase.txt', 'a', encoding="utf-8") as outfile:
                        for i in range(len(new_testcases)):
                            try:
                                json.dump(new_testcases[i], outfile, indent=2)
                                outfile.write('\n')
                            except TypeError:
                                logging.info("Check the types of test cases")
            #  The last generation
                generation += 1
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
                ave_fitness = 0
                generation_fitness = float('inf')
                for j in range(len(new_testcases)):
                    while True:
                        msg = await websocket.recv()
                        msg = json.loads(msg)
                        print(msg['TYPE'])
                        if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                            if msg['DATA']:
                                logging.info('Running Generation: {}, Individual: {}'.format(generation, j + 1))
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
                            logging.info("The number of states in the trace is {}".format(len(output_trace['trace'])))
                            if not output_trace['destinationReached']:
                                with open(directory + '/Incompleted.txt', 'a', encoding="utf-8") as f:
                                    json.dump(new_testcases[j], f, indent=2)
                                    f.write('\n')
                            if len(output_trace['trace']) > 1:
                                encoded_testcase = EncodedTestCase(output_trace, single_spec)
                                output_trace['fitness'] = encoded_testcase.fitness
                                logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                                ave_fitness += encoded_testcase.fitness
                                if encoded_testcase.fitness < generation_fitness:
                                    generation_fitness = encoded_testcase.fitness
                                del encoded_testcase.trace
                                if encoded_testcase.fitness < 0.0:
                                    tmp_path = directory
                                    fileList = os.listdir(tmp_path)
                                    tmp_path = tmp_path + '/violation_scenario_' + str(len(fileList)+1) + ".txt"
                                    with open(tmp_path, 'a', encoding="utf-8") as bug_file:
                                        now = datetime.now()
                                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                        string_index = "Time:" + dt_string + "Generation: " + str(
                                            generation) + ", Individual: " + str(j + 1) + '\n'
                                        bug_file.write(string_index)
                                        json.dump(output_trace, bug_file, indent=2)
                                        bug_file.write('\n')
                                    msg_path = directory
                                    fileList = os.listdir(msg_path)
                                    msg_path = msg_path + '/violation_msg_' + str(len(fileList))
                                    with open(msg_path, 'w') as msg_file:
                                        msg_file.write(json.dumps(msg['DATA']))
                                    violation = True
                                population.append(encoded_testcase)
                            elif len(output_trace['trace']) == 1:
                                logging.info("Only one state. Is reached: {}, minimal distance: {}".format(
                                    output_trace['destinationReached'], output_trace['minEgoObsDist']))
                                testcase = TestCaseRandom(output_trace)
                                testcase.testcase_random(1)
                                next_new_testcases.append(testcase.cases[-1])
                            else:
                                testcase = TestCaseRandom(output_trace)
                                testcase.testcase_random(1)
                                next_new_testcases.append(testcase.cases[-1])
                                logging.info("No trace for the test cases!")
                                with open(directory + '/NoTrace.txt', 'a', encoding="utf-8") as f:
                                    now = datetime.now()
                                    dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                    f.write("Time: Generation: {}, Individual: {}".format(dt_string, generation, j))
                                    json.dump(new_testcases[j], f, indent=2)
                                    f.write('\n')
                            now = datetime.now()
                            dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                            file = directory + '/data/result' + dt_string + '.json'
                            with open(file, 'w', encoding="utf-8") as outfile:
                                json.dump(output_trace, outfile, indent=2)
                            init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                            await websocket.send(init_msg)
                            break
                    # logging.info('Generation: {}, Individual: {}'.format(generation + 1, j+1))
                    # send_msg = {'CMD': "CMD_NEW_TEST", 'DATA': new_testcases[j]}
                    # await websocket.send(json.dumps(send_msg))
                    # while True:
                    #     msg_valid = await websocket.recv()
                    #     msg_valid = json.loads(msg_valid)
                    #     # print("Received Message: " + msg_valid['TYPE'])
                    #     # if msg_valid['TYPE'] == 'ERROR' or 'TEST_STARTED':
                    #     #     print(msg_valid)
                    #     if msg_valid['TYPE'] == 'TEST_TERMINATED' or msg_valid['TYPE'] == 'ERROR':
                    #         print("Try to reconnect!")
                    #         time.sleep(3)
                    #         init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                    #         await websocket.send(init_msg)
                    #         msg = await websocket.recv()
                    #         msg = json.loads(msg)
                    #         if msg['TYPE'] == 'READY_FOR_NEW_TEST' and msg['DATA']:
                    #             send_msg = {'CMD': "CMD_NEW_TEST", 'DATA': new_testcases[j]}
                    #             await websocket.send(json.dumps(send_msg))
                    #         continue
                    #     elif msg_valid['TYPE'] == 'TEST_COMPLETED':
                    #         output_trace = msg_valid['DATA']
                    #         now = datetime.now()
                    #         dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                    #         file = directory + '/data/result' + dt_string + '.json'
                    #         with open(file, 'w') as outfile:
                    #             json.dump(output_trace, outfile, indent=2)
                    #         if not output_trace['destinationReached']:
                    #             with open(directory + '/Incompleted.txt', 'a') as f:
                    #                 json.dump(new_testcases[j], f, indent=2)
                    #                 f.write('\n')
                    #         if len(output_trace['trace']) > 1:
                    #             encoded_testcase = EncodedTestCase(output_trace, single_spec)
                    #             logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                    #             if encoded_testcase.fitness < generation_fitness:
                    #                 generation_fitness = encoded_testcase.fitness
                    #             del encoded_testcase.trace
                    #             ave_fitness += encoded_testcase.fitness
                    #             if encoded_testcase.fitness < 0.0:
                    #                 with open(directory + '/bugTestCase.txt', 'a') as bug_file:
                    #                     string_index = "Generation: " + str(generation + 1) + ", Individual: " + str(j+1) + '\n'
                    #                     bug_file.write(string_index)
                    #                     json.dump(output_trace, bug_file, indent=2)
                    #                     bug_file.write('\n')
                    #         elif len(output_trace['trace']) == 1:
                    #             logging.info("Is reached: {}, minimal distance: {}".format(output_trace['destinationReached'], output_trace['minEgoObsDist']))
                    #         else:
                    #             logging.info("No trace for the test cases!")
                    #             with open(directory + '/NoTrace.txt', 'a') as f:
                    #                 json.dump(new_testcases[j], f, indent=2)
                    #                 f.write('\n')
                    #         break
                min_fitness_list.append(generation_fitness)
                ave_fitness_list.append(ave_fitness/population_size)
                logging.info("The minimal fitness for the last generation is {}.".format(generation_fitness))
                logging.info("The average fitness for the last generation is {}.".format(ave_fitness/population_size))
                if violation:
                    violation_num = len(os.listdir(violation_path))
                    with open(violation_path + "/violation_" + str(violation_num) + ".txt", 'w') as f:
                        f.write(file)
                else:
                    violation_num = len(os.listdir(scenario_path))
                    with open(scenario_path + "/scenario_" + str(violation_num) + ".txt", 'w') as f:
                        f.write(file)
                # logging.info("Minimal fitness: {}".format(min_fitness_list))
                # logging.info("Average fitness: {}".format(ave_fitness_list))


def spec_scenario(file, spec, testcase, generations=0, pop_size=1,file_directory=None):
    loop = asyncio.get_event_loop()
    scenario_specification = copy.deepcopy(spec)
    scenario_testcase = copy.deepcopy(testcase)
    msgs = [scenario_testcase]
    with open(file_directory + '/InitTestCase.txt', 'w', encoding="utf-8") as f:
        json.dump(scenario_testcase, f, indent=2)
    loop.run_until_complete(
        asyncio.gather(hello(file, msgs, scenario_specification, generation_number=generations, population_size=pop_size, directory=file_directory)))


def test_scenario(direct, item):
    file = direct + item
    with open(file, 'r') as f:
        scenario_program = f.read()
    scenario = add_specifications(scenario_program)
    file_name = file.split(".t")
    file = file_name[0] + "_exec.txt"
    with open(file, 'w') as f:
        f.write(scenario)
    log_direct = 'ts/' + Path(item).stem
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
                ego_position = (ego_init_start['position']['x'], ego_init_start['position']['y'], ego_init_start['position']['z']) # ego_run_until_complete
            for spec_index in range(len(specifications_in_scenario)):
                first_specification = specifications_in_scenario[spec_index]
                single_specification = SingleAssertion(first_specification, current_map, ego_position)
                logging.info("\n Evaluate Scenario {} with Assertion {}: {} \n ".format(scenario_name, spec_index,
                                                                                        single_specification.specification))
                spec_scenario(scenario_program, spec=single_specification, testcase=test_case, generations=2, pop_size=2, # 2 2
                              file_directory=log_direct)
        except KeyError:
            spec_scenario(scenario_program, spec={}, testcase=test_case)


class MyHandler2(FileSystemEventHandler):
    def __init__(self, timeout, method_to_execute):
        super().__init__()
        self.timeout = timeout
        self.method_to_execute = method_to_execute
        self.last_change_time = time.time()

    def on_any_event(self, event):
        self.last_change_time = time.time()

    def check_timeout(self):
        if time.time() - self.last_change_time > self.timeout:
            self.method_to_execute()


class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        path1 = "../main/safe_scenario_description"
        path2 = "../main/violation_scenario_description"
        if event.src_path.startswith(path1):
            files = os.listdir(path1)
            folder = path1 + "scenario_folder" + str(len(files))
            folder_files = os.listdir(folder)
            for i in range(4):
                test_scenario(folder+"/", ["scenario_"+str(len(folder_files)-i)+".txt"])
        elif event.src_path.startswith(path2):
            violation_files = os.listdir(path2)
            scenarios = []
            if len(violation_files) == 1:
                with open(path2 + "/violation_" + str(len(violation_files)), "r") as f:
                    scenario = f.read()
                new_scenario = crossover_scenario(scenario)
                scenarios.append(new_scenario)
                files = os.listdir(path1)
                folder = path1 + "scenario_folder" + str(len(files))
                folder_files = os.listdir(folder)
                for i in range(3):
                    with open(folder + "/scenario_" + str(len(folder_files) - i), "r") as f:
                        scenario1 = f.read()
                    new_scenario1, new_scenario2 = crossover_scenarios(scenario, scenario1)
                    scenarios.append(new_scenario1)
            elif len(violation_files) == 2:
                with open(path2 + "/violation_1", "r") as f:
                    scenario1 = f.read()
                with open(path2 + "/violation_2", "r") as f:
                    scenario2 = f.read()
                new_scenario1, new_scenario2 = crossover_scenarios(scenario1, scenario2)
                scenarios.append(new_scenario1)
                scenarios.append(new_scenario2)
                files = os.listdir(path1)
                folder = path1 + "scenario_folder" + str(len(files))
                folder_files = os.listdir(folder)
                with open(folder + "/scenario_" + str(len(folder_files) - i), "r") as f:
                    scenario = f.read()
                new_scenario3, new_scenario4 = crossover_scenarios(random.choices([scenario1, scenario2]), scenario)
                scenarios.append(new_scenario3)
                scenarios.append(new_scenario4)
            else:
                for i in range(3):
                    this_scenarios = []
                    with open(path2 + "/violation_" + str(len(violation_files)-i), "r") as f:
                        scenario = f.read()
                        this_scenarios.append(scenario)
                new_scenario1, new_scenario2 = crossover_scenarios(this_scenarios[0], this_scenarios[1])
                new_scenario3, new_scenario4 = crossover_scenarios(random.choices([this_scenarios[0], this_scenarios[1]]), this_scenarios[2])
                scenarios.append(new_scenario1)
                scenarios.append(new_scenario2)
                scenarios.append(new_scenario3)
                scenarios.append(new_scenario4)
            for each in scenarios:
                violation_files = os.listdir(path2)
                with open(path2 + "/violation_" + str(len(violation_files)+1), "w") as f:
                    f.write(each)


def adp_evolution(num):
    path = "../main/safe_scenario_description"
    files = os.listdir(path)
    folder_to_watch = path + "scenario_folder" + str(len(files))
    path2 = "../main/violation_scenario_description"
    folder_files = os.listdir(folder_to_watch)
    for i in range(num):
        this_file = folder_to_watch + "/" + "scenario_" + str(len(folder_files) - i) + ".txt"
        with open(this_file, "r") as f:
            tmp_file = f.read()
            this_files = tmp_file.split("```")
            for each in this_files:
                if "CreateScenario" in each:
                    content = each
        with open(this_file, 'w') as file:
            file.write(content)
        test_scenario(folder_to_watch + "/", ["scenario_" + str(len(folder_files) - i) + ".txt"])

    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, folder_to_watch, recursive=True)
    observer.schedule(event_handler, path2, recursive=True)

    folder_path_violation = '../main/violation_scenario_description'
    timeout = 600

    event_handler2 = MyHandler2(timeout, feedback_generation())
    observer.schedule(event_handler2, folder_path_violation, recursive=True)

    observer.start()

    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()



