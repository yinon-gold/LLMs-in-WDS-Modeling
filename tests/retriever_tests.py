import asyncio
from datetime import date, datetime
import json
import os
import argparse
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List

from pydantic import BaseModel, Field
from concurrent.futures import ThreadPoolExecutor, as_completed


from pathlib import Path
from dotenv import load_dotenv

from llm_epanet.models.vdb import get_embedding_function_name, get_embedding_function_name, get_possible_embedding_providers
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env', override=True)

from llm_epanet.models.llm import LanguageModel
from llm_epanet.models.retriever import BM25Retriever, HybridRetriever, Retriever, SemanticRetriever
# from llm_epanet.utils.prompts import get_prompt
from llm_epanet.utils.logger import logger
from llm_epanet.utils.utils import get_project_root, get_results_dir
from llm_epanet.data.queries import get_queries
from llm_epanet.utils.retriever_utils import build_retrieval_prompt, clean_retrieved_docs, get_gt_relevant_functions


# class RetrievalGrade(BaseModel):
#     query: str = Field(default="", description="The query string")
#     command: str = Field(default="", description="The ground truth command to be executed")
#     explanation: str = Field(default="", description="Explanation of query grading")
#     scores: dict = Field(default_factory=dict, description="Scores for various criteria")
    

def calc_score(retrieved_docs: List[str], ground_truth: List[str]) -> dict:
    results = {}
    for k in [1, 3, 5, 7, 10]:
        retrieved_docs_k = retrieved_docs[:k]
        ground_truth_k = ground_truth[:k]
        true_positives = len(set(retrieved_docs_k) & set(ground_truth_k))
        false_positives = len(set(retrieved_docs_k) - set(ground_truth_k))
        false_negatives = len(set(ground_truth_k) - set(retrieved_docs_k))

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0

        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        results[f'precision@{k}'] = precision
        results[f'recall@{k}'] = recall
        results[f'f1@{k}'] = f1_score
    return results


async def run_reviewer_single_query(gt_all: Dict, retriever: Retriever, query: Dict) -> Dict:
    k = 10
    qid = query['id']
    query_text = query['prompt']
    ground_truth = gt_all.get(qid, [])
    if ground_truth == []:
        logger.error(f"No ground truth found for query ID {qid}. Skipping.")
        return {qid: {'scores': {}, 'retrieved_docs': [], 'ground_truth': []}}
    k_similar_docs = retriever(query_text, k=k)
    retrieved_docs = clean_retrieved_docs(k_similar_docs)
    assert len(retrieved_docs) == k, f"Expected {k} documents, got {len(retrieved_docs)}"

    scores = calc_score(retrieved_docs, ground_truth)

    logger.info(f"{qid}: {scores}")

    return {qid: {'scores': scores, 'retrieved_docs': retrieved_docs, 'ground_truth': ground_truth}}
    

async def run_reviewer_multi_threaded(retriever: Retriever, queries: List[Dict], num_threads: int = 1) -> List[Dict]:
    results = {}
    gt_all = get_gt_relevant_functions(filter_empty=True)
    logger.info(f"Running retrieval evaluation with {num_threads} threads on {len(queries)} queries.")

    tasks = [run_reviewer_single_query(gt_all, retriever, query) for query in queries]
    results = await asyncio.gather(*tasks)

    return results


def create_retriever(retriever_type: str, alpha: float = 0.5, embed_model: str = "voyage") -> Retriever:
    """Create a retriever based on the type and alpha value."""
    if retriever_type == "semantic":
        return SemanticRetriever(
            vectorstore_path=os.path.join(get_project_root(), 'data', 'faiss', f"{embed_model}_metric_L2"),
            embed_provider=embed_model
        )
    elif retriever_type == "bm25":
        return BM25Retriever(
            doc_path=None,
            k=10
        )
    elif retriever_type == "hybrid":
        bm25_retriever = BM25Retriever(
            doc_path=None,
            k=10
        )
        semantic_retriever = SemanticRetriever(
            vectorstore_path=os.path.join(get_project_root(), 'data', 'faiss', f"{embed_model}_metric_L2"),
            embed_provider=embed_model
        )
        return HybridRetriever(
            keyword_retriever=bm25_retriever,
            semantic_retriever=semantic_retriever,
            alpha=alpha
        )
    else:
        raise ValueError(f"Unknown retriever type: {retriever_type}")


async def main(args):
    logger.info("[START] Starting LLM-Epanet Retrieval Tests")
    logger.info(f'{args=}')

    retriever = create_retriever(args.retriever, alpha=args.alpha, embed_model=args.embedding_model)

    queries = get_queries('all')
    results = []

    results = await run_reviewer_multi_threaded(retriever, queries, num_threads=args.num_threads)

    cleaned_results = {}
    for res in results:
        print(res)
        for k, v in res.items():
            cleaned_results[k] = v
    results = cleaned_results

    results_dir = get_results_dir()
    timestamp = datetime.now().strftime('%Y_%m_%d_%H-%M-%S')
    result_unique_id = f"{args.retriever}"
    if args.retriever == "hybrid":
        result_unique_id += f"_a_{args.alpha}"
    filename = f"retrieval_results_{timestamp}_{result_unique_id}.json"
    os.makedirs(os.path.join(results_dir, 'retrieval'), exist_ok=True)
    results_file = os.path.join(results_dir, 'retrieval', filename)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=4)
    logger.info(f"Saved retrieval results to {results_file}")
    logger.info("[END] Retrieval Tests Completed")
    return filename, results


async def run_alpha_sweep(args, alpha_values: List[float]) -> Dict[float, Dict]:
    """Run retrieval evaluation for multiple alpha values."""
    all_results = {}
    queries = get_queries('all')

    for alpha in alpha_values:
        logger.info(f"Running hybrid retriever with alpha={alpha}")
        retriever = create_retriever("hybrid", alpha=alpha, embed_model=args.embedding_model)

        results = await run_reviewer_multi_threaded(retriever, queries, num_threads=args.num_threads)

        cleaned_results = {}
        for res in results:
            for k, v in res.items():
                cleaned_results[k] = v

        all_results[alpha] = cleaned_results
        logger.info(f"Completed alpha={alpha}")

    return all_results


def aggregate_scores_by_alpha(all_results: Dict[float, Dict], metric: str = "recall") -> Dict[float, Dict[int, List[float]]]:
    """
    Aggregate scores from all queries for each alpha value.

    Returns a dict: {alpha: {k: [list of scores for all queries]}}
    """
    k_values = [1, 3, 5, 7, 10]
    aggregated = {}

    for alpha, results in all_results.items():
        aggregated[alpha] = {k: [] for k in k_values}
        for query_id, query_result in results.items():
            scores = query_result.get('scores', {})
            for k in k_values:
                score_key = f"{metric}@{k}"
                if score_key in scores:
                    aggregated[alpha][k].append(scores[score_key])

    return aggregated


def create_boxplots(all_results: Dict[float, Dict], results_dir: str = None):
    """
    Create box plots showing retrieval performance across different alpha values.

    Creates 3 separate figures (Precision@k, Recall@k, F1@k).
    Each figure has a single plot with:
    - X-axis: k values (1, 3, 5, 7, 10)
    - Y-axis: score
    - Grouped box plots for each alpha value at each k position
    """
    metrics = ["precision", "recall", "f1"]
    k_values = [1, 3, 5, 7, 10]
    alpha_values = sorted(all_results.keys())

    if results_dir is None:
        results_dir = get_results_dir()
        results_dir = os.path.join(results_dir, 'retrieval')
        os.makedirs(results_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y_%m_%d_%H-%M-%S')
    output_paths = []

    # Color palette for different alpha values
    colors = plt.cm.viridis(np.linspace(0, 1, len(k_values)))

    for metric in metrics:
        fig, ax = plt.subplots(figsize=(10, 6))
        aggregated = aggregate_scores_by_alpha(all_results, metric)

        n_alphas = len(alpha_values)
        width = 0.15
        positions = []
        box_data = []
        box_colors = []

        for k_idx, k in enumerate(k_values):
            base_pos = k_idx * (n_alphas + 1) * width + k_idx * 0.3
            positions.append(base_pos)
            box_data.append(np.mean([aggregated[alpha][k] for alpha in alpha_values], axis=-1))
            box_colors.append(colors[k_idx])  # Color for the mean point
            # for alpha_idx, alpha in enumerate(alpha_values):
                # pos = base_pos + alpha_idx * width
                # positions.append(pos)
                # box_data.append(aggregated[alpha][k])
                # box_colors.append(colors[alpha_idx])

        bp = ax.boxplot(box_data, widths=width * 0.8, patch_artist=True)

        # Color the boxes
        for patch, color in zip(bp['boxes'], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        # Set x-axis labels at center of each k group
        tick_positions = []
        for k_idx, k in enumerate(k_values):
            base_pos = k_idx * width
            tick_positions.append(base_pos + width / 2)

        # ax.set_xticks(tick_positions)
        ax.set_xticklabels([str(k) for k in k_values])
        ax.set_xlabel('k', fontsize=12)
        ax.set_ylabel('Score', fontsize=12)
        ax.set_title(f'{metric.capitalize()}@k', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 1.05)
        ax.grid(axis='y', alpha=0.3)

        # Create legend
        # legend_handles = [plt.Rectangle((0, 0), 1, 1, facecolor=colors[i], alpha=0.7)
                        #   for i in range(len(k_values))]
        # legend_labels = [f'α={alpha}' for alpha in alpha_values]
        # ax.legend(legend_handles, legend_labels, loc='lower right')

        plt.tight_layout()

        metric_output_path = os.path.join(results_dir, f"retrieval_boxplot_{metric}_{timestamp}.png")
        plt.savefig(metric_output_path, dpi=150, bbox_inches='tight')
        logger.info(f"Saved {metric} box plot to {metric_output_path}")
        plt.close()
        output_paths.append(metric_output_path)

    return output_paths


async def run_alpha_sweep_and_plot(args):
    """Run experiments with multiple alpha values and create box plots."""
    alpha_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.93, 0.95, 1.0]

    logger.info(f"[START] Running alpha sweep with values: {alpha_values}")

    all_results = await run_alpha_sweep(args, alpha_values)

    # Save aggregated results
    results_dir = get_results_dir()
    timestamp = datetime.now().strftime('%Y_%m_%d_%H-%M-%S')

    # Convert float keys to strings for JSON serialization
    serializable_results = {str(k): v for k, v in all_results.items()}
    results_file = os.path.join(results_dir, 'retrieval', f"retrieval_alpha_sweep_{timestamp}.json")
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(serializable_results, f, indent=4)
    logger.info(f"Saved alpha sweep results to {results_file}")

    # Create box plots (one per metric)
    plot_paths = create_boxplots(all_results, results_dir=os.path.join(results_dir, 'retrieval'))

    logger.info("[END] Alpha sweep completed")
    return results_file, plot_paths


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-n', '--networks', nargs='+', help='networks to run on', required=True)
    argparser.add_argument('--num_threads', type=int, default=1,
                           help="Number of parallel threads for query processing")
    argparser.add_argument("-em", "--embedding_model", type=str, default='voyage', 
                        choices=get_possible_embedding_providers(), 
                        help="The embedding model to use for creating the vector store")
    argparser.add_argument('--retriever', type=str, help="Retriever class to use",
                           choices=["semantic", "bm25", "hybrid"], default="semantic")
    argparser.add_argument('--alpha', type=float, default=0.5,
                           help="Alpha value for HybridRetriever (0 <= alpha <= 1)")
    argparser.add_argument('--alpha_sweep', action='store_true',
                           help="Run experiments with multiple alpha values (0, 0.1, 0.5, 1.0) and create box plots")

    args = argparser.parse_args()

    if args.alpha_sweep:
        asyncio.run(run_alpha_sweep_and_plot(args))
    else:
        asyncio.run(main(args))

    print(f'{args=}')