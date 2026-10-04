import os
import requests


GPU_URL = os.getenv(
    "OLLAMA_GPU_URL",
    ""
)

CPU_URL = os.getenv(
    "OLLAMA_CPU_URL",
    "http://r-core-ollama:11434"
)


def get_ollama_url():
    """
    GPU側Ollamaが利用可能ならそちらを使用。
    利用できなければCPU側へフォールバック。
    """

    if GPU_URL:
        try:
            response = requests.get(
                f"{GPU_URL}/api/tags",
                timeout=1
            )

            if response.ok:
                return GPU_URL

        except requests.RequestException:
            pass

    return CPU_URL