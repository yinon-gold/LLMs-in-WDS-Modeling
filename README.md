# Large Language Models for Water Distribution Systems Modeling and Decision-Making

[![Python](https://shields.io/badge/Python-3.10-blue?logo=python&style=for-the-badge)](https://www.python.org/)

## Pre-requisites
- **Python 3.10** - [Download here](https://www.python.org/downloads/)
- **uv package manager** - [Installation guide](https://docs.astral.sh/uv/getting-started/installation/)
- **Docker Desktop (for safe code execution)** - [Download here](https://www.docker.com/products/docker-desktop/)
- **API Keys** - Obtain API keys for OpenRouter and Voyage



## Installation

### Automatic (preferred)
<details>
  <summary>Click to expand</summary>

1. Clone the repository:
```bash
git clone git@github.com:yinon-gold/LLMs-in-WDS-Modeling.git
cd LLMs-in-WDS-Modeling
```

2. Run the installation script:
```bash
./scripts/install.sh
```

</details>

### Manual
<details>
  <summary>Click to expand</summary>

1. Clone the repository:
```bash
git clone git@github.com:yinon-gold/LLMs-in-WDS-Modeling.git  # ssh
# git clone https://github.com/yinon-gold/LLMs-in-WDS-Modeling.git  # https
```

2. Clone and copy EPyT documentation:
```bash
git clone git@github.com:OpenWaterAnalytics/EPyT.git  # ssh
# git clone https://github.com/OpenWaterAnalytics/EPyT.git  # https
cp EPyT/epyt/epanet.py LLMs-in-WDS-Modeling/data/epyt_documentation.py
rm -rf EPyT
```

3. Install dependencies and set up the environment:
```bash
# installing dependencies and setting up the environment
cd LLMs-in-WDS-Modeling
uv sync
source .venv/bin/activate
```
</details>

## Configuration

### Filling environment variables

In the project root, copy the example environment file:
```bash
cp .env.example .env
```

Then, open the `.env` file and fill in your API keys:
```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
VOYAGE_API_KEY=your_voyage_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Creating the vector store from EPyT documentation
```bash
uv run scripts/clean_epyt_docs.py
uv run scripts/create_faiss_store.py --embedding_model <provider_name>
```

Replace `<provider_name>` with your preferred embedding providers. 
Supported values are: `openai`, `voyage`, `nvidia`. 

**All configured! ready to go!**


## Retrieval Tests
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


## LLM-Agent Tests

### Usage:
```bash
uv run tests/query_tests.py \
  --network <NETWORKS> \
  --prompt <PROMPT_TYPE> \
  --num_retries <NUM_EXECUTION_RETRIES> \
  --large_model <MODEL_NAME> \
  --small_model <MODEL_NAME> \
  -k <K_VALUE> \
  -t 0.7 \
  --num_threads <NUM_THREADS> \
  --sandbox
```

### LLM Agent Test Parameters:

| Parameter | Description | Default Value |
| --------- | ----------- | ---------------- |
| `--network` | List of networks to run tests on. Use `all` to run on all networks. For example: `--network net1 l_town` will run tests on net1 and l_town networks. | - |
| `--prompt` | Type of prompt to use for the LLM agent. Can be `basic`, `simple`, or `complex`. | `complex` |
| `--num_retries` | Number of times to retry executing the code in case of errors. Recommended > 3. | `5` |
| `--large_model` | Name of the model to use for function block generation and review. Can be any model supported by OpenRouter. Recommended to use a strong model. Recommended `openai/o3-mini-high` or `qwen/qwen2.5-vl-72b-instruct`. | `openai/gpt-4.1-mini` |
| `--small_model` | Name of the model to use for one-liner evaluation generation. Can be any model supported by OpenRouter. Recommended to use a smaller, cost-effective model. Recommended `qwen/qwen-2.5-coder-32b-instruct`. | `qwen/qwen-2.5-coder-32b-instruct` |
| `--num_retries` | Number of times to retry executing the code in case of errors. Recommended > 3. | `5` |
| `-k` | Number of retrieved documents to use as context for the LLM. Recommended > 5. | `5` |
| `-t` | Temperature to use for the LLM. Recommended 0.7 for a good balance between creativity and coherence. | `0.7` |
| `--num_threads` | Number of concurrent threads to run. Recommended > 4. Takes ~30 mins to run on all 69 queries with 10 threads. | `1` |
| `--sandbox` | Whether to run the code execution in [LLMSandbox](https://github.com/vndee/llm-sandbox). Extremely recommended to use for safe execution, and for multi-threaded execution as functions can interfere with the network state. If not used, code will be executed directly on the host machine using `execv`. | `True` |


### Example usage:
```bash
uv run tests/query_tests.py --network pa --prompt complex --num_retries 5 --large_model qwen/qwen2.5-vl-72b-instruct --small_model qwen/qwen-2.5-coder-32b-instruct -k 5 -t 0.7 --num_threads 10 --sandbox
```

## Results

* All results are saved in the `results` directory.
* Retrieval test results are saved in `results/retrieval` directory.
* LLM agent test results are saved in `results/agent` directory.
* All logs are saved in the `logs` directory.

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