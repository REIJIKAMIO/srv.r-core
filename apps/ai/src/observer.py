import os
import json
from ollama_client import ollama_post
from pydantic import BaseModel
from persona_inference import infer_persona
from memory import (
    save_observation,
    count_observations,
    get_last_inferred_count,
    set_last_inferred_count
)


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://ollama:11434"
)

OBSERVER_MODEL = os.getenv(
    "REI_NORMAL_MODEL",
    "qwen2.5:1.5b"
)


class ObservationResult(BaseModel):
    should_save: bool
    observation: str = ""
    confidence: float = 0.0


def observe_chat(
    subject: str,
    user_message: str
):
    prompt = f"""
以下の発言から、
「{subject}」について長期的に記憶する価値のある人物観察があるか判断してください。

保存対象:
- 長期間続きそうな好み
- 判断基準
- 考え方の傾向
- 行動パターン
- 継続的な関心
- 価値観
- 会話スタイル上の安定した特徴

保存しないもの:
- 一時的な気分
- その日の予定
- 単発の出来事
- 軽い雑談
- 根拠が弱い推測
- 健康状態など一時的・センシティブな情報
- 発言だけでは本人の属性と断定できない内容

重要:
- 原文にない情報を補完しない
- 一回の発言から性格を強く断定しない
- 観察は「〜を重視する傾向がある可能性」など慎重に表現する
- 長期記憶する価値がなければ should_save を false にする

JSONのみ返してください。

形式:
{{
  "should_save": true,
  "observation": "技術そのものより、目的を重視する傾向がある可能性がある。",
  "confidence": 0.78
}}

対象発言:
--- message ---
{user_message}
--- end ---
"""

    response, backend = ollama_post(
        "/api/chat",
        payload={
            "model": OBSERVER_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "あなたはREIです。"
                        "人物についての発言から、"
                        "長期的に意味のある観察だけを抽出します。"
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
                ObservationResult.model_json_schema(),

            "options": {
                "num_predict": 256
            }
        },
        timeout=600
    )

    response.raise_for_status()

    raw = response.json()["message"]["content"]

    result = ObservationResult.model_validate_json(raw)

    if not result.should_save:
        return {
            "status": "ignored",
            "reason": "not worth saving"
        }

    if result.confidence < 0.70:
        return {
            "status": "ignored",
            "reason": "low confidence",
            "confidence": result.confidence
        }

    save_result = save_observation(
        subject=subject,
        content=result.observation,
        source_type="chat",
        source_ref="chat"
    )

    observation_count = count_observations(subject)

    last_inferred_count = (
        get_last_inferred_count(
            subject
        )
    )

    inference_result = infer_persona(
        subject
    )

    if (
        inference_result.get("status")
        == "ok"
    ):
        set_last_inferred_count(
            subject,
            observation_count
        )

    # 前回inferから5件以上増えたら再推論
    if (
        observation_count
        - last_inferred_count
        >= 5
    ):
        try:
            inference_result = infer_persona(
                subject
            )

            # 成功した場合だけ更新
            if (
                inference_result.get("status")
                == "ok"
            ):
                set_last_inferred_count(
                    subject,
                    observation_count
                )

        except Exception as e:
            print(
                "[observer] persona inference "
                f"failed: {e}"
            )

    return {
        "status": "saved",
        "confidence": result.confidence,
        "observation": result.observation,
        "observation_count":
            observation_count,
        "last_inferred_count":
            last_inferred_count,
        "inference":
            inference_result,
        "memory":
            save_result
    }