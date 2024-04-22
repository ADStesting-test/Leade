import copy
import math
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

import numpy as np
import websockets
import json
import asyncio
from EXtraction import ExtractAll
from GeneticAlgorithm_hxs import GAGeneration, EncodedTestCase, DecodedTestCase
from TestCaseRandom import TestCaseRandom
from datetime import datetime
from AssertionExtraction import SingleAssertion
from map import get_map_info
from monitor import Monitor
import logging
from spec_coverage import failure_statement

# logging.basicConfig(level=level, handlers=[stdout_handler, file_handler],format='%(asctime)s, %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.FileHandler('test.log', 'a'))
# logger.addHandler(logging.StreamHandler(sys.stdout))




def newlist(parent_list, list1):
    new_element = [element for element in list1 if element not in parent_list]
    return new_element



def to_json(obj):
    return json.dumps(obj, default=lambda o: o.__dict__, indent=4)

def fitness_vector(local_vector, global_vector):
    assert len(local_vector)==len(global_vector)
    n=len(local_vector)
    z=[local_vector[i] if global_vector[i]>0 else global_vector[i] for i in range(n)]
    return z

def selection(population, fitness_matrix, number):
    n = len(population)
    new_population = []
    fitness = [min([j for j in fitness_matrix[i] if j > 0]) for i in range(n)]
    sorted_index = sorted(range(len(fitness)), key=lambda kk: fitness[kk])
    for k in range(number):
        first_int = random.sample(range(0, math.ceil(n / 2)), 1)[0]
        second_int = random.sample(range(0, n), 1)[0]
        if first_int <= second_int:
            population_index = sorted_index[first_int]
        else:
            population_index = sorted_index[second_int]
        new_population.append(population[population_index])
    return new_population





async def hello(scenario_msg, single_spec, generation_number=1, population_size=3, directory=None) -> object:
    spec_str = single_spec.translated_statement
    negative_predicate_obj = failure_statement(spec_str)
    all_predicates = negative_predicate_obj.neg_predicate()  # string list
    logging.info("The set of negative predicates: {}".format(all_predicates))
    global_fitness = np.full(len(all_predicates), np.inf)
    all_covered_predicates = set()

    uri = "ws://localhost:6666"
    async with websockets.connect(uri, max_size=None) as websocket:
        while True:
            prediction_msg = json.dumps({'CMD': "CMD_RESTART_PREDICTION_MODULE"})
            await websocket.send(prediction_msg)
            msg = await websocket.recv()
            msg = json.loads(msg)
            if msg['TYPE'] == 'PREDICTION_MODULE_STARTED':
                break
        # while True:
        #     init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
        #     await websocket.send(init_msg)
        #     msg = await websocket.recv()
        #     msg = json.loads(msg)
        #     print("Not Ready: {}".format(msg))
        #     if msg['TYPE'] == 'READY_FOR_NEW_TEST' and msg['DATA']:
        #         break
        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
        await websocket.send(init_msg)
        msg = await websocket.recv()
        msg = json.loads(msg)
        print(msg)
        if msg['TYPE'] == 'READY_FOR_NEW_TEST' and msg['DATA']:
            now = datetime.now()
            dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
            with open(directory + '/Incompleted.txt', 'a') as f:
                f.write('Time: {} \n'.format(dt_string))
            with open(directory + '/bugTestCase.txt', 'a') as f:
                f.write('Time: {} \n'.format(dt_string))
            with open(directory + '/NoTrace.txt', 'a') as f:
                f.write('Time: {} \n'.format(dt_string))
            init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
            await websocket.send(init_msg)
            if len(scenario_msg) < population_size:
                test_case = scenario_msg[0]
                testcase = TestCaseRandom(test_case)
                testcase.testcase_random(population_size - len(scenario_msg))
                for i2 in range(len(testcase.cases) - 1):
                    scenario_msg.append(testcase.cases[i2 + 1])
            population = []
            temp_population = []
            new_testcases = []
            covered_predicates = []
            generation_fitness_matrix = []
            for i in range(population_size):
                while True:
                    msg = await websocket.recv()
                    msg = json.loads(msg)
                    if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                        if msg['DATA']:
                            logging.info('Running Generation: 0, Individual: {}'.format(i + 1))
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
                            # if encoded_testcase.fitness < 0.0:
                            cover_monitor = Monitor(output_trace, single_spec)
                            coverage_rate, coverage_statement, _, local_fitness_vector = cover_monitor.coverage_monitor()
                            logging.info("Fitness: {}".format(local_fitness_vector))
                            logging.info("Coverage rate is: {}/{}, Covered Predicates are: {}".format(len(coverage_statement), len(all_predicates), coverage_statement))

                            global_fitness = np.minimum(global_fitness, local_fitness_vector)
                            del encoded_testcase.trace
                            # new_predicate = newlist(covered_predicates, coverage_statement)
                            new_predicate = set(coverage_statement).difference(all_covered_predicates)
                            if len(new_predicate):
                                # covered_predicates = covered_predicates + new_predicate
                                all_covered_predicates = all_covered_predicates.union(new_predicate)
                                population.append(encoded_testcase)
                                with open(directory + '/improvedTestCase.txt', 'a') as bug_file:
                                    now = datetime.now()
                                    dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                    string_index = "Time:" + dt_string + '\n'
                                    bug_file.write(string_index)
                                    json.dump(output_trace, bug_file, indent=2)
                                    bug_file.write('\n')
                            else:
                                temp_population.append(encoded_testcase)
                                uncovered_fitness_vector = fitness_vector(local_fitness_vector, global_fitness)
                                generation_fitness_matrix.append(uncovered_fitness_vector)

                            # else:
                            #     logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                        elif len(output_trace['trace']) == 1:
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
            # coverage_rate = len(covered_predicates) / len(all_predicates)
            # logging.info("total coverage rate: {}/{} = {}, covered predicates: {}\n".format(len(covered_predicates), len(all_predicates), coverage_rate, covered_predicates))
            # all_covered_predicates = all_covered_predicates.union(set(covered_predicates))
            logging.info("Current global fitness: {}, coverage rate: {}/{}".format(global_fitness, len(all_covered_predicates), len(all_predicates)))
            if generation_number:
                if len(population) < population_size:
                    remaining_number = population_size - len(population)
                    remaining_population = selection(temp_population, generation_fitness_matrix, remaining_number)
                    population += remaining_population
                new_population_obj = GAGeneration(population)
                new_population = new_population_obj.coverage_one_generation(population)
                decoder = DecodedTestCase(new_population)
                new_testcases = decoder.decoding()
                # if len(new_testcases) < population_size:
                #     if improved_trace is None:
                #         improved_trace = output_trace
                #     testcase = TestCaseRandom(improved_trace)
                #     testcase.testcase_random(population_size - len(new_testcases))
                #     for i2 in range(len(testcase.cases) - 1):
                #         new_testcases.append(testcase.cases[i2 + 1])
                with open(directory + '/TestCase.txt', 'w') as outfile:
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
                    temp_population = []
                    generation_fitness_matrix = []
                    population = []
                    next_new_testcases = []
                    if len(new_testcases) < population_size:
                        print('checking the number of test cases')
                    print("number of individuals: {}".format(len(new_testcases)))
                    for j in range(len(new_testcases)):
                        # deal with each test case
                        while True:
                            msg = await websocket.recv()
                            msg = json.loads(msg)
                            print(msg['TYPE'])
                            if msg['TYPE'] == 'READY_FOR_NEW_TEST':
                                if msg['DATA']:
                                    logging.info('Running Generation: {}, Individual: {}'.format(generation + 1, j + 1))
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
                                logging.info(
                                    "The number of states in the trace is {}".format(len(output_trace['trace'])))
                                if not output_trace['destinationReached']:
                                    with open(directory + '/Incompleted.txt', 'a') as f:
                                        json.dump(new_testcases[j], f, indent=2)
                                        f.write('\n')
                                if len(output_trace['trace']) > 1:
                                    encoded_testcase = EncodedTestCase(output_trace, single_spec)
                                    # if encoded_testcase.fitness < 0.0:
                                    cover_monitor = Monitor(output_trace, single_spec)
                                    coverage_rate, coverage_statement, _, local_fitness_vector = cover_monitor.coverage_monitor()
                                    logging.info("Local fitness: {}".format(local_fitness_vector))
                                    logging.info("Coverage rate is: {}/{}, Covered Predicates are: {}".format(
                                        len(coverage_statement), len(all_predicates), coverage_statement))
                                    global_fitness = np.minimum(global_fitness, local_fitness_vector)
                                    del encoded_testcase.trace
                                    # new_predicate = newlist(covered_predicates, coverage_statement)
                                    new_predicate = set(coverage_statement).difference(all_covered_predicates)
                                    if len(new_predicate):
                                        # covered_predicates = covered_predicates + new_predicate
                                        all_covered_predicates = all_covered_predicates.union(new_predicate)
                                        population.append(encoded_testcase)
                                        with open(directory + '/improvedTestCase.txt', 'a') as bug_file:
                                            now = datetime.now()
                                            dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                            string_index = "Time:" + dt_string + "Generation: " + str(
                                                generation + 1) + ", Individual: " + str(j + 1) + '\n'
                                            bug_file.write(string_index)
                                            json.dump(output_trace, bug_file, indent=2)
                                            bug_file.write('\n')
                                    else:
                                        temp_population.append(encoded_testcase)
                                        uncovered_fitness_vector = fitness_vector(local_fitness_vector, global_fitness)
                                        generation_fitness_matrix.append(uncovered_fitness_vector)
                                        # generation_fitness_matrix.append(local_fitness_vector)
                                    # else:
                                    #     logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                                elif len(output_trace['trace']) == 1:
                                    logging.info("Only one state. Is reached: {}, minimal distance: {}".format(
                                        output_trace['destinationReached'], output_trace['minEgoObsDist']))
                                    # testcase = TestCaseRandom(output_trace)
                                    # testcase.testcase_random(1)
                                    # next_new_testcases.append(testcase.cases[-1])
                                else:
                                    # testcase = TestCaseRandom(output_trace)
                                    # testcase.testcase_random(1)
                                    # next_new_testcases.append(testcase.cases[-1])
                                    logging.info("No trace for the test cases!")
                                    with open(directory + '/NoTrace.txt', 'a') as f:
                                        now = datetime.now()
                                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                        f.write("Time: Generation: {}, Individual: {}".format(dt_string, generation + 1, j))
                                        json.dump(new_testcases[j], f, indent=2)
                                        f.write('\n')
                                init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                                await websocket.send(init_msg)
                                break
                    # coverage_rate = len(covered_predicates) / len(all_predicates)
                    # logging.info("total coverage rate: {}/{} = {}, covered predicates: {}\n".format(len(covered_predicates), len(all_predicates), coverage_rate, covered_predicates))
                    # all_covered_predicates = all_covered_predicates.union(set(covered_predicates))
                    logging.info("Current global fitness: {}, coverage rate: {}/{}".format(global_fitness,
                                                                                           len(all_covered_predicates),
                                                                                           len(all_predicates)))
                    if len(population) < population_size:
                        remaining_number = population_size - len(population)
                        remaining_population = selection(temp_population, generation_fitness_matrix, remaining_number)
                        population += remaining_population
                    new_population_obj = GAGeneration(population)
                    new_population = new_population_obj.coverage_one_generation(population)
                    decoder = DecodedTestCase(new_population)
                    ga_new_testcases = decoder.decoding()
                    next_new_testcases.extend(ga_new_testcases)
                    new_testcases = copy.deepcopy(next_new_testcases)
                    with open(directory + '/TestCase.txt', 'a') as outfile:
                        for i in range(len(new_testcases)):
                            try:
                                json.dump(new_testcases[i], outfile, indent=2)
                                outfile.write('\n')
                            except TypeError:
                                logging.info("Check the types of test cases")
                #  The last generation
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
                generation += 2
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
                                # if encoded_testcase.fitness < 0.0:
                                cover_monitor = Monitor(output_trace, single_spec)
                                coverage_rate, coverage_statement, _, local_fitness_vector = cover_monitor.coverage_monitor()
                                logging.info("Coverage rate is: {}/{}, Covered Predicates are: {}".format(
                                    len(coverage_statement), len(all_predicates), coverage_statement))
                                global_fitness = np.minimum(global_fitness, local_fitness_vector)
                                del encoded_testcase.trace
                                new_predicate = set(coverage_statement).difference(all_covered_predicates)
                                if len(new_predicate):
                                    all_covered_predicates = all_covered_predicates.union(new_predicate)
                                    with open(directory + '/improvedTestCase.txt', 'a') as bug_file:
                                        now = datetime.now()
                                        dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
                                        string_index = "Time:" + dt_string + "Generation: " + str(
                                            generation) + ", Individual: " + str(j + 1) + '\n'
                                        bug_file.write(string_index)
                                        json.dump(output_trace, bug_file, indent=2)
                                        bug_file.write('\n')
                                # else:
                                #     logging.info("      Fitness Value: {}".format(encoded_testcase.fitness))
                            elif len(output_trace['trace']) == 1:
                                logging.info("Only one state. Is reached: {}, minimal distance: {}".format(
                                    output_trace['destinationReached'], output_trace['minEgoObsDist']))
                                # testcase = TestCaseRandom(output_trace)
                                # testcase.testcase_random(1)
                                # next_new_testcases.append(testcase.cases[-1])
                            else:
                                # testcase = TestCaseRandom(output_trace)
                                # testcase.testcase_random(1)
                                # next_new_testcases.append(testcase.cases[-1])
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
                # coverage_rate = len(covered_predicates) / len(all_predicates)
                # logging.info("total coverage rate: {}/{} = {}, covered predicates: {}\n".format(len(covered_predicates), len(all_predicates), coverage_rate, covered_predicates))
                # all_covered_predicates = all_covered_predicates.union(set(covered_predicates))
                logging.info("Global Fitness: {}".format(global_fitness))
                logging.info("Final coverage rate: {}/{}".format(len(all_covered_predicates), len(all_predicates)))
                logging.info("Covered Predicates: {}".format(all_covered_predicates))


def spec_scenario(spec, testcase, generations=0, pop_size=1, file_directory=None):
    loop = asyncio.get_event_loop()
    scenario_specification = copy.deepcopy(spec)
    msgs = copy.deepcopy(testcase)
    loop.run_until_complete(
        asyncio.gather(hello(msgs, scenario_specification, generation_number=generations, population_size=pop_size,
                             directory=file_directory)))

def read_bug_testcase(bug_file):
    with open(bug_file) as f:
        lines = f.readlines()
        time_index = [index for index, s in enumerate(lines) if "Time" in s]
        testcases = []
        for i in range(1, len(time_index)-1):
            case_str = ''
            for j in range(time_index[i]+1, time_index[i+1]):
                case_str += lines[j]
            case = json.loads(case_str)
            del case['testFailures']
            del case['testResult']
            del case['timeOfDay']
            del case['destinationReached']
            del case['minEgoObsDist']
            del case['nearestGtObs']
            del case['completed']
            del case['groundTruthPerception']
            del case['recordingPath']
            testcases.append(case)
        case_str = ''
        for j in range(time_index[-1] + 1, len(lines)):
            case_str += lines[j]
        case = json.loads(case_str)
        del case['testFailures']
        del case['testResult']
        del case['timeOfDay']
        del case['destinationReached']
        del case['minEgoObsDist']
        del case['nearestGtObs']
        del case['completed']
        del case['groundTruthPerception']
        del case['recordingPath']
        testcases.append(case)
        return testcases



def test_scenario(direct, item):
    file = direct + item
    bug_file = 'test_cases/bugTestCase.txt'
    bug_cases = read_bug_testcase(bug_file)

    log_direct ='coverage/' + Path(item).stem
    if not os.path.exists(log_direct):
        os.makedirs(log_direct)
    else:
        shutil.rmtree(log_direct)

    if not os.path.exists(log_direct + '/data'):
        os.makedirs(log_direct + '/data')

    logging_file = log_direct + '/test.log'
    file_handler = logging.FileHandler(logging_file, mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    logging.basicConfig(level=logging.INFO, handlers=[stdout_handler, file_handler],
                        format='%(asctime)s, %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    logging.info("Current Test Case: {}".format(item))
    isGroundTruth = True
    extracted_data = ExtractAll(file, isGroundTruth)
    origin_case = extracted_data.Get_TestCastINJsonList()
    all_specifications = extracted_data.Get_Specifications()
    maps = extracted_data.Get_AllMaps()

    for i in range(len(origin_case)):
        test_case = origin_case[i]
        scenario_name = test_case['ScenarioName']
        logging.info("Current scenario is {}.\n".format(scenario_name))
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
                spec_scenario(spec=single_specification, testcase=origin_case, generations=25, pop_size=20,
                              file_directory=log_direct)
        except KeyError:
            spec_scenario(spec={}, testcase=test_case)


if __name__ == "__main__":
    direct = 'test_cases/final/'
    arr = os.listdir(direct)
    arr = sorted(arr)
    # arr = ['intersection5.txt']
    # arr = ['change02.txt', 'change03.txt', 'change04.txt', 'change11.txt', 'change12.txt', 'change13.txt']
    # arr = ['intersection1.txt', 'intersection2.txt']
    # arr = ['intersection3.txt', 'intersection4.txt']
    # arr = ['intersection5.txt', 'overtaking1.txt']
    # arr = ['intersection1.txt', 'intersection2.txt', 'intersection3.txt', 'intersection4.txt', 'intersection5.txt', 'overtaking1.txt', 'lanechange1.txt', 'lanechange3.txt']
    arr = ['test.txt']
    for item in arr:
        test_scenario(direct, item)
