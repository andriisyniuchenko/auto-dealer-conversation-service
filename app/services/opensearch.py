from opensearchpy import AsyncOpenSearch

from app.core.config import settings
from app.services.embeddings import get_embedding

INDEX = "vehicles"
PIPELINE = "hybrid-search-pipeline"

_client: AsyncOpenSearch | None = None


def get_client() -> AsyncOpenSearch:
    global _client
    if _client is None:
        _client = AsyncOpenSearch(settings.opensearch_url)
    return _client


async def search_vehicles(query: str, k: int = 5) -> list[dict]:
    vector = await get_embedding(query)
    response = await get_client().search(
        index=INDEX,
        params={"search_pipeline": PIPELINE},
        body={
            "size": k,
            "query": {
                "hybrid": {
                    "queries": [
                        {
                            "knn": {
                                "vector": {
                                    "vector": vector,
                                    "k": k,
                                }
                            }
                        },
                        {
                            "match": {
                                "text": {
                                    "query": query,
                                }
                            }
                        },
                    ]
                }
            },
        },
    )
    return [hit["_source"] for hit in response["hits"]["hits"]]