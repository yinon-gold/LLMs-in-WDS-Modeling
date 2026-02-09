import os
import pandas as pd
from typing import List, Optional, Tuple
from langchain_core.documents import Document

from langchain_openai import OpenAIEmbeddings
from langchain_voyageai import VoyageAIEmbeddings
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_community.vectorstores import FAISS
from llm_epanet.models.vdb import get_embedding_function_name
from llm_epanet.utils.utils import get_project_root
from llm_epanet.utils.logger import logger
from llm_epanet.utils.settings import VOYAGE_API_KEY, NVIDIA_API_KEY, OPENAI_API_KEY  # OAI key not needed, here for clarity
from llm_epanet.models.bm25retriever import BM25RetrieverBase


class Retriever:
    def retrieve(self, query: str, k: int = 10) -> List[Tuple[str, str]]:
        raise NotImplementedError("Subclasses should implement this method")

    def __call__(self, query: str, k: int = 10) -> List[Tuple[str, str]]:
        return self.retrieve(query, k=k)


class KeywordRetriever(Retriever):
    def __init__(self, doc_path: Optional[str] = None):
        logger.info(f"Initializing Retriever with HOME_DIR: {get_project_root()}")
        self._build_document_store(doc_path=doc_path)

    def retrieve(self, query: str, k: int = 10) -> List[Tuple[str, str]]:
        raise NotImplementedError("Keyword-based retrieval not implemented yet")
    
    def _build_document_store(self, doc_path: Optional[str] = None):
        if doc_path is None:
            HOME_DIR = get_project_root()
            doc_path = os.path.join(HOME_DIR, 'data', 'epyt_documentation_cleaned.csv')
        
        df = pd.read_csv(doc_path)

        docs = [
            Document(metadata={
                'func_name': doc['func_name'].strip(),
                'func_signature': doc['func_signature'].strip(),
                'func_description': ' '.join(doc['func_description'].split()),
                'func_code': ' '.join(doc['func_code'].split()),
                }, 
                page_content=str(' '.join(doc['func_signature'].split()) + '\n' + ' '.join(doc['func_description'].split())), 
                ) for doc in df.to_dict(orient='records')
        ]
        _docs = []
        for doc in docs:
            if 'See also' in doc.page_content:
                _page_content = doc.page_content.split('See also')[0].strip()
                _docs.append(Document(
                    metadata=doc.metadata,
                    page_content=_page_content,
                ))
            else:
                _docs.append(doc)

        self.docs = _docs

class BM25Retriever(KeywordRetriever):
    def __init__(self, doc_path: Optional[str] = None, k: int = 10):
        super().__init__(doc_path=doc_path)
        self.retriever = BM25RetrieverBase.from_documents(documents=self.docs, k=k)

        logger.info("BM25Retriever initialized")

    def retrieve_with_scores(self, query: str, k: Optional[int] = 10) -> List[Tuple[str, str, float]]:
        results = self.retriever.invoke(input=query)
        results = [
            (res[0].metadata['func_signature'], res[0].page_content, res[1]) for res in results
        ]
        return results

    def retrieve(self, query: str, k: Optional[int] = 10) -> List[Tuple[str, str]]:
        results = self.retrieve_with_scores(query, k=k)
        return [(res[0], res[1]) for res in results]


class SemanticRetriever(Retriever):
    def __init__(self, vectorstore_path = None, embed_provider = "voyage"):
        try:
            if vectorstore_path is None:
                vectorstore_path = os.path.join(get_project_root(), 'data', 'faiss', f"{embed_provider}_metric_L2")
            logger.info(f"Initializing Retriever with HOME_DIR: {get_project_root()}")
            logger.info(f"Using vectorstore_path: {vectorstore_path}")
            vectorstore_path = os.path.join(get_project_root(), 'data', vectorstore_path)
            self.vectorstore_path = vectorstore_path

            embed_model = get_embedding_function_name(embed_provider)

            if 'voyage' in embed_model:
                logger.info("Using VoyageAI embeddings")
                self.embeddings = VoyageAIEmbeddings(model=embed_model, voyage_api_key=VOYAGE_API_KEY)
            elif 'nvidia' in embed_model:
                logger.info("Using NVIDIA embeddings")
                self.embeddings = NVIDIAEmbeddings(model=embed_model, api_key=NVIDIA_API_KEY, truncate="NONE")
            elif 'openai' in embed_model:
                logger.info("Using OpenAI embeddings")
                self.embeddings = OpenAIEmbeddings(model=embed_model)
            else:
                logger.info("Using OpenAI embeddings")
                self.embeddings = OpenAIEmbeddings(model=embed_model)

            self.vector_store = FAISS.load_local(self.vectorstore_path, self.embeddings, allow_dangerous_deserialization=True)
            logger.info("Successfully initialized vector store")
        except Exception as e:
            logger.error(f"Failed to initialize Retriever: {str(e)}")
            raise

    def retrieve_with_scores(self, query: str, k: int = 10) -> List[Tuple[str, str, float]]:
        try:
            results = self.vector_store.similarity_search_with_score(
                query,
                k=k,
            )
            return_val = []
            for res, score in results:
                page_content = res.page_content
                try:
                    page_content = page_content.split("See also")[0]
                except Exception as e:
                    logger.warning(f"Failed to split 'See also' section, using full content: {str(e)}")
                    # return_val.append((res.metadata['func_signature'], res.page_content))
                return_val.append((res.metadata['func_signature'], page_content.strip(), score))
            return return_val
        except Exception as e:
            logger.error(f"Failed to retrieve results for query: {str(e)}")
            raise

    def retrieve(self, query: str, k: int = 10) -> List[Tuple[str, str]]:
        results = self.retrieve_with_scores(query, k=k)
        return [(res[0], res[1]) for res in results]

    def __call__(self, query: str, k: int = 10) -> List[Tuple[str, str]]:
        try:
            res = self.retrieve(query, k=k)
            return res
        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}")
            raise


class HybridRetriever(Retriever):
    def __init__(self, 
                 alpha: float = 0.5, 
                keyword_retriever: KeywordRetriever = None,
                semantic_retriever: SemanticRetriever = None
    ):
        """
        :param alpha: Weight for combining scores from keyword and semantic retrievers (0 <= alpha <= 1). Higher alpha gives more weight to keyword retriever.
        :param keyword_retriever: Description
        :param semantic_retriever: Description
        """
        self.keyword_retriever = keyword_retriever
        self.semantic_retriever = semantic_retriever
        self.alpha = alpha  # Weight for combining scores

    def retrieve(self, query: str, k: int = 10) -> List[Tuple[str, str]]:
        keyword_results = self.keyword_retriever.retrieve_with_scores(query, k=k)
        semantic_results = self.semantic_retriever.retrieve_with_scores(query, k=k)
        combined_results = [(kw[0], kw[1], kw[2] * self.alpha) for kw in keyword_results] + \
                           [(sem[0], sem[1], sem[2] * (1 - self.alpha)) for sem in semantic_results]
    
        combined_results.sort(key=lambda x: x[2], reverse=True)  # Sort by combined score

        return combined_results[:k]  # Return top-k results