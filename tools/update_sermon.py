#!/usr/bin/env python3
"""Refresh the homepage sermon block from the "KCPC 주일설교" playlist.

Takes the newest sermon in the playlist and rewrites the region of index.html
between the SERMON:START and SERMON:END markers.

Why it scrapes: YouTube retired the per-playlist RSS feed, and it now answers
404 for the per-channel feed as well whenever the request comes from a data
centre — including every GitHub Actions runner. The playlist page and the
oEmbed endpoint both still answer, so those are what we use.

Run it any time — it only touches index.html when the video actually changed:

    python3 tools/update_sermon.py

GitHub Actions runs this daily (see .github/workflows/update-sermon.yml).
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

PLAYLIST_ID = "PLPLmhoZV7R_3AgKUpLbK2-s_Q8u5PWge6"
PLAYLIST_URL = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"

# Every sermon upload carries this in its title, e.g.
# "09062026 | 로마서 강해(4) | 당신이 그 사람이라 | 주예찬 담임목사 | KCPC 주일설교 | 로마서 2:1-11"
SERMON_TAG = "KCPC 주일설교"

INDEX = Path(__file__).resolve().parent.parent / "index.html"

START = "<!-- SERMON:START"
END = "<!-- SERMON:END -->"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


@dataclass
class Video:
    video_id: str
    title: str

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"


def get(url: str, attempts: int = 4) -> str:
    """Fetch a URL as text, retrying a few times.

    YouTube throttles bursts from one address and answers 404 while it does, so
    a failure here is usually worth sleeping off rather than giving up on.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            # Korean titles come back in full; the auto-translated English ones
            # get cut off with an ellipsis.
            "Accept-Language": "ko-KR,ko;q=0.9",
            # Skips the EU consent interstitial that YouTube shows some servers.
            "Cookie": "CONSENT=YES+1",
        },
    )

    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", "replace")
        except (urllib.error.URLError, OSError) as exc:
            if attempt == attempts:
                raise
            delay = 5 * 2 ** (attempt - 1)
            print(f"  {url} failed ({exc}); retrying in {delay}s", file=sys.stderr)
            time.sleep(delay)

    raise AssertionError("unreachable")


def playlist_videos() -> list[Video]:
    """Every video on the playlist page, in playlist order."""
    page = get(f"{PLAYLIST_URL}&hl=ko")

    match = re.search(r"var ytInitialData = (\{.*?\});</script>", page, re.DOTALL)
    if match:
        videos = list(walk_lockups(json.loads(match.group(1))))
        if videos:
            return videos

    # The embedded JSON moves around from time to time; the ids alone are enough
    # to carry on, since oEmbed can supply the titles.
    ids = re.findall(
        r'"contentId":"([\w-]{11})","contentType":"LOCKUP_CONTENT_TYPE_VIDEO"', page
    ) or re.findall(
        r'"contentType":"LOCKUP_CONTENT_TYPE_VIDEO","contentId":"([\w-]{11})"', page
    )
    if not ids:
        raise SystemExit("Found no videos on the sermon playlist page.")

    print("warning: read only video ids from the playlist page", file=sys.stderr)
    return [Video(video_id, "") for video_id in dict.fromkeys(ids)]


def walk_lockups(node: object) -> "list[Video]":
    """Collect the video entries out of YouTube's ytInitialData blob."""
    found: list[Video] = []
    seen: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            lockup = node.get("lockupViewModel")
            if (
                isinstance(lockup, dict)
                and lockup.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO"
            ):
                video_id = lockup.get("contentId")
                title = ""
                try:
                    title = lockup["metadata"]["lockupMetadataViewModel"]["title"][
                        "content"
                    ]
                except (KeyError, TypeError):
                    pass
                if video_id and video_id not in seen:
                    seen.add(video_id)
                    found.append(Video(video_id, title.strip()))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(node)
    return found


def full_title(video: Video) -> str:
    """The complete title, asking oEmbed when the playpage page clipped it."""
    if video.title and not video.title.endswith(("...", "…")):
        return video.title

    query = urllib.parse.urlencode({"url": video.url, "format": "json"})
    try:
        return json.loads(get(f"https://www.youtube.com/oembed?{query}"))["title"].strip()
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        print(f"warning: oEmbed failed for {video.video_id} ({exc})", file=sys.stderr)
        return video.title


def sermon_date(title: str) -> date | None:
    """The service date encoded in the title, e.g. 09062026 or 071226."""
    cutoff = date.today() + timedelta(days=7)
    for token in re.findall(r"(?<!\d)(\d{8}|\d{6})(?!\d)", title):
        month, day = int(token[:2]), int(token[2:4])
        year = int(token[4:]) if len(token) == 8 else 2000 + int(token[4:])
        try:
            when = date(year, month, day)
        except ValueError:
            continue
        # A typo in the title shouldn't be able to pin a stale sermon to the top.
        if date(2000, 1, 1) <= when <= cutoff:
            return when
    return None


def latest_sermon() -> tuple[Video, date | None]:
    videos = playlist_videos()

    # The playlist is kept newest-first, but it's hand-ordered, so prefer the
    # service date in the title and keep playlist position only as a tiebreak.
    resolved = [Video(v.video_id, full_title(v)) for v in videos[:12]]

    sermons = [v for v in resolved if SERMON_TAG in v.title] or resolved
    dated = [(sermon_date(v.title), i, v) for i, v in enumerate(sermons)]
    dated = [(d, i, v) for d, i, v in dated if d is not None]

    if dated:
        when, _, video = max(dated, key=lambda row: row[0])
        return video, when

    print("warning: no title carried a service date; using playlist order", file=sys.stderr)
    return sermons[0], None


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


def build_block(video: Video, when: date | None) -> str:
    headline, preacher, scripture = split_title(video.title)
    meta = " · ".join(
        p
        for p in (korean_date(when) if when else "", scripture, preacher)
        if p
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
    video, when = latest_sermon()

    source = INDEX.read_text(encoding="utf-8")

    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(source):
        print(f"error: could not find the sermon markers in {INDEX}", file=sys.stderr)
        return 1

    # A plain replace would eat backslashes and \g in the title.
    updated = pattern.sub(lambda _m: build_block(video, when), source, count=1)

    if updated == source:
        print(f"unchanged — latest sermon is still {video.video_id}")
        return 0

    INDEX.write_text(updated, encoding="utf-8")
    print(f"updated to {video.video_id} — {video.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
