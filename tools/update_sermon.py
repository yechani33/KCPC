#!/usr/bin/env python3
"""Refresh the homepage sermon block from the church YouTube channel.

Reads the channel's public RSS feed, takes the newest video, and rewrites the
region of index.html between the SERMON:START and SERMON:END markers.

Run it any time — it only touches index.html when the video actually changed:

    python3 tools/update_sermon.py

GitHub Actions runs this daily (see .github/workflows/update-sermon.yml).
"""

from __future__ import annotations

import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

CHANNEL_ID = "UC-Olyp21hkfR_vJuafZgI1A"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
CHANNEL_URL = "https://www.youtube.com/@KCPC_of_Cincinnati"

INDEX = Path(__file__).resolve().parent.parent / "index.html"

START = "<!-- SERMON:START"
END = "<!-- SERMON:END -->"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def latest_video() -> tuple[str, str, str]:
    """Return (video_id, title, published_iso) for the newest upload."""
    req = urllib.request.Request(
        FEED, headers={"User-Agent": "cincinnatikcpc.com sermon updater"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        feed = ET.parse(resp)

    entry = feed.find("atom:entry", NS)
    if entry is None:
        raise SystemExit("No videos found in the channel feed.")

    video_id = entry.findtext("yt:videoId", namespaces=NS)
    title = (entry.findtext("atom:title", namespaces=NS) or "").strip()
    published = entry.findtext("atom:published", namespaces=NS) or ""

    if not video_id:
        raise SystemExit("Feed entry had no video id.")
    return video_id, title, published


def korean_date(published: str) -> str:
    try:
        dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
    except ValueError:
        return ""
    return f"{dt.year}년 {dt.month}월 {dt.day}일"


def build_block(video_id: str, title: str, published: str) -> str:
    safe_title = html.escape(title, quote=True)
    date_text = korean_date(published)

    return f"""<!-- SERMON:START — 이 영역은 GitHub Actions가 매일 자동으로 갱신합니다. 직접 수정하지 마세요. -->
        <div class="video">
          <iframe
            src="https://www.youtube-nocookie.com/embed/{video_id}"
            title="{safe_title}"
            loading="lazy"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            referrerpolicy="strict-origin-when-cross-origin"
            allowfullscreen></iframe>
        </div>
        <div class="sermon__meta">
          <div>
            <p class="sermon__title">{safe_title}</p>
            <p class="sermon__date">{date_text}</p>
          </div>
          <a class="btn btn--ghost" href="{CHANNEL_URL}" target="_blank" rel="noopener">유튜브 채널 전체 보기</a>
        </div>
        {END}"""


def main() -> int:
    video_id, title, published = latest_video()

    source = INDEX.read_text(encoding="utf-8")

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(source):
        print(f"error: could not find the sermon markers in {INDEX}", file=sys.stderr)
        return 1

    # A plain replace would eat backslashes and \g in the title.
    updated = pattern.sub(lambda _m: build_block(video_id, title, published), source, count=1)

    if updated == source:
        print(f"unchanged — latest sermon is still {video_id}")
        return 0

    INDEX.write_text(updated, encoding="utf-8")
    print(f"updated to {video_id} — {title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
