from pathlib import Path
from datetime import datetime
import uuid
import json

STATE_FILE = Path(
    "/var/lib/ai/persona-state.json"
)

MEMORY_DIR = Path("/home/memory/personas")


def get_persona_memory_dir(subject: str) -> Path:
    return MEMORY_DIR / subject


def save_observation(
    subject: str,
    content: str,
    source_type: str,
    source_ref: str = ""
):
    """
    人物についての個別観察を保存する。
    """

    base_dir = get_persona_memory_dir(subject)
    observations_dir = base_dir / "observations"

    observations_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    observation_id = (
        datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_"
        + uuid.uuid4().hex[:6]
    )

    path = observations_dir / f"{observation_id}.md"

    text = f"""---
id: {observation_id}
subject: {subject}
source_type: {source_type}
source_ref: {source_ref}
created: {datetime.now().isoformat()}
---

{content}
"""

    path.write_text(
        text,
        encoding="utf-8"
    )

    return {
        "status": "ok",
        "id": observation_id,
        "subject": subject,
        "path": str(path)
    }


def load_observations(subject: str):
    """
    指定人物についての観察をすべて読み込む。
    """

    observations_dir = (
        get_persona_memory_dir(subject)
        / "observations"
    )

    if not observations_dir.exists():
        return []

    observations = []

    for path in sorted(
        observations_dir.glob("*.md")
    ):
        try:
            text = path.read_text(
                encoding="utf-8"
            )

            observations.append({
                "path": path.name,
                "text": text
            })

        except Exception as e:
            print(
                f"[memory] failed to read "
                f"{path}: {e}"
            )

    return observations


def load_inferred_persona(subject: str):
    path = (
        get_persona_memory_dir(subject)
        / "inferred.md"
    )

    if not path.exists():
        return ""

    return path.read_text(
        encoding="utf-8"
    )


def save_inferred_persona(
    subject: str,
    content: str
):
    base_dir = get_persona_memory_dir(subject)

    base_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    path = base_dir / "inferred.md"

    path.write_text(
        content,
        encoding="utf-8"
    )

    return {
        "status": "ok",
        "subject": subject,
        "path": str(path)
    }


def count_observations(subject: str) -> int:
    observations_dir = (
        get_persona_memory_dir(subject)
        / "observations"
    )

    if not observations_dir.exists():
        return 0

    return len(
        list(
            observations_dir.glob("*.md")
        )
    )

#
# inferred count
#
def load_persona_state():
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(
            STATE_FILE.read_text(
                encoding="utf-8"
            )
        )
    except Exception as e:
        print(
            f"[memory] failed to load state: {e}"
        )
        return {}


def save_persona_state(state):
    STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    STATE_FILE.write_text(
        json.dumps(
            state,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def get_last_inferred_count(
    subject: str
) -> int:
    state = load_persona_state()

    return (
        state
        .get(subject, {})
        .get("last_inferred_count", 0)
    )


def set_last_inferred_count(
    subject: str,
    count: int
):
    state = load_persona_state()

    if subject not in state:
        state[subject] = {}

    state[subject][
        "last_inferred_count"
    ] = count

    save_persona_state(state)

def load_observations_since(
    subject: str,
    start_index: int = 0
):
    """
    start_index以降のobservationだけ読み込む。
    ファイル名順を処理順として扱う。
    """

    observations_dir = (
        get_persona_memory_dir(subject)
        / "observations"
    )

    if not observations_dir.exists():
        return []

    paths = sorted(
        observations_dir.glob("*.md")
    )

    paths = paths[start_index:]

    observations = []

    for path in paths:
        try:
            text = path.read_text(
                encoding="utf-8"
            )

            observations.append({
                "path": path.name,
                "text": text
            })

        except Exception as e:
            print(
                f"[memory] failed to read "
                f"{path}: {e}"
            )

    return observations