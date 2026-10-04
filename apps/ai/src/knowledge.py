from pathlib import Path


SOURCE_DIRS = {
    "docs": Path("/home/docs"),
    "knowledge": Path("/home/knowledge"),
    "canon": Path("/home/canon"),
}


def load_markdown_files():
    """
    docs / knowledge / canon 配下のMarkdownファイルをすべて読み込む。

    Returns:
        [
            {
                "source_type": "docs",
                "path": "00_Journal/example.md",
                "text": "...Markdown本文..."
            },
            ...
        ]
    """

    files = []

    for source_type, base_dir in SOURCE_DIRS.items():

        if not base_dir.exists():
            continue

        for path in sorted(base_dir.rglob("*.md")):

            try:
                text = path.read_text(encoding="utf-8")

            except Exception as e:
                print(
                    f"[knowledge] failed to read: {path} "
                    f"error={e}"
                )
                continue

            files.append({
                "source_type": source_type,
                "path": str(path.relative_to(base_dir)),
                "text": text
            })

    return files


def load_files_by_source(source_type: str):
    """
    指定したsource_typeだけ読み込む。

    例:
        load_files_by_source("docs")
        load_files_by_source("knowledge")
        load_files_by_source("canon")
    """

    if source_type not in SOURCE_DIRS:
        raise ValueError(
            f"Unknown source_type: {source_type}"
        )

    base_dir = SOURCE_DIRS[source_type]

    if not base_dir.exists():
        return []

    files = []

    for path in sorted(base_dir.rglob("*.md")):

        try:
            text = path.read_text(encoding="utf-8")

        except Exception as e:
            print(
                f"[knowledge] failed to read: {path} "
                f"error={e}"
            )
            continue

        files.append({
            "source_type": source_type,
            "path": str(path.relative_to(base_dir)),
            "text": text
        })

    return files


def get_source_directory(source_type: str):
    """
    source_typeに対応するディレクトリを返す。
    """

    if source_type not in SOURCE_DIRS:
        raise ValueError(
            f"Unknown source_type: {source_type}"
        )

    return SOURCE_DIRS[source_type]