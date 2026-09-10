# Deploying and connecting the domain

One-time setup. Once this is done, publishing is just `git push`.

---

## 1. Install git (one time, on this Mac)

Nothing is installed on this machine yet. In Terminal:

```bash
sudo softwareupdate --install "Command Line Tools for Xcode 27.0-27.0"
```

Enter your Mac login password when asked (nothing appears as you type — that's normal).
The label really does repeat the version — check the exact name on your machine with
`softwareupdate --list` if it ever differs. It downloads about 500MB. Then confirm:

```bash
git --version
```

*Alternative:* run `xcode-select --install` and click **Install** in the dialog that pops up.

---

## 2. The GitHub repository

Already created: <https://github.com/yechani33/KCPC> — public, empty, default branch
`main`. Public is what you want here; GitHub Pages is only free on public repositories.

---

## 3. Push the site

```bash
cd ~/cincinnatikcpc
git init
git add -A
git commit -m "Rebuild cincinnatikcpc.com as a static site"
git branch -M main
git remote add origin https://github.com/yechani33/KCPC.git
git push -u origin main
```

GitHub will ask you to sign in. When it asks for a **password**, it does *not* mean your
GitHub account password — it wants a Personal Access Token:

1. <https://github.com/settings/tokens> → **Generate new token (classic)**
2. Tick the **repo** scope, generate, and copy the token
3. Paste it as the password

---

## 4. Turn on GitHub Pages

In the repository: **Settings → Pages**

- **Source:** Deploy from a branch
- **Branch:** `main`, folder `/ (root)` → **Save**

The `CNAME` file in this repo already sets the custom domain to
`www.cincinnatikcpc.com`, so that field should fill itself in.

Wait for the first build (Actions tab shows it), then confirm the site loads at
`https://yechani33.github.io/KCPC/`. Some styling will look wrong on that
temporary address because the site uses absolute paths — that's expected and fixes itself
once the real domain is connected.

---

## 5. Point the domain at GitHub

The domain is registered at **GoDaddy** and uses GoDaddy's own nameservers, so nothing has
to be transferred — only the DNS records change.

Go to GoDaddy → **My Products → cincinnatikcpc.com → DNS**.

### Delete first

Remove the existing records that currently point at Wix:

- the `A` record on `@`
- the `CNAME` record on `www`

Leave `MX` records and anything email-related **alone** — deleting those breaks email.

### Then add

| Type  | Name | Value                      | TTL    |
|-------|------|----------------------------|--------|
| A     | @    | `185.199.108.153`          | 1 hour |
| A     | @    | `185.199.109.153`          | 1 hour |
| A     | @    | `185.199.110.153`          | 1 hour |
| A     | @    | `185.199.111.153`          | 1 hour |
| CNAME | www  | `yechani33.github.io.` | 1 hour |

Those four IPs are GitHub's — they're the same for everybody. The CNAME value is your GitHub
Pages host, `yechani33.github.io.` (keep the trailing dot if GoDaddy shows one).

Optionally also add IPv6, as four `AAAA` records on `@`:

```
2606:50c0:8000::153
2606:50c0:8001::153
2606:50c0:8002::153
2606:50c0:8003::153
```

---

## 6. Turn on HTTPS

DNS takes anywhere from a few minutes to a few hours to propagate. Check progress with:

```bash
dig +short www.cincinnatikcpc.com
dig +short cincinnatikcpc.com
```

Once those return the GitHub values, go back to **Settings → Pages** and tick
**Enforce HTTPS**. If the box is greyed out, GitHub is still issuing the certificate —
wait and check again later.

---

## 7. Last steps

- Visit `https://www.cincinnatikcpc.com` and click through every page.
- In the repo's **Actions** tab, run **Update Sunday sermon** once by hand to confirm it
  works.
- Only after the new site is confirmed working: cancel the Wix plan. Keep the domain
  registration at GoDaddy — that's separate from Wix hosting and must stay active.

---

## Troubleshooting

**Site loads but has no styling.** The custom domain isn't active yet. The CSS is
referenced from the site root (`/assets/css/site.css`), which only resolves once
`www.cincinnatikcpc.com` is serving the site.

**"Domain does not resolve to the GitHub Pages server."** DNS hasn't propagated. Wait and
re-check with `dig`.

**404 on every page.** Check that Pages is set to branch `main`, folder `/ (root)`.

**Sermon video shows an error locally.** Use `http://localhost:8123`, not
`http://127.0.0.1:8123`. YouTube blocks embeds on that address.
