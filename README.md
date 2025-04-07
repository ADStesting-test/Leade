# 基于路网建模的自动驾驶关键场景生成与自适应演化方法

This project contains the implementation of LEADE.

The generation approach requires the following dependencies to run:

	1. SORA-SVL: https://github.com/YuqiHuai/SORA-SVL
	2. Apollo autonomous driving platform: https://github.com/ApolloAuto/apollo
    3. AVUnit: https://avunit.readthedocs.io/en/latest/Introduction_to_AVUnit.html

# Prerequisites

* A 8-core processor and 16GB memory minimum
* Ubuntu 20.04 or later
* Python 3.11 or higher
* NVIDIA graphics card: GeForce RTX 2080 ti
* Docker-CE version 19.03 and above
* NVIDIA Container Toolkit

# Run
Enter Apollo and start dreamview, and then start rc_recorder:

``
bash ./docker/scripts/dev_start.sh
``
``
bash ./docker/scripts/dev_into.sh
``
``
./scripts/bootstrap_lgsvl.sh
``
``
node rc_recorder/index.js
``

Start AVUnit testing platform.

Enter SORA-SVL and starts the simulator:

``
sudo docker compose up --build -d
``

Start SVL simulator and localhost to run API only.

Run src/LEADE_run.py


