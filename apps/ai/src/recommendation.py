from pathlib import Path
from datetime import datetime
import hashlib
import json
import os
import shutil

from pydantic import BaseModel

from memory import load_inferred_persona
from ollama_client import ollama_post


RECOMMENDATION_DIR = Path(
    "/home/recommendations"
)

PENDING_DIR = (
    RECOMMENDATION_DIR / "pending"
)

OPENED_DIR = (
    RECOMMENDATION_DIR / "opened"
)

DISMISSED_DIR = (
    RECOMMENDATION_DIR / "dismissed"
)


SUBJECT_PERSONA = os.getenv(
    "SUBJECT_PERSONA",
    "reiji"
)

RECOMMEND_MODEL = os.getenv(
    "REI_INFERENCE_MODEL",
    "qwen2.5:3b"
)


class RecommendationResult(BaseModel):
    recommend: bool
    score: float
    reason: str


def make_recommendation_id(
    url: str
):
    return hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:16]


def evaluate_article(
    title: str,
    url: str,
    summary: str,
    source_name: str
):
    inferred_persona = (
        load_inferred_persona(
            SUBJECT_PERSONA
        )
    )

    prompt = f"""
以下の記事について、
現在の会話相手「{SUBJECT_PERSONA}」に
薦める価値があるか判断してください。

人物像はREIによる推論であり、
確定情報ではありません。
過度に断定せず参考情報として使用してください。

評価基準:
- 過去の関心や考え方と関連がある
- 新しい視点を得られそう
- 継続して扱っているテーマと関係する
- 実際に本人が読む価値がありそう
- 単なる広告や利用規約などは薦めない

score:
0.0〜1.0

reason:
なぜ薦めたいかを、
本人にそのまま見せられる短い日本語で書いてください。

--- 人物像 ---

{inferred_persona}

--- 記事 ---

情報源:
{source_name}

タイトル:
{title}

URL:
{url}

内容:
{summary}

--- end ---
"""

    response, backend = ollama_post(
        "/api/chat",
        payload={
            "model": RECOMMEND_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "あなたはREIです。"
                        "記事を会話相手に薦める価値が"
                        "あるか判断します。"
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "think": False,
            "format":
                RecommendationResult.model_json_schema(),
            "options": {
                "num_predict": 256
            }
        },
        timeout=600
    )

    result = (
        RecommendationResult
        .model_validate_json(
            response.json()
            ["message"]
            ["content"]
        )
    )

    return result, backend


def create_recommendation(
    title: str,
    url: str,
    summary: str,
    source_name: str,
    knowledge_path: str
):
    result, backend = (
        evaluate_article(
            title=title,
            url=url,
            summary=summary,
            source_name=source_name
        )
    )

    # 薦めない場合
    if not result.recommend:
        return {
            "status": "ignored",
            "score": result.score,
            "reason": result.reason
        }

    # あまりにも弱い推薦は保存しない
    if result.score < 0.65:
        return {
            "status": "ignored",
            "score": result.score,
            "reason": result.reason
        }

    PENDING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    recommendation_id = (
        make_recommendation_id(url)
    )

    path = (
        PENDING_DIR
        / f"{recommendation_id}.json"
    )

    data = {
        "id": recommendation_id,
        "status": "pending",
        "title": title,
        "url": url,
        "source_name": source_name,
        "knowledge_path":
            knowledge_path,
        "score": result.score,
        "reason": result.reason,
        "created":
            datetime.now().isoformat(),
        "backend": backend
    }

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return {
        "status": "recommended",
        **data
    }


def load_recommendations():
    if not PENDING_DIR.exists():
        return []

    items = []

    for path in sorted(
        PENDING_DIR.glob("*.json")
    ):
        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            items.append(data)

        except Exception as e:
            print(
                f"[recommendation] "
                f"failed: {path} {e}"
            )

    # scoreの高い順
    items.sort(
        key=lambda x:
            x.get("score", 0),
        reverse=True
    )

    return items


def move_recommendation(
    recommendation_id: str,
    destination_dir: Path,
    status: str
):
    source = (
        PENDING_DIR
        / f"{recommendation_id}.json"
    )

    if not source.exists():
        return {
            "status": "not_found",
            "id": recommendation_id
        }

    destination_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    data = json.loads(
        source.read_text(
            encoding="utf-8"
        )
    )

    data["status"] = status
    data[f"{status}_at"] = (
        datetime.now().isoformat()
    )

    destination = (
        destination_dir
        / source.name
    )

    destination.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    source.unlink()

    return {
        "status": status,
        "id": recommendation_id
    }


def mark_opened(
    recommendation_id: str
):
    return move_recommendation(
        recommendation_id,
        OPENED_DIR,
        "opened"
    )


def dismiss_recommendation(
    recommendation_id: str
):
    return move_recommendation(
        recommendation_id,
        DISMISSED_DIR,
        "dismissed"
    )