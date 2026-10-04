import os
from ollama_client import ollama_post
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

from knowledge import load_markdown_files


QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://qdrant:6333"
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "qwen3-embedding:0.6b"
)

COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION",
    "rei_memory"
)


client = QdrantClient(
    url=QDRANT_URL
)


def embed(text: str):

    response, backend = ollama_post(
        "/api/embed",
        payload={
            "model": EMBEDDING_MODEL,
            "input": text
        },
        timeout=120
    )

    data = response.json()

    return data["embeddings"][0]


def rebuild_index():
    """
    docs / knowledge / canon をすべて読み込み、
    Qdrantのcollectionを作り直す。
    """

    files = load_markdown_files()

    if not files:
        return {
            "status": "empty",
            "count": 0
        }

    # 最初のファイルでEmbedding次元数を確認
    first_vector = embed(files[0]["text"])

    vector_size = len(first_vector)

    # 既存collectionを削除
    if client.collection_exists(
        COLLECTION_NAME
    ):
        client.delete_collection(
            COLLECTION_NAME
        )

    # collection再作成
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )

    points = []

    for i, file in enumerate(files):

        try:
            vector = embed(
                file["text"]
            )

            points.append(
                PointStruct(
                    id=i,
                    vector=vector,
                    payload={
                        "source_type": file[
                            "source_type"
                        ],
                        "path": file[
                            "path"
                        ],
                        "text": file[
                            "text"
                        ]
                    }
                )
            )

            print(
                "[indexer] indexed:",
                file["source_type"],
                file["path"]
            )

        except Exception as e:
            print(
                "[indexer] failed:",
                file["source_type"],
                file["path"],
                e
            )

    if not points:
        return {
            "status": "error",
            "count": 0,
            "message": "No files could be indexed"
        }

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return {
        "status": "ok",
        "count": len(points),
        "collection": COLLECTION_NAME
    }


def search_knowledge(
    query: str,
    limit: int = 5
):
    """
    Qdrantから意味的に近い資料を検索する。
    """

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

            "source_type":
                result.payload.get(
                    "source_type"
                ),

            "path":
                result.payload.get(
                    "path"
                ),

            "text":
                result.payload.get(
                    "text"
                )
        }
        for result in results
    ]