from langchain_ollama import OllamaEmbeddings

from app.core.config import settings

_embeddings = OllamaEmbeddings(
    model=settings.embedding_model,
    base_url=settings.ollama_base_url,
)


async def get_embedding(text: str) -> list[float]:
    return await _embeddings.aembed_query(text)