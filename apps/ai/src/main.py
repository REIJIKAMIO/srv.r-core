from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from ollama_client import ollama_post
from ollama_client import ollama_get
from persona import load_persona_core
from knowledge import load_markdown_files
from indexer import rebuild_index, search_knowledge
from memory import (
    save_observation,
    load_observations,
    load_inferred_persona,
    count_observations,
    get_last_inferred_count
)
from persona_inference import infer_persona
from observer import observe_chat
from collector import collect_all
from recommendation import (
    load_recommendations,
    mark_opened,
    dismiss_recommendation
)

import os


app = FastAPI()


CHAT_MODEL = os.getenv(
    "CHAT_MODEL",
    "qwen2.5:1.5b"
)

ACTIVE_PERSONA = os.getenv(
    "ACTIVE_PERSONA",
    "rei"
)

SUBJECT_PERSONA = os.getenv(
    "SUBJECT_PERSONA",
    "reiji"
)

class ChatRequest(BaseModel):
    message: str

class ObservationRequest(BaseModel):
    content: str
    source_type: str
    source_ref: str = ""

class ObserveRequest(BaseModel):
    message: str

# -----------------------------
# UI
# -----------------------------

app.mount(
    "/ui",
    StaticFiles(
        directory="/app/static",
        html=True
    ),
    name="ui"
)


# -----------------------------
# Root
# -----------------------------

@app.get("/")
def root():
    return {
        "name": "REI",
        "status": "running",
        "model": CHAT_MODEL,
        "active_persona": ACTIVE_PERSONA,
        "subject_persona": SUBJECT_PERSONA
    }

#
# collect
#
@app.post("/knowledge/collect")
def collect_knowledge():
    return collect_all()

#
# reccomend
#
@app.get("/recommendations")
def recommendations():
    items = load_recommendations()

    return {
        "count": len(items),
        "recommendations": items
    }


@app.post(
    "/recommendations/{recommendation_id}/opened"
)
def recommendation_opened(
    recommendation_id: str
):
    return mark_opened(
        recommendation_id
    )


@app.post(
    "/recommendations/{recommendation_id}/dismiss"
)
def recommendation_dismiss(
    recommendation_id: str
):
    return dismiss_recommendation(
        recommendation_id
    )

# -----------------------------
# Chat
# -----------------------------

@app.post("/chat")
def chat(
    req: ChatRequest,
    background_tasks: BackgroundTasks
):
    # 誰として喋るか
    persona_core = load_persona_core(
        ACTIVE_PERSONA
    )

    # 誰と喋っているか
    inferred_persona = load_inferred_persona(
        SUBJECT_PERSONA
    )

    # 質問に意味的に近い資料をQdrantから取得
    results = search_knowledge(
        req.message,
        limit=5
    )


    context = "\n\n".join(
        [
            (
                f"### source_type: {item['source_type']}\n"
                f"### path: {item['path']}\n"
                f"{item['text']}"
            )
            for item in results
        ]
    )

    system_prompt = f"""
あなたはREIです。
名前の読み方は「レイ」です。

以下は現在のあなた自身の基本人格・設定です。
この内容は通常のRAG資料より優先してください。

--- persona core ---

{persona_core}

--- persona core end ---

現在の会話相手は「{SUBJECT_PERSONA}」です。

以下は、過去の会話や記録から推論された
会話相手についての人物像です。

これは確定情報ではありません。
参考情報として扱い、
現在の本人の発言と矛盾する場合は
現在の発言を優先してください。

--- inferred persona ---

{inferred_persona}

--- inferred persona end ---

普通の会話のように話してください。
親しみやすく、少しくだけた日本語で簡潔に回答してください。

短い質問には短く返してください。
必要以上に説明を広げないでください。

自分の話し方を説明しないでください。
「親しみやすい」「自然体」などの表現を自己紹介として使用しないでください。

例：

ユーザー：
こんにちは。あなたは誰？

REI：
こんにちは、REIです。


あなたは以下の資料を参照できます。

資料には3種類あります。


## canon

現在の設定・定義・基準として扱う資料です。

canonに記載されている内容は、
docsやknowledgeより優先してください。


## docs

レイジまたはイケボノオオカミが過去に作成した資料です。
レイジまたはイケボノオオカミが過去に何を考え、何を調べ、何を記録していたかを示す資料として扱ってください。

内容は現在も正しいとは限りません。

古い資料と現在の設定が異なる場合は、
古い内容を現在の事実として断定しないでください。


## knowledge

REIが外部情報源を調査して整理した資料です。
内容は参照日時点の情報であり、現在も正しいとは限りません。
参照元URLや参照日が記録されている場合は、必要に応じてそれらも考慮してください。


## 回答ルール

資料に答えがある場合は、
その内容を優先してください。

複数の資料に異なる内容がある場合は、
無理にひとつへ統合せず、
資料ごとの差異が分かるようにしてください。

資料から確認できない内容を、
事実として勝手に作らないでください。

docsに書かれている内容については、
必要に応じて
「過去の資料では」
「以前はこう考えていたようです」
など、
過去の記録であることが分かる表現を使用してください。


--- reference start ---

{context}

--- reference end ---
"""

    response, backend = ollama_post(
        "/api/chat",
        payload={
            "model": CHAT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": (
                        req.message
                        + "\n/no_think"
                    )
                }
            ],
            "stream": False,
            "think": False,
            "options": {
                "num_predict": 256
            }
        },
        timeout=600
    )

    response.raise_for_status()

    data = response.json()

    background_tasks.add_task(
        observe_chat,
        SUBJECT_PERSONA,
        req.message
    )

    return {
        "reply": data["message"]["content"],
        "backend": backend,

        "sources": [
            {
                "source_type":
                    item["source_type"],

                "path":
                    item["path"],

                "score":
                    item["score"]
            }
            for item in results
        ]
    }


# -----------------------------
# Knowledge debug
# -----------------------------

@app.get("/knowledge")
def knowledge():
    """
    docs / knowledge / canon の
    読み込み状況を確認するためのAPI。
    """

    return {
        "files": load_markdown_files()
    }


# -----------------------------
# Reindex
# -----------------------------

@app.post("/knowledge/reindex")
def reindex():
    """
    docs / knowledge / canon を
    Qdrantへ再登録する。
    """

    return rebuild_index()


# -----------------------------
# Search debug
# -----------------------------

@app.get("/knowledge/search")
def knowledge_search(
    q: str,
    limit: int = 5
):
    """
    Qdrantの検索結果を
    直接確認するためのAPI。
    """

    return {
        "query": q,
        "results": search_knowledge(
            q,
            limit=limit
        )
    }

# ---
# memory
# ---
@app.post("/memory/personas/{subject}/observations")
def create_observation(
    subject: str,
    req: ObservationRequest
):
    return save_observation(
        subject=subject,
        content=req.content,
        source_type=req.source_type,
        source_ref=req.source_ref
    )


@app.get("/memory/personas/{subject}/observations")
def get_observations(subject: str):
    observations = load_observations(subject)

    return {
        "subject": subject,
        "count": len(observations),
        "observations": observations
    }


@app.post("/memory/personas/{subject}/infer")
def run_persona_inference(subject: str):
    return infer_persona(subject)


@app.get("/memory/personas/{subject}/inferred")
def get_inferred_persona(subject: str):
    return {
        "subject": subject,
        "content":
            load_inferred_persona(subject)
    }

#
# memory observe
#
@app.post("/memory/personas/{subject}/observe")
def observe_persona(
    subject: str,
    req: ObserveRequest
):
    return observe_chat(
        subject=subject,
        user_message=req.message
    )

#
# debug
#
@app.get("/debug/persona")
def debug_persona():

    persona_core = load_persona_core(
        ACTIVE_PERSONA
    )

    inferred_persona = (
        load_inferred_persona(
            SUBJECT_PERSONA
        )
    )

    observation_count = (
        count_observations(
            SUBJECT_PERSONA
        )
    )

    last_inferred_count = (
        get_last_inferred_count(
            SUBJECT_PERSONA
        )
    )

    return {
        "active_persona":
            ACTIVE_PERSONA,

        "subject_persona":
            SUBJECT_PERSONA,

        "persona_core_loaded":
            bool(persona_core.strip()),

        "persona_core_length":
            len(persona_core),

        "persona_core":
            persona_core,

        "inferred_persona_loaded":
            bool(
                inferred_persona.strip()
            ),

        "inferred_persona_length":
            len(inferred_persona),

        "inferred_persona":
            inferred_persona,

        "observation_count":
            observation_count,

        "last_inferred_count":
            last_inferred_count,

        "observations_until_inference":
            max(
                0,
                5 - (
                    observation_count
                    - last_inferred_count
                )
            )
    }

@app.get("/debug/ollama")
def debug_ollama():

    response, backend = ollama_get(
        "/api/tags"
    )

    data = response.json()

    return {
        "backend": backend,
        "models": [
            model.get("name")
            for model in data.get(
                "models",
                []
            )
        ]
    }