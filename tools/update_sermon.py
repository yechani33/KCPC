#!/usr/bin/env python3
"""Refresh the homepage sermon block from the "KCPC 주일설교" playlist.

Takes the newest sermon on the church's YouTube channel and rewrites the region
of index.html between the SERMON:START and SERMON:END markers.

Two sources are combined, because YouTube retired the per-playlist RSS feed:

  * the playlist page tells us which videos belong to "KCPC 주일설교";
  * the channel's Atom feed (still supported) gives full titles and dates.

If the playlist page can't be read, we fall back to the feed alone and pick the
newest video whose title carries the "KCPC 주일설교" tag — every sermon upload
uses it.

Run it any time — it only touches index.html when the video actually changed:

    python3 tools/update_sermon.py

GitHub Actions runs this daily (see .github/workflows/update-sermon.yml).
"""

from __future__ import annotations

import html
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

CHANNEL_ID = "UC_WP9Tjs3qxHDUZSvdESLDg"
PLAYLIST_ID = "PLPLmhoZV7R_3AgKUpLbK2-s_Q8u5PWge6"

FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
PLAYLIST_URL = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"

# Every sermon upload carries this in its title, e.g.
# "09062026 | 로마서 강해(4) | 당신이 그 사람이라 | 주예찬 담임목사 | KCPC 주일설교 | 로마서 2:1-11"
SERMON_TAG = "KCPC 주일설교"

INDEX = Path(__file__).resolve().parent.parent / "index.html"

START = "<!-- SERMON:START"
END = "<!-- SERMON:END -->"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) cincinnatikcpc.com sermon updater"


@dataclass
class Video:
    video_id: str
    title: str
    published: date


def get(url: str, attempts: int = 4) -> bytes:
    """Fetch a URL, retrying a few times.

    YouTube throttles bursts of requests from one address and answers 404 while
    it does, so a failure here is usually worth sleeping off rather than giving
    up on.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.5",
            # Skips the EU consent interstitial that YouTube shows some servers.
            "Cookie": "CONSENT=YES+1",
        },
    )

    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except (urllib.error.URLError, OSError) as exc:
            if attempt == attempts:
                raise
            delay = 5 * 2 ** (attempt - 1)
            print(f"  {url} failed ({exc}); retrying in {delay}s", file=sys.stderr)
            time.sleep(delay)

    raise AssertionError("unreachable")


def channel_videos() -> list[Video]:
    """Newest uploads from the channel feed, most recent first."""
    feed = ET.fromstring(get(FEED))

    videos = []
    for entry in feed.findall("atom:entry", NS):
        video_id = entry.findtext("yt:videoId", namespaces=NS)
        title = (entry.findtext("atom:title", namespaces=NS) or "").strip()
        published = entry.findtext("atom:published", namespaces=NS) or ""
        if not video_id or not title:
            continue
        try:
            when = datetime.fromisoformat(published.replace("Z", "+00:00")).date()
        except ValueError:
            continue
        videos.append(Video(video_id, title, when))

    videos.sort(key=lambda v: v.published, reverse=True)
    return videos


def playlist_video_ids() -> list[str]:
    """Video ids in the sermon playlist. Empty if the page can't be read."""
    try:
        page = get(PLAYLIST_URL + "&hl=ko").decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as exc:
        print(f"warning: could not read the sermon playlist ({exc})", file=sys.stderr)
        return []

    ids = re.findall(
        r'"contentId":"([\w-]{11})","contentType":"LOCKUP_CONTENT_TYPE_VIDEO"', page
    ) or re.findall(
        r'"contentType":"LOCKUP_CONTENT_TYPE_VIDEO","contentId":"([\w-]{11})"', page
    )
    if not ids:
        print("warning: found no videos on the sermon playlist page", file=sys.stderr)
    return ids


def latest_sermon() -> Video:
    videos = channel_videos()
    if not videos:
        raise SystemExit("No videos found in the channel feed.")

    in_playlist = set(playlist_video_ids())
    if in_playlist:
        # Newest by upload date rather than playlist position, so a hand-sorted
        # playlist can't push an old sermon onto the homepage.
        members = [v for v in videos if v.video_id in in_playlist]
        if members:
            return members[0]
        print(
            "warning: no playlist video is recent enough to be in the channel feed; "
            "falling back to the title tag",
            file=sys.stderr,
        )

    tagged = [v for v in videos if SERMON_TAG in v.title]
    if tagged:
        return tagged[0]

    raise SystemExit(f"No recent video is tagged “{SERMON_TAG}”.")


def sermon_date(video: Video) -> date:
    """The service date encoded in the title, e.g. 09062026 or 071226.

    Falls back to the upload date, which runs a few days later.
    """
    for token in re.findall(r"(?<!\d)(\d{8}|\d{6})(?!\d)", video.title):
        month, day = int(token[:2]), int(token[2:4])
        year = int(token[4:]) if len(token) == 8 else 2000 + int(token[4:])
        if not 2000 <= year <= 2100:
            continue
        try:
            return date(year, month, day)
        except ValueError:
            continue
    return video.published


def korean_date(when: date) -> str:
    return f"{when.year}년 {when.month}월 {when.day}일"


def split_title(title: str) -> tuple[str, str, str]:
    """Pull (headline, preacher, scripture) out of the pipe-separated title.

    Returns the whole title as the headline when it doesn't follow the pattern.
    """
    parts = [p.strip() for p in title.split("|") if p.strip()]
    tag = next((i for i, p in enumerate(parts) if SERMON_TAG in p), None)
    if tag is None:
        return title, "", ""

    scripture = " · ".join(parts[tag + 1 :])
    head = parts[:tag]

    preacher = ""
    if head and re.search(r"(목사|전도사|선교사|장로)$", head[-1]):
        preacher = head.pop()

    # head is now [date, (series), 설교제목] — the sermon title is last.
    headline = head[-1] if head else ""
    if not headline or re.search(r"\d{6}", headline):
        return title, "", ""  # couldn't find a clean title; show the raw one
    return headline, preacher, scripture


def build_block(video: Video) -> str:
    headline, preacher, scripture = split_title(video.title)
    meta = " · ".join(
        p for p in (korean_date(sermon_date(video)), scripture, preacher) if p
    )

    return f"""<!-- SERMON:START — 이 영역은 GitHub Actions가 매일 자동으로 갱신합니다. 직접 수정하지 마세요. -->
    <div class="video">
      <iframe
        src="https://www.youtube-nocookie.com/embed/{video.video_id}"
        title="{html.escape(video.title, quote=True)}"
        loading="lazy"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        referrerpolicy="strict-origin-when-cross-origin"
        allowfullscreen></iframe>
    </div>
    <div class="sermon__meta">
      <div>
        <p class="sermon__title">{html.escape(headline)}</p>
        <p class="sermon__date">{html.escape(meta)}</p>
      </div>
      <a class="btn btn--ghost" href="{PLAYLIST_URL}" target="_blank" rel="noopener">지난 설교 전체 보기</a>
    </div>
    {END}"""


def main() -> int:
    video = latest_sermon()

    source = INDEX.read_text(encoding="utf-8")

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(source):
        print(f"error: could not find the sermon markers in {INDEX}", file=sys.stderr)
        return 1

    # A plain replace would eat backslashes and \g in the title.
    updated = pattern.sub(lambda _m: build_block(video), source, count=1)

    if updated == source:
        print(f"unchanged — latest sermon is still {video.video_id}")
        return 0

    INDEX.write_text(updated, encoding="utf-8")
    print(f"updated to {video.video_id} — {video.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
