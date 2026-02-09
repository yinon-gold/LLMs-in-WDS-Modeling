import os
from langchain_openai import OpenAIEmbeddings
from langchain_voyageai import VoyageAIEmbeddings
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings


embedding_models = {
    'openai': "text-embedding-3-large",
    'voyage': "voyage-code-3",
    'nvidia': "nv-embedqa-mistral-7b-v2"
}


embedding_function = {
    'openai': OpenAIEmbeddings(model=embedding_models['openai'], openai_api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None,
    'voyage': VoyageAIEmbeddings(voyage_api_key=os.getenv("VOYAGE_API_KEY"), model=embedding_models['voyage']) if os.getenv("VOYAGE_API_KEY") else None,
    'nvidia': NVIDIAEmbeddings(model=embedding_models['nvidia'], api_key=os.getenv("NVIDIA_NIM_API_KEY"), truncate="NONE") if os.getenv("NVIDIA_NIM_API_KEY") else None
}


def get_possible_embedding_providers():
    return list(embedding_function.keys())


def get_embedding_function_name(model_name):
    if model_name not in embedding_models:
        raise ValueError(f"Embedding model '{model_name}' is not supported. Choose from {list(embedding_models.keys())}.")
    return embedding_models[model_name]

def get_embedding_function(model_name):
    if model_name not in embedding_function:
        raise ValueError(f"Embedding model '{model_name}' is not supported. Choose from {list(embedding_function.keys())}.")
    return embedding_function[model_name]
