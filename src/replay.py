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
from GeneticAlgorithm import GAGeneration, EncodedTestCase, DecodedTestCase
from TestCaseRandom import TestCaseRandom
from datetime import datetime
from AssertionExtraction import SingleAssertion
from map import get_map_info

import logging

async def replay(scenario_msg) -> object:
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
                        init_msg = json.dumps({'CMD': "CMD_READY_FOR_NEW_TEST"})
                        await websocket.send(init_msg)
                        break


def replay_violation(path):
    with open(path, "r") as file:
        msg = file.read()
    # msg = [msg]
    msg = [json.loads(msg)]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(replay(msg)))



if __name__ == "__main__":
    path = "ts/1.3/violation_msg_10"
    replay_violation(path)



