from pathlib import Path

KNOWLEDGE_DIR = Path("/home/knowledge")


def load_markdown_files():
    files = []

    for path in KNOWLEDGE_DIR.rglob("*.md"):
        text = path.read_text(encoding="utf-8")

        files.append({
            "path": str(path.relative_to(KNOWLEDGE_DIR)),
            "text": text
        })

    return files