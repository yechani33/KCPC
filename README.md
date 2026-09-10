# cincinnatikcpc.com

신시내티 중앙장로교회 · Korean Central Presbyterian Church of Cincinnati

The church website. Plain HTML and CSS — **no build step, no framework, no npm.**
Edit a file, push it, and it's live in about a minute.

---

## How the site is organised

```
index.html              홈 · Home
staff/index.html        환영인사 · Welcome (담임목사 인사 & 소개)
portrait/index.html     자화상 · Portrait
vision/index.html       비전 · Vision
credo/index.html        고백 · Credo
venue/index.html        공간소개 · Venue
education/index.html    다음세대 교육철학 · Educational Philosophy
children/index.html     어린이부 · Children
youth/index.html        청소년부 · Youth
youngadult/index.html   청년부 · Young Adult
discipleship/index.html 장년 신앙훈련 · Discipleship
k-school/index.html     도토리 한글학교 · Korean School
football/index.html     도토리 축구교실 · Kids Football
time/index.html         모임 안내 & 오시는 길 · Gatherings & Directions
404.html                주소가 잘못되었을 때 보이는 페이지

assets/css/site.css     모든 디자인 (색, 글꼴, 여백, 반응형)
assets/js/site.js       메뉴 열고 닫기만 담당
assets/img/             사이트에서 쓰는 이미지
assets/img/extra/       지금은 안 쓰지만 보관 중인 이미지
tools/update_sermon.py  주일설교 자동 갱신 스크립트
tools/set_site_url.rb   사이트 주소 변경 (GitHub 주소 <-> 도메인)
```

The folder names match the old Wix addresses on purpose — `/staff`, `/time`, `/k-school`
and the rest all still work, so existing links and Google search results don't break.

### Why every page repeats the header and footer

Each page is a complete, standalone HTML file. That means no build tooling and nothing
to "compile" — but it also means the navigation menu appears in all 15 files. If you
change the menu, change it everywhere. Ask Claude to do it and it will update all of
them in one pass.

---

## Editing the site

Open the folder in VS Code and edit the HTML directly, or just tell Claude what you want
changed. Text is bilingual by convention: Korean first, then the English line right
underneath in `<p class="en">`.

### Preview your changes before pushing

```bash
cd ~/cincinnatikcpc
ruby -run -e httpd . -p 8123
```

Then open **http://localhost:8123** in your browser.

> Use `localhost`, not `127.0.0.1` — YouTube refuses to play embedded videos on
> `127.0.0.1`, so the sermon box will look broken for no reason.

Press `Ctrl+C` in the terminal to stop the server.

### Publishing

```bash
git add -A
git commit -m "무엇을 바꿨는지 적기"
git push
```

GitHub Pages rebuilds automatically. Changes are usually live within a minute.

---

## 주일설교 자동 갱신 · Automatic sermon updates

The homepage sermon video updates itself. A GitHub Action
(`.github/workflows/update-sermon.yml`) runs **every day at 12:00 UTC**, reads the church
YouTube channel's public feed, and rewrites the block between the `SERMON:START` and
`SERMON:END` markers in `index.html` with the newest video. If nothing new was posted, it
does nothing.

Nobody has to touch the site each week.

**To run it right now** instead of waiting: go to the repo's **Actions** tab →
*Update Sunday sermon* → **Run workflow**. Or locally:

```bash
python3 tools/update_sermon.py
```

**Heads up:** it picks whatever video was uploaded most recently. Right now the channel's
newest uploads are the *KINGDOM 청년 주일 4부 예배*, so that's what shows on the homepage.
If you'd rather pin it to a specific service, put those services in their own YouTube
playlist and change `CHANNEL_ID`/`FEED` at the top of `tools/update_sermon.py` to use
`?playlist_id=...` instead.

Don't hand-edit the region between the `SERMON:` markers — the next run overwrites it.

---

## Deployment

- **Hosting:** GitHub Pages, serving the `main` branch from the repository root.
- **Current address:** <https://yechani33.github.io/KCPC/>
- **Domain:** `www.cincinnatikcpc.com` is not connected yet. See `DEPLOY.md` — it is a
  one-time DNS change at GoDaddy plus `ruby tools/set_site_url.rb`, and the site keeps
  working at the GitHub address until you do it.
- **Paths are relative, deliberately.** That is what lets the same files work both at
  `yechani33.github.io/KCPC/` and at the root of a real domain. If you add a link or an
  image by hand, write `../assets/img/x.jpg` from a section page and `assets/img/x.jpg`
  from the homepage — never a leading `/`.
- `.nojekyll` tells GitHub Pages to publish the files as-is rather than running them
  through Jekyll.

---

## Images

Photos came off the old Wix site and were resized to a maximum of 1800px, with the
largest ones converted to WebP. To add a photo, drop it in `assets/img/` and reference it
without a leading slash — `assets/img/your-file.jpg` from the homepage,
`../assets/img/your-file.jpg` from a section page. Keep files under roughly 500KB so
pages stay fast.

Anything in `assets/img/extra/` is kept from the old site but unused — spare photos and
video thumbnails you can pull from later.
