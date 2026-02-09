import argparse
import os
import pandas as pd
from tqdm import tqdm
import logging
import sys
import numpy as np
import datetime as dt
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# logging.basicConfig(
#     format='%(levelname)s: %(asctime)s %(message)s',
#     datefmt='%m/%d/%Y %H:%M:%S',
#     filename='logs/llm_epanet.log'
# )

# logger = logging.getLogger("llm-epanet")
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler(sys.stdout))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env', override=True)

from llm_epanet.models.retriever import SemanticRetriever
from llm_epanet.models.llm import LanguageModel
from llm_epanet.utils.prompts import get_prompt
from llm_epanet.models.agent import EPANETAgent
from llm_epanet.utils.logger import logger
from llm_epanet.utils.utils import get_project_root, get_results_dir
# from llm_epanet.utils.settings import LARGE_MODEL, SMALL_MODEL
from llm_epanet.data.queries import get_queries


def process_single_query(agent: EPANETAgent, query: dict, prompt: str,
                         exec_prompt: str, except_prompt: str,
                         code_review_prompt: str, k: int, num_retries: int,
                         general_prompt: str) -> dict:
    """Process a single query and return result row"""
    head, tail = os.path.split(query["network"])
    try:
        result = agent(
            query["prompt"],
            prompt=prompt,
            k=k,
            args=query["args"],
            exec_script=True,
            code_exec_prompt=exec_prompt,
            code_fix_prompt=except_prompt,
            code_review_prompt=code_review_prompt,
            epanet_network=query["network"]
        )

        if is_number(result.query_result) and is_number(query['expected']):
            try:
                is_equal = np.isclose(float(query['expected']), float(result.query_result), rtol=0.05)
            except Exception as e:
                logger.error(f"Error in numeric comparison: {str(e)}")
                is_equal = False
        else:
            try:
                is_equal = result.query_result == query['expected']
            except Exception as e:
                logger.error(f"Error comparing results: {str(e)}")
                try:
                    is_equal = str(result.query_result) == str(query['expected'])
                except Exception as e:
                    logger.error(f"String comparison also failed: {str(e)}")
                    is_equal = False
        
        return {
            'id': query['id'],
            'network': tail,
            'query': query["prompt"].format(**query["args"]),
            'func_code': result.func_code,
            'eval_script': result.eval_script,
            'command': query["command"],
            'expected': query["expected"],
            'query_result': result.query_result,
            'is_equal': is_equal,
            'execution_successful': result.execution_successful,
            'execution_error': result.execution_error,
            'category': query["category"],
            'num_retries': num_retries,
            'large_model': agent.language_model.model_name,
            'temperature': agent.language_model.temperature,
            'general_prompt': general_prompt,
            'k': k,
            'attempt': result.attempt,
            'execution_time': result.execution_time,
            'query_time': result.query_time,
            'usage_tokens': result.usage_tokens,
            'cost': result.cost,
            'validation': 1 if is_equal else 0
        }
    except Exception as e:
        logger.error(f'query_test.py::process_single_query: Error in agent call: {str(e)}')
        logger.error(query["prompt"])
        return {
            'id': query['id'],
            'network': tail,
            'query': query["prompt"].format(**query["args"]),
            'func_code': None,
            'eval_script': None,
            'command': query["command"],
            'expected': query["expected"],
            'query_result': None,
            'is_equal': False,
            'execution_successful': None,
            'execution_error': None,
            'category': query["category"],
            'num_retries': num_retries,
            'large_model': agent.language_model.model_name,
            'temperature': agent.language_model.temperature,
            'general_prompt': general_prompt,
            'k': k,
            'attempt': None,
            'execution_time': None,
            'query_time': None,
            'usage_tokens': None,
            'cost': None,
            'validation': 0
        }


def process_network_queries(agent: EPANETAgent,
                            network_name: str,
                            query_list: list,
                            prompt: str,
                            exec_prompt: str,
                            except_prompt: str,
                            code_review_prompt: str,
                            num_retries: int,
                            k: int,
                            general_prompt: str,
                            num_threads: int = 1) -> pd.DataFrame:
    """Process all queries for a single network and return results as DataFrame"""

    logger.debug(f'Running queries for {network_name} with {num_threads} thread(s)...')

    if num_threads == 1:
        # Sequential execution (original behavior)
        rows_list = []
        for query in tqdm(query_list):
            row = process_single_query(
                agent, query, prompt, exec_prompt, except_prompt,
                code_review_prompt, k, num_retries, general_prompt
            )
            rows_list.append(row)
    else:
        # Parallel execution
        results_dict = {}
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {
                executor.submit(
                    process_single_query, agent, query, prompt, exec_prompt,
                    except_prompt, code_review_prompt, k, num_retries, general_prompt
                ): i
                for i, query in enumerate(query_list)
            }
            for future in tqdm(as_completed(futures), total=len(query_list)):
                original_index = futures[future]
                results_dict[original_index] = future.result()

        # Sort by original query order
        rows_list = [results_dict[i] for i in sorted(results_dict.keys())]

    return pd.DataFrame(rows_list)


def save_results(df: pd.DataFrame, filename):
    """Save results DataFrame to CSV file"""
    os.makedirs(os.path.join(get_results_dir(), 'agent'), exist_ok=True)
    save_path = os.path.join(get_results_dir(), 'agent', filename + ".csv")
    # Sort by id column to maintain query order
    df_sorted = df.sort_values('id').reset_index(drop=True)
    df_sorted.to_csv(save_path, index=False)
    logger.info(f"Results saved to {save_path}")


def initialize_agent(num_retries: int, temperature: float, large_model: str, small_model: str, use_sandbox: bool = True) -> EPANETAgent:
    """Initialize and return the EPANETAgent with required components"""
    retriever = SemanticRetriever(
        vectorstore_path=os.path.join(get_project_root(), 'data', 'faiss', f"voyage_metric_L2"),
        embed_provider="voyage"
    )
    llm = LanguageModel(model_name=large_model, temperature=temperature, top_p=1)
    eval_llm = LanguageModel(model_name=small_model, temperature=0.0)
    review_llm = LanguageModel(model_name=small_model, temperature=0.0)

    return EPANETAgent(
        retriever=retriever,
        language_model=llm,
        eval_language_model=eval_llm,
        review_language_model=review_llm,
        num_retries=num_retries,
        code_exec_fast_mode=not use_sandbox
    )


def get_network_queries(network_name: str) -> list:
    """Map network name to its query list"""
    return get_queries([network_name])


def is_number(s: str) -> bool:
    """Check if a string is a number"""
    try:
        float(s)
        return True
    except Exception:
        return False


def display_results(results_df: pd.DataFrame):
    """Display results from the DataFrame in a readable format"""
    pd.set_option('display.max_colwidth', None)

    correct = 0
    incorrect = 0
    categories = results_df['category'].unique()
    categories_dict = {cat: 0 for cat in categories}
    categories_dict_total = results_df['category'].value_counts().to_dict()

    for _, row in results_df.iterrows():
        print("\n" + "=" * 20)
        print(f"Query: {row['query']}")
        print(f"Command: {row['command']}")
        print("-" * 20)
        print("Generated code:")
        print(row['func_code'])
        print("-" * 20)
        print("Evaluation script:")
        print(row['eval_script'])
        print("-" * 20)
        print(f"Agent result: {row['query_result']}")
        print(f"Expected result: {row['expected']}")
        if is_number(row['query_result']) and is_number(row['expected']):
            is_equal = np.isclose(float(row['expected']), float(row['query_result']), rtol=0.05)
        elif type(row['query_result']) == str and type(row['expected']) == str:
            is_equal = row['query_result'].strip().casefold() == row['expected'].strip().casefold()
        else:
            is_equal = row['query_result'] == row['expected']
        print(f"Matches expected: {is_equal}")
        print('-'*20)
        print(f"Cost: {row['cost']}; Tokens used: {row['usage_tokens']}")
        print("=" * 20)
        if is_equal:
            categories_dict[row['category']] += 1
            correct += 1
        else:
            incorrect += 1

    print(f"Correct: {correct}, Incorrect: {incorrect}, Accuracy: {correct / (correct + incorrect)}")
    print(f"Categories::" + ' '.join(
        [f"{c} : {categories_dict[c]} / {categories_dict_total[c]} ;" for c in categories_dict_total.keys()]))


def main(args: argparse.Namespace):
    logger.debug(f'Starting with arguments: {args}')

    # Initialize prompts
    prompt = get_prompt(args.prompt)
    exec_prompt = get_prompt('code_exec')
    except_prompt = get_prompt('code_exception')
    review_prompt = get_prompt('code_review')

    filename = '_'.join(filter(None, [
        dt.datetime.now().strftime("%Y_%m_%d_%H-%M-%S"),
        args.save_results,
        '_'.join(args.networks),
        f"k{args.k_similar}"
    ]))
    results = pd.DataFrame()
    for model in args.large_model:
        # Initialize agent
        agent = initialize_agent(args.num_retries, args.temperature, model, args.small_model, args.sandbox)

        # Process each network
        for network_name in args.networks:
            query_list = get_network_queries(network_name)
            if not query_list:
                logger.warning(f"No queries found for network: {network_name}")
                continue

            # Process queries and save results
            network_results = process_network_queries(
                agent=agent,
                network_name=network_name,
                query_list=query_list,
                prompt=prompt,
                exec_prompt=exec_prompt,
                except_prompt=except_prompt,
                code_review_prompt=review_prompt,
                num_retries=args.num_retries,
                k=args.k_similar,
                general_prompt=args.prompt,
                num_threads=args.num_threads
            )

            # Display and save results
            print(f"\nResults for {network_name}:")
            display_results(network_results)
            results = pd.concat([results, network_results])
            if args.save_results is not None:
                save_results(results, filename)


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-n', '--networks', nargs='+', help='networks to run on', required=True)
    argparser.add_argument('--prompt', type=str, default='complex')
    argparser.add_argument('--num_retries', type=int, default=5)
    argparser.add_argument('--large_model', type=str, default='openai/gpt-4.1-mini', nargs='+')
    argparser.add_argument('--small_model', type=str, default='qwen/qwen-2.5-coder-32b-instruct')
    argparser.add_argument('-k', '--k_similar', type=int, default=5)
    argparser.add_argument('-t', '--temperature', type=float, default=0.7)
    argparser.add_argument('--num_threads', type=int, default=1,
                           help="Number of parallel threads for query processing")
    argparser.add_argument('--sandbox', action='store_true',
                           help='Run code execution in Docker sandbox (default: local run)')
    argparser.add_argument('--save_results', type=str, default='',
                           help="results file name will be: %Y_%m_%d_%H-%M-%S_ + --save_results arg")

    args = argparser.parse_args()
    main(args)
