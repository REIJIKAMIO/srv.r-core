import os
import requests

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)

from knowledge import load_markdown_files


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

EMBEDDING_MODEL = "qwen3-embedding:0.6b"
COLLECTION_NAME = "rei_knowledge"


client = QdrantClient(url=QDRANT_URL)


def embed(text: str):
    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={
            "model": EMBEDDING_MODEL,
            "input": text
        },
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["embeddings"][0]


def rebuild_index():
    files = load_markdown_files()

    if not files:
        return {
            "status": "empty",
            "count": 0
        }

    # 最初の文書でベクトル次元数を確認
    first_vector = embed(files[0]["text"])

    vector_size = len(first_vector)

    # collectionを作り直す
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )

    points = []

    for i, file in enumerate(files):
        vector = embed(file["text"])

        points.append(
            PointStruct(
                id=i,
                vector=vector,
                payload={
                    "path": file["path"],
                    "text": file["text"]
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return {
        "status": "ok",
        "count": len(points)
    }


def search_knowledge(query: str, limit: int = 3):
    vector = embed(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=limit,
        with_payload=True
    ).points

    return [
        {
            "score": result.score,
            "path": result.payload.get("path"),
            "text": result.payload.get("text")
        }
        for result in results
    ]