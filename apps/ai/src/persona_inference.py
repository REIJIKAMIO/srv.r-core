import os
from datetime import datetime
from ollama_client import (
    get_available_backend,
    ollama_post
)
from memory import (
    load_observations_since,
    load_inferred_persona,
    save_inferred_persona,
    get_last_inferred_count,
    count_observations
)


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://ollama:11434"
)

def infer_persona(subject: str):

    last_inferred_count = (
        get_last_inferred_count(subject)
    )

    observation_count = (
        count_observations(subject)
    )

    new_observations = (
        load_observations_since(
            subject,
            last_inferred_count
        )
    )

    current_inferred = (
        load_inferred_persona(subject)
    )

    if not new_observations:
        return {
            "status": "no_new_observations",
            "subject": subject,
            "observation_count":
                observation_count,
            "last_inferred_count":
                last_inferred_count
        }

    observation_text = "\n\n".join(
        [
            (
                f"### {item['path']}\n"
                f"{item['text']}"
            )
            for item in new_observations
        ]
    )

    prompt = f"""
以下は現在の「{subject}」についての人物像と、
その後に追加された新しい観察記録です。

既存の人物像を、新しい観察を踏まえて更新してください。

重要:
- 出力は更新後の人物像の全文にする
- 新しい情報を単純に末尾へ追記しない
- 似た意味の傾向は統合する
- 重複する傾向は一つにまとめる
- 新しい観察によって根拠が強くなった場合はconfidenceを上げてもよい
- 矛盾する観察が追加された場合はconfidenceを下げる
- 一件しか根拠がない内容は強く断定しない
- 一時的な発言を恒久的な性格として扱わない
- 以前の推論が不適切なら修正または削除してよい
- 原文に存在しない情報を追加しない
- 観察記録そのものを全文転載しない
- 表現が違うだけで意味が近い情報を矛盾扱いしない

以下の構造でMarkdownを出力してください。

# 人物名
## 推論された傾向

各傾向について:
- 傾向の見出し
- confidence
- 根拠となる観察ファイル名
- 短い説明

必要な場合のみ:

## 不確実な点


--- 現在の人物像 ---

{current_inferred}

--- 現在の人物像ここまで ---


--- 新しい観察 ---

{observation_text}

--- 新しい観察ここまで ---

...

--- observations ---

{observation_text}

--- end ---
"""
    # -----------------------------
    # backendに応じてモデル・出力量を変更
    # -----------------------------

    backend, _ = get_available_backend()

    if backend == "gpu":
        model = os.getenv(
            "REI_INFERENCE_MODEL",
            "qwen2.5:3b"
        )

        num_predict = 1024

    else:
        model = os.getenv(
            "REI_NORMAL_MODEL",
            "qwen2.5:1.5b"
        )

        num_predict = 512

    print(
        f"[persona_inference] "
        f"backend={backend} "
        f"model={model} "
        f"num_predict={num_predict}"
    )

    # -----------------------------
    # Ollama実行
    # -----------------------------

    response, backend = ollama_post(
        "/api/chat",
        payload={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "あなたはREIです。"
                        "人物についての観察記録を整理します。"
                    )
                },
                {
                    "role": "user",
                    "content":
                        prompt + "\n/no_think"
                }
            ],
            "stream": False,
            "think": False,

            "options": {
                "num_predict": num_predict
            }
        },
        timeout=1800
    )

    response.raise_for_status()

    content = (
        response.json()
        ["message"]
        ["content"]
    )

    save_inferred_persona(
        subject,
        content
    )

    return {
        "status": "ok",
        "subject": subject,
        "backend": backend,
        "model": model,
        "num_predict": num_predict,
        "observations": len(new_observations)
    }