#!/usr/bin/env python3
"""Cache publisher thumbnail URLs for the static site.

Binary assets are not committed in this repository.  This script reads
content/press.md, visits each article, extracts the publisher-provided social
image URL (Open Graph, Twitter card or common link metadata), and writes
content/press-thumbnails.json so the press carousel uses real newspaper images
instead of generated placeholders.
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PRESS_MD = ROOT / "content" / "press.md"
OUT_JSON = ROOT / "content" / "press-thumbnails.json"
TIMEOUT = 25
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
IMAGE_META_KEYS = {
    "og:image",
    "og:image:url",
    "og:image:secure_url",
    "twitter:image",
    "twitter:image:src",
    "thumbnail",
}
IMAGE_LINK_RELS = {"image_src", "preload"}


class ImageMetadataParser(HTMLParser):
    """Collect publisher-declared image URLs from an article document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images: list[str] = []
        # Some sites emit Open Graph tags before a formal <head> tag.
        self._in_head = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): (v or "").strip() for k, v in attrs}
        tag = tag.lower()
        if tag == "head":
            self._in_head = True
            return
        if tag == "body":
            self._in_head = False
            return
        if not self._in_head:
            return
        if tag == "meta":
            key = (attrs_dict.get("property") or attrs_dict.get("name") or attrs_dict.get("itemprop") or "").lower()
            content = attrs_dict.get("content", "")
            if key in IMAGE_META_KEYS and content:
                self.images.append(content)
        elif tag == "link":
            rels = {rel.lower() for rel in attrs_dict.get("rel", "").split()}
            href = attrs_dict.get("href", "")
            as_attr = attrs_dict.get("as", "").lower()
            if href and (rels & IMAGE_LINK_RELS) and (as_attr in {"", "image"}):
                self.images.append(href)


def parse_press() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in PRESS_MD.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("#### "):
            if current:
                items.append(current)
            current = {"title": line.replace("####", "", 1).strip().strip('“”'), "url": ""}
            continue
        if not current or not line.startswith("- "):
            continue
        value = line[2:]
        key, sep, rest = value.partition(":")
        if sep and key.lower().strip() == "url":
            current["url"] = rest.strip()
    if current:
        items.append(current)
    return items


def fetch_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    with urlopen(req, timeout=TIMEOUT) as response:
        return response.read().decode("utf-8", errors="ignore")


def extract_image_urls(article_url: str) -> list[str]:
    parser = ImageMetadataParser()
    parser.feed(fetch_text(article_url)[:500_000])
    seen: set[str] = set()
    urls: list[str] = []
    for image_url in parser.images:
        absolute = urljoin(article_url, image_url.strip())
        if absolute and absolute not in seen:
            seen.add(absolute)
            urls.append(absolute)
    return urls


def microlink_image_urls(article_url: str) -> list[str]:
    api_url = "https://api.microlink.io/?" + urlencode({"url": article_url})
    try:
        payload = json.loads(fetch_text(api_url))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return []
    image_url = payload.get("data", {}).get("image", {}).get("url", "")
    return [image_url] if image_url else []


def candidate_image_urls(article_url: str) -> list[str]:
    try:
        direct_urls = extract_image_urls(article_url)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        print(f"WARN article failed: {article_url} ({exc})", file=sys.stderr)
        direct_urls = []
    seen: set[str] = set()
    urls: list[str] = []
    for image_url in [*direct_urls, *microlink_image_urls(article_url)]:
        if image_url and image_url not in seen:
            seen.add(image_url)
            urls.append(image_url)
    return urls


def main() -> None:
    previous_mapping: dict[str, str] = {}
    if OUT_JSON.exists():
        previous_mapping = json.loads(OUT_JSON.read_text(encoding="utf-8"))

    mapping: dict[str, str] = {}
    failures: list[str] = []
    for idx, item in enumerate(parse_press(), start=1):
        if not item.get("url"):
            continue
        candidates = candidate_image_urls(item["url"])
        if candidates:
            mapping[item["url"]] = candidates[0]
            print(f"cached {idx:02d}: {candidates[0]}")
            continue
        previous = previous_mapping.get(item["url"], "")
        if previous and re.match(r"https?://", previous):
            mapping[item["url"]] = previous
            print(f"kept {idx:02d}: {previous}")
            continue
        failures.append(item["url"])
        print(f"WARN no publisher thumbnail found: {item['url']}", file=sys.stderr)

    OUT_JSON.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Cached {len(mapping)} publisher thumbnail URLs in {OUT_JSON.relative_to(ROOT)}")
    if failures:
        print(f"Failed to cache {len(failures)} thumbnail URLs", file=sys.stderr)


if __name__ == "__main__":
    main()
