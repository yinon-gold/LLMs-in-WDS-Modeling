
import os

from llm_epanet.utils.prompts import get_prompt
from llm_epanet.utils.logger import logger

import pandas as pd
from typing import List
from llm_epanet.utils.utils import get_results_dir
from llm_epanet.data.queries import get_queries


def build_retrieval_prompt(query: str, k_similar_docs: list) -> str:
    similar_docs_text = "\n\n".join([f"Function Signature: {sig}\nDocumentation: {doc}" for sig, doc in k_similar_docs])
    prompt = get_prompt(prompt_type="retrieval_evaluation").format(
        query=query,
        context=similar_docs_text,
    )
    return prompt


def extract_function_codes(qid: str, df: pd.DataFrame) -> List[str]:
    return df['func_code'][df['id'] == qid].tolist()


def extract_function_names(func_code: str) -> str:
    functions = []
    lines = func_code.split('\n')
    for line in lines:
        line = line.strip()
        if 'd.' in line:
            func_name = line.split('d.')[1].split('(')[0]
            functions.append(func_name)
    return functions


def get_gt_relevant_functions(filter_empty: bool = False) -> dict:
    all_qids = [e['id'] for e in get_queries('all')]
    results_dir = os.path.join(get_results_dir(), 'agent')
    result_files = sorted(os.listdir(results_dir))
    result_files = [f for f in result_files if not f.startswith('.') and f.endswith('.csv')]
    ground_truth = {}

    for qid in all_qids:
        relevant_functions = []


        for result_file in result_files[::-1]:
            df_io = pd.read_csv(os.path.join(results_dir, result_file))
            if 'is_equal' not in df_io.columns and 'validation' not in df_io.columns:
                continue
            if 'validation' in df_io.columns:
                df_true = df_io[df_io['validation'] == True]
            else:
                df_true = df_io[df_io['is_equal'] == True]

            func_codes = extract_function_codes(qid, df_true)
            for code in func_codes:
                relevant_functions.extend(extract_function_names(code))

        relevant_functions = list(set(relevant_functions))
        ground_truth[qid] = relevant_functions
        if filter_empty and len(ground_truth[qid]) == 0:
            del ground_truth[qid]
    return ground_truth


def clean_retrieved_docs(k_similar_docs):
    cleaned_docs = []
    for doc in k_similar_docs:
        func_name = doc[0]
        # Remove code block markers if present
        func_name = func_name.split('(')[0] 
        cleaned_docs.append(func_name)
    return cleaned_docs


