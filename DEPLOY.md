# Deploying

The site is hosted free on GitHub Pages. Publishing is `git push` — nothing else.

There are two phases. **Phase 1** puts the site online right now at a GitHub address,
with no domain work and no cost. **Phase 2**, whenever you're ready, moves it onto
`www.cincinnatikcpc.com`.

---

# Phase 1 — live at the GitHub address

## Turn on GitHub Pages

Go to <https://github.com/yechani33/KCPC/settings/pages>

- **Source:** Deploy from a branch
- **Branch:** `main`, folder `/ (root)`
- **Save**

Wait a minute or two — the **Actions** tab shows the build running. Then the site is live at:

**<https://yechani33.github.io/KCPC/>**

That's it. HTTPS is automatic, there's no bill, and nothing about your domain or your
current Wix site is touched.

## Making changes after that

```bash
cd ~/cincinnatikcpc
# edit files, or ask Claude to
git add -A
git commit -m "무엇을 바꿨는지 적기"
git push
```

Live in about a minute.

---

# Phase 2 — move onto cincinnatikcpc.com

Do this whenever you want. Until then Phase 1 keeps working, and your Wix site keeps
serving the real domain, so nothing breaks in the meantime.

The domain is registered at **GoDaddy** and uses GoDaddy's nameservers. GitHub has no DNS
service of its own, so the records have to change there. It is a one-time job — after this
you never log into GoDaddy again.

## Step 1 — repoint the site URL

```bash
cd ~/cincinnatikcpc
ruby tools/set_site_url.rb https://www.cincinnatikcpc.com
printf 'www.cincinnatikcpc.com\n' > CNAME
git add -A
git commit -m "Switch site to the cincinnatikcpc.com domain"
git push
```

The script updates the canonical tags, Open Graph URLs, `sitemap.xml`, `robots.txt`, and
the `<base>` tag on `404.html`. Page links and images are all relative, so they need no
changes and work at either address.

The `CNAME` file is what tells GitHub Pages which domain to answer on. It must contain
exactly `www.cincinnatikcpc.com` and nothing else.

## Step 2 — change the DNS records at GoDaddy

**My Products → cincinnatikcpc.com → DNS**

Delete the records pointing at Wix:

- the `A` record on `@`
- the `CNAME` record on `www`

**Leave every `MX` record alone.** Those route church email — deleting them breaks it.

Then add:

| Type  | Name | Value                  | TTL    |
|-------|------|------------------------|--------|
| A     | @    | `185.199.108.153`      | 1 hour |
| A     | @    | `185.199.109.153`      | 1 hour |
| A     | @    | `185.199.110.153`      | 1 hour |
| A     | @    | `185.199.111.153`      | 1 hour |
| CNAME | www  | `yechani33.github.io.` | 1 hour |

Those four IPs are GitHub's and are the same for every user. The CNAME value is your
Pages host — keep the trailing dot if GoDaddy shows one.

Optionally add IPv6 as four `AAAA` records on `@`:

```
2606:50c0:8000::153
2606:50c0:8001::153
2606:50c0:8002::153
2606:50c0:8003::153
```

## Step 3 — set the custom domain and HTTPS

Back at **Settings → Pages**, the custom domain should read `www.cincinnatikcpc.com`
(picked up from the CNAME file).

DNS takes anywhere from minutes to a few hours. Watch it with:

```bash
dig +short www.cincinnatikcpc.com
dig +short cincinnatikcpc.com
```

Once those show GitHub's values instead of `wixdns.net`, tick **Enforce HTTPS**. If it is
greyed out, GitHub is still issuing the certificate — check back later.

## Step 4 — afterwards

- Visit `https://www.cincinnatikcpc.com` and click through every page.
- Run **Update Sunday sermon** once by hand from the **Actions** tab.
- Only once that all works: cancel the Wix plan.
- **Keep the GoDaddy registration.** It is separate from Wix hosting, costs about $22/year,
  and is currently paid through 26 May 2027. If it lapses you lose the domain name.

To back out at any point, put the old Wix DNS values back.

---

## Appendix — installing git on a new Mac

```bash
sudo softwareupdate --install "Command Line Tools for Xcode 27.0-27.0"
```

The label really does repeat the version; check the exact name with `softwareupdate --list`
if it ever differs. Or run `xcode-select --install` and click **Install** in the dialog.

When git asks for a password on push, it wants a **Personal Access Token**, not your
account password. Create one at <https://github.com/settings/tokens> with both **`repo`**
and **`workflow`** ticked. macOS Keychain remembers it after the first time.

---

## Troubleshooting

**Pages built but the site looks unstyled.** Check the browser console for 404s on
`assets/css/site.css`. All paths are relative, so this usually means a file did not get
committed.

**"Domain does not resolve to the GitHub Pages server."** DNS has not propagated yet. Wait
and re-check with `dig`.

**404 on every page.** Settings → Pages must be branch `main`, folder `/ (root)`.

**Sermon video errors when previewing locally.** Use `http://localhost:8123`, never
`http://127.0.0.1:8123` — YouTube refuses to play embeds on that address.

**Push rejected over a workflow file.** Your token needs both `repo` and `workflow` scopes.
