# Load testing tool for experiments 

This repository is a collection of tools and commands for configuring experiments and running load tests. Use this repository as a template to configure load testing for your own experiments. This doc will take you through the organization of this repository, usage, and the steps to configure and run load tests for your own experiments. 

This repository uses [K6](https://k6.io/) and [Nginx](https://www.nginx.com/) to run load tests. But you can configure this repository to use any other web server. The commands are written in a way that you can easily replace Nginx with any other web server. 

## Getting started 

In this section we will go through the steps to configure and run the load tests with K6 and a Nginx web server. 

1. Clone this repository

```bash
git clone --recurse-submodules https://github.com/gwcloudlab/exp-load-test.git
```

2. Create a cloudlab experiment, or any other setup with two nodes connected by a link. Here we are using [CloudLab](https://www.cloudlab.us/) to create a simple experiment with two nodes using the CloudLab profile [ub-2-node](https://www.cloudlab.us/p/d5c0176c154f497f53637e59a6173e04569a6452). This creates a simple experiment with two Ubuntu 22.04 nodes connected by a link. If you are using any other setup, the commands in this repository can be easily adapter to your setup, provided you have configured both the load generator and the web server to use the same ssh key. 

3. Setup the cloudlab configurations. This step helps you configure the repository to use with cloudlab and your own setup. The tools in the `setup/cloudlab-tools` directory provide you with a range of commands to help you in your experiments. 

```bash
make cl-setup
``` 

This command will create a `.cloudlab` directory. This directory contains the configuration files used by the cloudlab tools. Configure the following parameters in the `.cloudlab/config` file.

- SSH_KEY_PATH : The absolute path to the ssh key used to connect to the nodes.
- CLOUDLAB_USERNAME : Ths username to use with your cloudlab account, or the username for your custom servers. 
- NODE_0 : The IP address of the load generator node. This node will generate the load for the web server.
- NODE_1 : The IP address of the web server node. This node will host the web server.

4. Setup the platform. Run the following command to setup the platform. This command will install the necessary tools on the nodes and configure them. 

```bash
make setup-platform
```

5. Configure the experiment. Add your experiment configurations to the `experiments.json` file. A sample configuration looks like this: 

```json
[
    {
        "name": "exp-1",
        "description": "This is the first experiment. With 100 worker connections.",
        "config": {
            "loadgen": {
                "runcfg": "configs/k6/default/script.js",
                "parameters": []
            },
            "server": {
                "WORKER_CONNECTIONS": 100
            }
        },
        "tags": [
            "variable worker connections"
        ]
    },
]
```

Let's break down the configuration: 

- `name`: The name of the experiment. This is a unique identifier for the experiment. The experiment will be addressed through this name throughout your experimentation phase. 

- `description`: A brief description of the experiment. 

- `config`: The configurations for the load generator and the web server. 

    - `loadgen`: The configurations for the load generator. 

        - `runcfg`: The path to the k6 script file. This file contains the k6 script that generates the load. 

        - `parameters`: The additional parameters to pass to the k6 run command. 

    - `server`: The configurations for the web server. 

        - `WORKER_CONNECTIONS`: The number of worker connections to configure for the web server. This is a Nginx-specific configuration, you can add your own configurations for the server of your choice. 

- `tags`: A list of tags to categorize the experiments.


6. Run the experiment. Run the following command to run the experiment. 

```bash
make run-exp EXP_NAME=exp-1
```

7. Once the experiment is complete, run the following command to copy the experiment results to your local machine. 

```bash
make copy-exp-data EXP_NAME=exp-1
```


After this, you will have a directory created with the name `experiments/exp-1` in the root of this repository. This directory contains the following: 

- `config`: which contains a copy of configurations for the load generator and web server
    - `loadgen`: contains the configurations for the load generator, including the k6 script and any additional parameters passed to the k6 run command. 
    - `server`: contains the configurations for the web server. 
- `metrics`: contains the metrics collected during the experiment.
    - `loadgen`: this directory contains the metrics of the load generator.
        - `out.txt`: this is the output of the k6 run command. 
        - `results.csv`: this csv contains the benchmarks of the load generator and metrics from the K6. 
    - `server`: this directory contains the metrics of the web server.
        - `results.csv`: this csv contains the benchmark of the web server throughout the duration of the experiment. 

You can use these metrics to analyze the performance of teh web server throughout the duration of the experiment. 


## Organization of this repository

This repository is organized as follows: 

```shell
.
├── .cloudlab
├── configs
│   ├── k6
│   └── server
├── examples
│   └── k6
│       ├── k6_resp
│       │   └── output
│       ├── open-model
│       └── testing-types
├── experiments
│   └── exp-1
│       ├── config
│       │   ├── loadgen
│       │   └── server
│       └── metrics
│           ├── loadgen
│           └── server
├── loadgen
├── scripts
├── server
└── setup
│   └── cloudlab-tools
├── experiments.json
├── install.sh
├── LICENSE
├── Makefile
├── README.md
└── requirements.txt
```

- `.cloudlab`: This directory is created when you run the `make cl-setup` command. This directory contains the cloudlab configurations. This directory is excluded from the git version controlling.
- `configs`: This directory contains the configurations for both the server and the load generator. 
    - `k6`: This directory contains the k6 script files. 
    - `server`: This directory contains the configurations for the web server.
- `examples`: This directory contains examples of k6 scripts.
- `experiments`: This directory contains the results of the experiments. This directory is excluded from the git version controlling. 
- `loadgen`: This directory contains the benchmarking scripts for the load generator. 
- `scripts`: This directory contains the shell scripts to perform the experiments.
- `server`: This directory contains the configuration and benchmarking scripts for the server.
- `setup`: This directory contains the setup scripts, including the cloudlab-tools submodule. 
- `experiments.json`: This flie contains all hte experiments you would wish to perform. You can add experiment metadata here and use the make targets to perform the experiments.
- `install.sh`: This script contains the installation scripts, useful for setting up the server. 
- `Makefile`: This file contains a collection of make targets useful for setting up and running the experiments. 
- `requirements.txt`: This file contains the python requirements useful for plotting the results. 



