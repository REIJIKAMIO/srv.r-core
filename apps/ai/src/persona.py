from pathlib import Path


PERSONA_DIR = Path("/home/canon/personas")


def load_persona_core(persona_name: str) -> str:
    """
    指定したpersonaのcore.mdを読み込む。

    例:
        load_persona_core("rei")
    """

    path = PERSONA_DIR / persona_name / "core.md"

    if not path.exists():
        return ""

    try:
        return path.read_text(
            encoding="utf-8"
        )

    except Exception as e:
        print(
            f"[persona] failed to read: {path} "
            f"error={e}"
        )

        return ""