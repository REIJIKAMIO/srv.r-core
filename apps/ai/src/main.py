from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from knowledge import load_markdown_files
from indexer import rebuild_index
from indexer import search_knowledge
from suggester import suggest_from_doc
from fastapi.staticfiles import StaticFiles
from scanner import scan_docs
import os
import requests
import shutil

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://r-core-ollama:21434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen3:4b")
KNOWLEDGE_DIR = Path("/home/knowledge")
INBOX_DIR = Path("/home/knowledge-inbox")
REJECTED_DIR = Path("/home/knowledge-rejected")


class ChatRequest(BaseModel):
    message: str

class SuggestRequest(BaseModel):
    path: str


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return {}

    parts = text.split("---", 2)

    if len(parts) < 3:
        return {}

    metadata = {}

    for line in parts[1].splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    return metadata


app.mount(
    "/ui",
    StaticFiles(directory="/app/static", html=True),
    name="ui"
)


@app.get("/")
def root():
    return {
        "name": "REI",
        "status": "running",
        "model": CHAT_MODEL
    }


@app.get("/knowledge/proposals")
def get_proposals():
    proposals = []

    if not INBOX_DIR.exists():
        return {
            "count": 0,
            "proposals": []
        }

    for path in sorted(INBOX_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)

        proposals.append({
            "id": meta.get("id", path.stem),
            "title": meta.get("title", ""),
            "status": meta.get("status", "pending"),
            "source": meta.get("source", ""),
            "suggested_path": meta.get("suggested_path", ""),
            "created": meta.get("created", "")
        })

    return {
        "count": len(proposals),
        "proposals": proposals
    }


@app.post("/chat")
def chat(req: ChatRequest):
    results = search_knowledge(req.message, limit=3)

    knowledge = "\n\n".join(
        [
            f"### {item['path']}\n{item['text']}"
            for item in results
        ]
    )

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": CHAT_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": f"""
                    あなたはREIです。名前の読み方はレイです。

                    親しみやすく、少しくだけた日本語で簡潔に回答してください。
                    短い質問には短く返してください。
                    必要以上に説明を広げず、自然な会話を優先してください。
                    
                    なお、普通の会話のように話してください。
                    自分の話し方を説明しないでください。
                    「親しみやすい」「自然体」などの表現を自己紹介に使わないでください。

                    例：
                    ユーザー：こんにちは。あなたは誰？
                    REI：こんにちは、私はREIです。
                    以下はあなたが参照できる知識です。
                    知識に答えがある場合は、その内容を優先してください。
                    知識に書かれていないことは、勝手に事実として作らないでください。

                    --- knowledge ---
                    {knowledge}
                    --- end ---
                    """
                },
                {
                    "role": "user",
                    "content": req.message + "\n/no_think"
                }
            ],
            "stream": False,
            "think": False,
            "options": {
                "num_predict":128
            }
        },
        timeout=600
    )

    response.raise_for_status()
    data = response.json()

    return {
        "reply": data["message"]["content"],
        "sources": [
            {
                "path": item["path"],
                "score": item["score"]
            }
            for item in results
        ]
    }


@app.get("/knowledge")
def knowledge():
    return {
        "files": load_markdown_files()
    }

@app.post("/knowledge/reindex")
def reindex():
    return rebuild_index()

@app.get("/knowledge/search")
def knowledge_search(q: str):
    return {
        "query": q,
        "results": search_knowledge(q)
    }

@app.post("/knowledge/suggest")
def suggest_knowledge(req: SuggestRequest):
    return suggest_from_doc(req.path)


@app.get("/knowledge/proposals/{proposal_id}")
def get_proposal(proposal_id: str):
    proposal_id = proposal_id.removesuffix(".md")

    source = INBOX_DIR / f"{proposal_id}.md"

    if not source.exists():
        return {
            "status": "not_found",
            "id": proposal_id
        }

    text = source.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)

    return {
        "status": "ok",
        "id": proposal_id,
        "metadata": meta,
        "content": text
    }

@app.post("/knowledge/proposals/{proposal_id}/approve")
def approve_proposal(proposal_id: str):

    proposal_id = proposal_id.removesuffix(".md")

    source = INBOX_DIR / f"{proposal_id}.md"

    if not source.exists():
        return {
            "status": "not_found",
            "id": proposal_id
        }

    text = source.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)

    suggested_path = meta.get("suggested_path")

    if not suggested_path:
        return {
            "status": "error",
            "message": "suggested_path not found"
        }

    destination = KNOWLEDGE_DIR / suggested_path
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        return {
            "status": "conflict",
            "message": "knowledge file already exists",
            "path": str(destination.relative_to(KNOWLEDGE_DIR))
        }

    shutil.move(str(source), str(destination))

    index_result = rebuild_index()

    return {
        "status": "approved",
        "id": proposal_id,
        "path": str(destination.relative_to(KNOWLEDGE_DIR)),
        "index": index_result
    }


@app.post("/knowledge/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: str):
    proposal_id = proposal_id.removesuffix(".md")

    source = INBOX_DIR / f"{proposal_id}.md"

    if not source.exists():
        return {
            "status": "not_found",
            "id": proposal_id
        }

    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    destination = REJECTED_DIR / source.name

    shutil.move(str(source), str(destination))

    return {
        "status": "rejected",
        "id": proposal_id,
        "path": str(destination)
    }

@app.post("/knowledge/scan")
def scan_knowledge_docs(limit: int | None = None):
    return scan_docs(limit)