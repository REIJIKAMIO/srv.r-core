from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse
import hashlib
import os
import requests
import yaml
from recommendation import (
    create_recommendation
)

from bs4 import BeautifulSoup

from ollama_client import ollama_post


SOURCES_FILE = Path("/app/sources.yaml")
KNOWLEDGE_DIR = Path("/home/knowledge")

SUMMARY_MODEL = os.getenv(
    "REI_NORMAL_MODEL",
    "qwen2.5:1.5b"
)


def load_sources():
    if not SOURCES_FILE.exists():
        return []

    data = yaml.safe_load(
        SOURCES_FILE.read_text(
            encoding="utf-8"
        )
    )

    return data.get("sources", [])


def make_id(url: str):
    return hashlib.sha256(
        url.encode("utf-8")
    ).hexdigest()[:16]


def fetch_html(url: str):
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "REI-RCORE/1.0"
        }
    )

    response.raise_for_status()

    return response.text


def extract_text(html: str):
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    for tag in soup([
        "script",
        "style",
        "noscript",
        "nav",
        "footer",
        "header",
        "form",
        "svg",
        "aside"
    ]):
        tag.decompose()

    # article / main があれば優先
    main = (
        soup.find("article")
        or soup.find("main")
        or soup.body
        or soup
    )

    text = main.get_text(
        separator="\n",
        strip=True
    )

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return "\n".join(lines)


def extract_title(html: str):
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # og:title 優先
    og_title = soup.find(
        "meta",
        property="og:title"
    )

    if og_title and og_title.get("content"):
        return og_title["content"].strip()

    if soup.title and soup.title.string:
        return soup.title.string.strip()

    h1 = soup.find("h1")

    if h1:
        return h1.get_text(
            " ",
            strip=True
        )

    return "Untitled"


def extract_published_at(html: str):
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidates = [
        ("meta", {
            "property":
                "article:published_time"
        }),
        ("meta", {
            "name":
                "date"
        }),
        ("meta", {
            "name":
                "publish-date"
        }),
    ]

    for tag_name, attrs in candidates:
        tag = soup.find(
            tag_name,
            attrs=attrs
        )

        if tag and tag.get("content"):
            return tag["content"].strip()

    time_tag = soup.find("time")

    if time_tag:
        return (
            time_tag.get("datetime")
            or time_tag.get_text(
                " ",
                strip=True
            )
        )

    return ""


def is_same_domain(base_url: str, url: str):
    return (
        urlparse(base_url).netloc
        ==
        urlparse(url).netloc
    )


def extract_article_links(
    index_url: str,
    html: str
):
    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    links = []

    for a in soup.find_all(
        "a",
        href=True
    ):
        href = a["href"].strip()

        if not href:
            continue

        url = urljoin(
            index_url,
            href
        )

        parsed = urlparse(url)

        if parsed.scheme not in (
            "http",
            "https"
        ):
            continue

        if not is_same_domain(
            index_url,
            url
        ):
            continue

        # フラグメント除去
        url = url.split("#")[0]

        # トップページ自身は除外
        if (
            url.rstrip("/")
            ==
            index_url.rstrip("/")
        ):
            continue

        # 明らかに記事ではないページを除外
        excluded = [
            "/category/",
            "/tag/",
            "/author/",
            "/about",
            "/contact",
            "/privacy",
            "/terms",
            "/login",
            "/signup",
            "/search",
        ]

        if any(
            word in url
            for word in excluded
        ):
            continue

        links.append(url)

    # 重複除去
    return list(
        dict.fromkeys(links)
    )


def summarize_article(
    source_name: str,
    title: str,
    url: str,
    content: str
):
    prompt = f"""
以下はWebサイトの記事本文です。

これはユーザー入力ではありません。

REIのknowledgeとして保存するため、
本文に明示されている内容だけを
日本語で整理してください。

重要:
- 原文にない情報を追加しない
- 推測や補完をしない
- 本文に書かれている事実を優先する
- 日付、人名、商品名、場所、価格は特に厳密に扱う
- 不明な情報は書かない
- 広告、ナビゲーション、UI文言は無視する
- 要約処理そのものについて説明しない
- URLや参照日は別途メタデータに保存される
- Markdown形式で記述する
- 情報が少ない場合は無理に膨らませない
- 原文全文の転載はせず、要点を整理する

情報源:
{source_name}

記事タイトル:
{title}

URL:
{url}

--- article ---

{content[:24000]}

--- end ---
"""

    response, backend = ollama_post(
        "/api/chat",
        payload={
            "model": SUMMARY_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "あなたはREIです。"
                        "外部の記事を読み、"
                        "長期参照用のknowledgeとして"
                        "正確に整理します。"
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "think": False,
            "options": {
                "num_predict": 1024
            }
        },
        timeout=600
    )

    return (
        response.json()
        ["message"]
        ["content"],
        backend
    )


def save_article(
    source_name: str,
    category: str,
    url: str,
    title: str,
    summary: str,
    published_at: str
):
    directory = (
        KNOWLEDGE_DIR
        / category
    )

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    article_id = make_id(url)

    path = (
        directory
        / f"{article_id}.md"
    )

    now = datetime.now()

    content = f"""---
title: {title}
source_name: {source_name}
source_url: {url}
accessed_at: {now.isoformat()}
published_at: {published_at}
category: {category}
---

# {title}

{summary}
"""

    path.write_text(
        content,
        encoding="utf-8"
    )

    return path


def article_already_exists(
    category: str,
    url: str
):
    article_id = make_id(url)

    path = (
        KNOWLEDGE_DIR
        / category
        / f"{article_id}.md"
    )

    return path.exists()


def collect_index_source(
    source: dict
):
    name = source["name"]
    index_url = source["url"]

    category = source.get(
        "category",
        "uncategorized"
    )

    max_articles = source.get(
        "max_articles",
        5
    )

    index_html = fetch_html(
        index_url
    )

    links = extract_article_links(
        index_url,
        index_html
    )

    results = []
    errors = []

    processed = 0

    for url in links:

        if processed >= max_articles:
            break

        # 既に取得済みならスキップ
        if article_already_exists(
            category,
            url
        ):
            continue

        try:
            html = fetch_html(url)

            title = extract_title(
                html
            )

            published_at = (
                extract_published_at(
                    html
                )
            )

            text = extract_text(
                html
            )

            # あまりにも短ければ
            # 記事ページではないとみなす
            if len(text) < 300:
                continue

            summary, backend = (
                summarize_article(
                    name,
                    title,
                    url,
                    text
                )
            )

            path = save_article(
                source_name=name,
                category=category,
                url=url,
                title=title,
                summary=summary,
                published_at=published_at
            )

            recommendation = (
                create_recommendation(
                    title=title,
                    url=url,
                    summary=summary,
                    source_name=name,
                    knowledge_path=str(
                        path.relative_to(
                            KNOWLEDGE_DIR
                        )
                    )
                )
            )

            results.append({
                "title": title,
                "url": url,
                "path": str(
                    path.relative_to(
                        KNOWLEDGE_DIR
                    )
                ),
                "backend": backend,
                "recommendation":
                    recommendation
            })

            processed += 1

        except Exception as e:
            errors.append({
                "url": url,
                "error": str(e)
            })

    return {
        "source": name,
        "status": "ok",
        "collected_count":
            len(results),
        "error_count":
            len(errors),
        "results":
            results,
        "errors":
            errors
    }


def collect_source(source: dict):
    mode = source.get(
        "mode",
        "page"
    )

    if mode == "index":
        return collect_index_source(
            source
        )

    raise ValueError(
        f"Unknown collection mode: {mode}"
    )


def collect_all():
    sources = load_sources()

    results = []
    errors = []

    for source in sources:
        try:
            results.append(
                collect_source(source)
            )

        except Exception as e:
            errors.append({
                "name": source.get(
                    "name",
                    "unknown"
                ),
                "error": str(e)
            })

    return {
        "status": "ok",
        "sources":
            len(sources),
        "results":
            results,
        "errors":
            errors
    }