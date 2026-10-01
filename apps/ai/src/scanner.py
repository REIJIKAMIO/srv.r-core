from pathlib import Path
import hashlib
import json

from suggester import suggest_from_doc


DOCS_DIR = Path("/home/docs")
STATE_FILE = Path("/var/lib/ai/docs-state.json")


def file_hash(path: Path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)

    return h.hexdigest()


def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )
    except Exception:
        return {}


def save_state(state):
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


def scan_docs(limit: int | None = None):
    state = load_state()

    processed = []
    skipped = []
    errors = []

    for path in sorted(DOCS_DIR.rglob("*.md")):

        if limit is not None and len(processed) >= limit:
            break

        relative_path = str(
            path.relative_to(DOCS_DIR)
        )

        current_hash = file_hash(path)

        if state.get(relative_path) == current_hash:
            skipped.append(relative_path)
            continue

        try:
            result = suggest_from_doc(relative_path)

            processed.append({
                "path": relative_path,
                "result": result
            })

            state[relative_path] = current_hash
            save_state(state)

        except Exception as e:
            errors.append({
                "path": relative_path,
                "error": str(e)
            })

    return {
        "status": "ok",
        "processed_count": len(processed),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "processed": processed,
        "errors": errors
    }