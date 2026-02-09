# LLM-EPANET: A Benchmark for Evaluating LLMs on EPANET-Related Tasks

[![Python](https://shields.io/badge/Python-3.10-blue?logo=python&style=for-the-badge)](https://www.python.org/)

## Pre-requisites
- **Python 3.10** - [Download here](https://www.python.org/downloads/)
- **uv package manager** - [Installation guide](https://docs.astral.sh/uv/getting-started/installation/)
- **Docker Desktop (for safe code execution)** - [Download here](https://www.docker.com/products/docker-desktop/)
- **API Keys** - Obtain API keys for OpenRouter and Voyage



## 1. Installation

### 1.1 Automatic (preferred)
<details>
  <summary>Click to expand</summary>

```bash
git clone git@github.com:yinon-gold/LLMs-in-WDS-Modeling.git
cd LLMs-in-WDS-Modeling
./scripts/install.sh
```
</details>

### 1.2 Manual
<details>
  <summary>Click to expand</summary>

```bash
# cloning the repository

git clone git@github.com:yinon-gold/LLMs-in-WDS-Modeling.git  # ssh
# git clone https://github.com/yinon-gold/LLMs-in-WDS-Modeling.git  # https


# cloning and copying EPyT documentation

git clone git@github.com:OpenWaterAnalytics/EPyT.git  # ssh
# git clone https://github.com/OpenWaterAnalytics/EPyT.git  # https
cp EPyT/epyt/epanet.py LLMs-in-WDS-Modeling/data/epyt_documentation.py
rm -rf EPyT


# installing dependencies and setting up the environment
cd LLMs-in-WDS-Modeling
uv sync
source .venv/bin/activate


```
</details>

## 2. Fill environment variables
```bash
# create .env file in the root directory and add the following lines with your API keys, according to .env.example
OPENROUTER_API_KEY=your_openrouter_api_key_here
VOYAGE_API_KEY=your_voyage_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## 3. Creating the vector store from EPyT documentation
```bash
uv run scripts/clean_epyt_docs.py
uv run scripts/create_faiss_store.py --embedding_model openai  # possible embedding providers are: openai, voyage, nvidia 
```

**All configured! ready to go!**


## Running tests
> **All test results are saved in the `results` directory.**
>
> **All logs are saved in the `logs` directory.**

### Retrieval tests
> **All retrieval results are saved in the `results/retrieval` directory.**
```bash
uv run tests/retriever_tests.py --networks <NETWORKS> --alpha_sweep --num_threads <NUM_THREADS>
```
Will run a retrieval tests with several alpha values for Hybrid Retrieval (combination of semantic and keyword retrieval)

Example:
```bash
uv run tests/retriever_tests.py --networks net1 net3 l_town --alpha_sweep --num_threads 4
```
runs tests on net1, net3, and l_town networks with 4 concurrent threads.

```bash
uv run tests/retriever_tests.py --networks all --alpha_sweep --num_threads 10
```
runs on all networks: net1, net3, L_TOWN, PA2 with 10 concurrent threads.


### LLM-Agent tests
> **All agent results are saved in the `results/agent` directory.**
```bash
# usage:
uv run tests/query_tests.py --network <NETWORKS> --prompt <PROMPT_TYPE> --num_retries <NUM_EXECUTION_RETRIES> --large_model <MODEL_NAME> --small_model <MODEL_NAME> -k <K_VALUE> -t 0.7 --num_threads <NUM_THREADS> --sandbox
```

`--network`: list, can have any of: {net1, net3, l_town, pa2}, use `all` to run on all networks

`--prompt`: either `basic`, `simple` or `complex`. Recommended to use `complex` for less errors.

`--num_retries`: number of times to retry executing the code in case of errors. Recommended > 3.

`--large_model`: name of the model to use for function block generation and review. Can be any model supported by OpenRouter. Recommended to use a strong model. Recommended `openai/o3-mini-high` or `qwen/qwen2.5-vl-72b-instruct`.

`--small_model`: name of the model to use for one-liner evaluation generation. Can be any model supported by OpenRouter. Recommended to use a smaller, cost-effective model. Recommended `qwen/qwen-2.5-coder-32b-instruct`.

`-k`: number of retrieved documents to use as context for the LLM. Recommended > 5.

`--num_threads`: number of concurrent threads to run. Recommended > 4. Takes ~30 mins to run on all 69 queries with 10 threads.

`--sandbox`: whether to run the code execution in [LLMSandbox](https://github.com/vndee/llm-sandbox). Extremely recommended to use for safe execution, and for multi-threaded execution as functions can interfere with the network state. If not used, code will be executed directly on the host machine using `execv`.

Example:
```bash
uv run tests/query_tests.py --network pa --prompt complex --num_retries 5 --large_model qwen/qwen2.5-vl-72b-instruct --small_model qwen/qwen-2.5-coder-32b-instruct -k 5 -t 0.7 --num_threads 10 --sandbox
```

## Citation
If you use this repository for your research, please consider citing:
```bibtex
@misc{goldshtein2025largelanguagemodelswater,
      title={Large Language Models for Water Distribution Systems Modeling and Decision-Making}, 
      author={Yinon Goldshtein and Gal Perelman and Assaf Schuster and Avi Ostfeld},
      year={2025},
      eprint={2503.16191},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2503.16191}, 
}
```