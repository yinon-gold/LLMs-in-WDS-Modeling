import os
from datetime import datetime
import pandas as pd
from tqdm import tqdm

import faiss
from langchain_core.documents import Document
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS

from llm_epanet.models.vdb import get_embedding_function, get_possible_embedding_providers, get_embedding_function_name
from llm_epanet.utils.utils import get_project_root
HOME_DIR = get_project_root()

import dotenv
dotenv.load_dotenv()


def main(args):

    embeddings = get_embedding_function(args.embedding_model)

    df = pd.read_csv(os.path.join(HOME_DIR, 'data', 'epyt_documentation_cleaned.csv'))

    index = faiss.IndexFlatL2(len(embeddings.embed_query("hello world")))

    vector_store = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore(),
        index_to_docstore_id={},
    )

    # metadata can be str(sha256(doc['func_name'].encode("utf-8")).hexdigest())
    docs = [
        Document(metadata={
            'func_name': doc['func_name'].strip(),
            'func_signature': doc['func_signature'].strip(),
            'func_description': ' '.join(doc['func_description'].split()),
            'func_code': ' '.join(doc['func_code'].split()),
            }, 
            page_content=' '.join(doc['func_signature'].split()) + '\n' + ' '.join(doc['func_description'].split()), doc_id=doc['func_name'].strip()) for doc in df.to_dict(orient='records')
    ]

    print(f'Embedding {len(df)} documents with {get_embedding_function_name(args.embedding_model)}...')
    time_start = datetime.now().timestamp()

    vector_store.add_documents(docs)

    time_end = datetime.now().timestamp()
    time_to_create = time_end - time_start

    path_to_save = os.path.join(HOME_DIR, 'data', 'faiss', f"{args.embedding_model}_metric_L2")
    vector_store.save_local(path_to_save)

    print(f'Vector store created at {time_to_create:.3f} seconds saved at {path_to_save}')


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a FAISS vector store from EPyT documentation.")
    parser.add_argument("-em", "--embedding_model", type=str, default='voyage', 
                        choices=get_possible_embedding_providers(), 
                        help="The embedding model to use for creating the vector store")
    args = parser.parse_args()

    main(args)