#!/usr/bin/env python3
"""Generate lightweight local press thumbnails for the static site.

The site is served as static files, so browsers should not call third-party
newspaper pages or metadata services while rendering the press carousel. This
script reads content/press.md and creates small SVG thumbnails plus a JSON URL
map that can be committed and served from GitHub Pages.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PRESS_MD = ROOT / "content" / "press.md"
OUT_DIR = ROOT / "images" / "press-thumbnails"
OUT_JSON = ROOT / "content" / "press-thumbnails.json"

PALETTES = [
    ("#0f5132", "#d1e7dd", "#ffffff"),
    ("#1a6b2f", "#e8f5e9", "#ffffff"),
    ("#14532d", "#bbf7d0", "#ffffff"),
    ("#166534", "#dcfce7", "#ffffff"),
    ("#365314", "#ecfccb", "#ffffff"),
]


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:64] or "press"


def wrap(text: str, width: int, max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and words:
        consumed = " ".join(lines)
        if len(consumed) < len(text):
            lines[-1] = lines[-1].rstrip(".,;:") + "…"
    return lines


def parse_press() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in PRESS_MD.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("#### "):
            if current:
                items.append(current)
            current = {"title": line.replace("####", "", 1).strip().strip('“”'), "date": "", "url": ""}
            continue
        if not current or not line.startswith("- "):
            continue
        value = line[2:]
        key, sep, rest = value.partition(":")
        if not sep:
            continue
        key = key.lower().strip()
        if key in {"fecha", "url"}:
            current["date" if key == "fecha" else "url"] = rest.strip()
    if current:
        items.append(current)
    return items


def make_svg(item: dict[str, str], idx: int) -> str:
    host = urlparse(item["url"]).netloc.replace("www.", "") or "noticia"
    digest = hashlib.sha1(item["url"].encode("utf-8")).hexdigest()
    dark, light, white = PALETTES[int(digest[:2], 16) % len(PALETTES)]
    title_lines = wrap(item["title"], 34, 3)
    title_tspans = "".join(
        f'<tspan x="32" dy="{0 if i == 0 else 30}">{html.escape(line)}</tspan>'
        for i, line in enumerate(title_lines)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360" role="img" aria-label="Miniatura de prensa: {html.escape(item['title'])}">
  <defs>
    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="{light}"/>
      <stop offset="1" stop-color="#ffffff"/>
    </linearGradient>
  </defs>
  <rect width="640" height="360" rx="28" fill="url(#g)"/>
  <circle cx="566" cy="70" r="82" fill="{dark}" opacity=".12"/>
  <circle cx="76" cy="318" r="108" fill="{dark}" opacity=".10"/>
  <rect x="32" y="32" width="180" height="40" rx="20" fill="{dark}" opacity=".95"/>
  <text x="122" y="58" text-anchor="middle" font-family="Ubuntu, Arial, sans-serif" font-size="18" font-weight="700" fill="{white}">PRESS</text>
  <text x="32" y="118" font-family="Ubuntu, Arial, sans-serif" font-size="26" font-weight="700" fill="#1a3a1f">{title_tspans}</text>
  <text x="32" y="286" font-family="Ubuntu, Arial, sans-serif" font-size="18" font-weight="600" fill="{dark}">{html.escape(host)}</text>
  <text x="32" y="316" font-family="Ubuntu, Arial, sans-serif" font-size="16" fill="#486a4d">{html.escape(item.get('date', ''))}</text>
</svg>'''


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}
    for idx, item in enumerate(parse_press(), start=1):
        if not item.get("url"):
            continue
        digest = hashlib.sha1(item["url"].encode("utf-8")).hexdigest()[:10]
        filename = f"{idx:02d}-{slugify(urlparse(item['url']).netloc)}-{digest}.svg"
        path = OUT_DIR / filename
        path.write_text(make_svg(item, idx), encoding="utf-8")
        mapping[item["url"]] = f"images/press-thumbnails/{filename}"
    OUT_JSON.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(mapping)} thumbnails in {OUT_DIR.relative_to(ROOT)}")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
