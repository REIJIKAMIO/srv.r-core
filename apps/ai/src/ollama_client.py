import os
import requests


OLLAMA_GPU_URL = os.getenv(
    "OLLAMA_GPU_URL",
    ""
).rstrip("/")

OLLAMA_CPU_URL = os.getenv(
    "OLLAMA_CPU_URL",
    "http://r-core-ollama:11434"
).rstrip("/")


def get_ollama_urls():
    """
    利用するOllamaを優先順で返す。

    1. Windows GPU
    2. Server CPU
    """

    urls = []

    if OLLAMA_GPU_URL:
        urls.append(
            ("gpu", OLLAMA_GPU_URL)
        )

    if (
        OLLAMA_CPU_URL
        and OLLAMA_CPU_URL != OLLAMA_GPU_URL
    ):
        urls.append(
            ("cpu", OLLAMA_CPU_URL)
        )

    return urls


def ollama_post(
    path: str,
    payload: dict,
    timeout: int = 600
):
    """
    OllamaへPOSTする。

    GPU側を優先し、
    接続失敗・HTTPエラー・タイムアウト時は
    CPU側へフォールバックする。

    Returns:
        (response, backend)

        backend:
            "gpu"
            "cpu"
    """

    last_error = None

    for backend, base_url in get_ollama_urls():

        url = f"{base_url}{path}"

        try:
            print(
                f"[ollama] trying "
                f"{backend}: {url}"
            )

            response = requests.post(
                url,
                json=payload,

                # 接続5秒 / 処理本体timeout秒
                timeout=(5, timeout)
            )

            response.raise_for_status()

            print(
                f"[ollama] success: "
                f"{backend}"
            )

            return response, backend

        except requests.RequestException as e:

            last_error = e

            print(
                f"[ollama] failed: "
                f"{backend} "
                f"url={url} "
                f"error={e}"
            )

    if last_error:
        raise last_error

    raise RuntimeError(
        "No Ollama backend configured"
    )


def ollama_get(
    path: str,
    timeout: int = 5
):
    """
    GET用。
    デバッグや状態確認に使用。
    """

    last_error = None

    for backend, base_url in get_ollama_urls():

        url = f"{base_url}{path}"

        try:
            response = requests.get(
                url,
                timeout=(3, timeout)
            )

            response.raise_for_status()

            return response, backend

        except requests.RequestException as e:
            last_error = e

    if last_error:
        raise last_error

    raise RuntimeError(
        "No Ollama backend configured"
    )

def get_available_backend():
    """
    利用可能なOllama backendを返す。

    Returns:
        ("gpu", url)
        または
        ("cpu", url)
    """

    for backend, base_url in get_ollama_urls():

        try:
            response = requests.get(
                f"{base_url}/api/tags",
                timeout=(2, 3)
            )

            response.raise_for_status()

            return backend, base_url

        except requests.RequestException:
            continue

    raise RuntimeError(
        "No Ollama backend available"
    )