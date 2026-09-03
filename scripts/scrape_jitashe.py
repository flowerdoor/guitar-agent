"""Fetch the public Jitashe tablature tutorial and save its article body as Markdown."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import httpx


DEFAULT_URL = "https://www.jitashe.org/school/tablature/"
DEFAULT_OUTPUT = Path("data/jitashe_tablature.md")


@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Node | str] = field(default_factory=list)


class ArticleParser(HTMLParser):
    """Build only the requested article subtree, ignoring the rest of the page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root: Node | None = None
        self.stack: list[Node] = []
        self.capturing = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if not self.capturing and attributes.get("id") == "school_tablature":
            self.root = Node(tag, attributes)
            self.stack = [self.root]
            self.capturing = True
            return
        if not self.capturing:
            return
        node = Node(tag, attributes)
        self.stack[-1].children.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if not self.capturing:
            return
        if tag == self.root.tag if self.root else False:
            self.stack = []
            self.capturing = False
            return
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if self.capturing and self.stack:
            self.stack[-1].children.append(data)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value)


def render_inline(node: Node | str, source_url: str) -> str:
    if isinstance(node, str):
        return normalize_text(node)
    if node.tag in {"script", "style", "noscript"}:
        return ""
    if node.tag == "br":
        return "\n"
    if node.tag == "img":
        return ""

    content = "".join(render_inline(child, source_url) for child in node.children)
    if node.tag in {"strong", "b", "em", "i"} and content.strip():
        return f"**{content.strip()}**"
    if node.tag == "a":
        href = urljoin(source_url, node.attrs.get("href", ""))
        text = content.strip()
        if href and not href.lower().startswith("javascript:") and text:
            return f"[{text}]({href})"
        return content
    return content


def render_blocks(node: Node, source_url: str, *, is_root: bool = False) -> list[str]:
    blocks: list[str] = []
    block_tags = {"h1", "h2", "h3", "h4", "p", "blockquote", "pre"}
    for child in node.children:
        if isinstance(child, str):
            continue
        if child.tag in block_tags:
            content = render_inline(child, source_url).strip()
            if not content or (is_root and child.tag == "h1"):
                continue
            if child.tag.startswith("h"):
                level = int(child.tag[1])
                blocks.append(f"{'#' * level} {content}")
            elif child.tag == "blockquote":
                blocks.append("\n".join(f"> {line}" for line in content.splitlines() if line.strip()))
            else:
                blocks.append(content)
        else:
            blocks.extend(render_blocks(child, source_url))
    return blocks


def scrape(url: str) -> tuple[str, str]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; GuitarCoach article importer)"}
    with httpx.Client(follow_redirects=True, timeout=30, headers=headers) as client:
        response = client.get(url)
        response.raise_for_status()
    html = response.content.decode(response.encoding or "utf-8", errors="replace")
    parser = ArticleParser()
    parser.feed(html)
    if parser.root is None:
        raise RuntimeError("Could not find #school_tablature in the downloaded page")
    title = next(
        (render_inline(child, url).strip() for child in parser.root.children if isinstance(child, Node) and child.tag == "h1"),
        "吉他社教程",
    )
    body = "\n\n".join(render_blocks(parser.root, url, is_root=True))
    return title, body


def main() -> None:
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--url", default=DEFAULT_URL)
    argument_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = argument_parser.parse_args()

    title, body = scrape(args.url)
    scraped_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    document = f"# {title}\n\n来源：{args.url}\n抓取时间：{scraped_at}\n\n---\n\n{body}\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document, encoding="utf-8")
    print(f"Saved {len(body)} article characters to {args.output}")


if __name__ == "__main__":
    main()
