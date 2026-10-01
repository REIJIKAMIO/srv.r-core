from pathlib import Path
from datetime import datetime
import os
import requests
import json
import re
import uuid

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
SUGGEST_MODEL = os.getenv("REI_DEEP_MODEL", "qwen3:4b")

DOCS_DIR = Path("/home/docs")
INBOX_DIR = Path("/home/knowledge-inbox")


def safe_filename(text: str) -> str:
    text = re.sub(r'[\\/:*?"<>|]', "-", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:80] or "proposal"


def generate_proposal_id():
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = uuid.uuid4().hex[:6]
    return f"p_{now}_{short_id}"


def suggest_from_doc(relative_path: str):
    source_path = DOCS_DIR / relative_path

    if not source_path.exists():
        raise FileNotFoundError(relative_path)

    source = source_path.read_text(encoding="utf-8")

    prompt = f"""
以下のドキュメントから、
長期的に再利用価値のある知識だけを抽出してください。

対象:
- 定義
- 確定した事実
- 採用した設計
- 方針
- 判断基準
- 長期間有効な設定
- 他資料を理解するための前提

除外:
- 一時的な予定
- 雑談
- 未採用案
- 思考途中の仮説
- その場限りの感情
- すでに否定された案

原文にない内容を補完しないでください。

JSONだけを返してください。

形式:
{{
  "title": "知識のタイトル",
  "suggested_path": "分類/filename.md",
  "content": "知識として残す本文",
  "reason": "なぜ長期知識として残す価値があるか"
}}

対象ドキュメント:
--- source ---
{source}
--- end ---
"""

    response = requests.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": SUGGEST_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "あなたはREIです。資料整理を担当します。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "think": False,
            "format": "json",
            "options": {
                "num_predict": 512
            }
        },
        timeout=1800
    )

    response.raise_for_status()

    raw = response.json()["message"]["content"]
    proposal = json.loads(raw)

    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    proposal_id = generate_proposal_id()
    filename = f"{proposal_id}.md"
    output_path = INBOX_DIR / filename

    output = f"""---
id: {proposal_id}
status: pending
title: {proposal["title"]}
source: {relative_path}
suggested_path: {proposal["suggested_path"]}
created: {datetime.now().isoformat()}
---

# {proposal["title"]}

{proposal["content"]}

## REIからの提案理由

{proposal["reason"]}
"""

    output_path.write_text(output, encoding="utf-8")

    return {
        "status": "ok",
        "proposal": filename,
        "source": relative_path,
        "suggested_path": proposal["suggested_path"]
    }