# Deploying it for free

Everything here is free forever, needs no credit card, and takes about
fifteen minutes.

There are two things to host:

| What | What it is | Where it goes |
|---|---|---|
| `portfolio/` | the website — pure static files | **GitHub Pages** (free, unlimited, no card) |
| `payroll-suite/` | the payroll app — a Python server with a database | **PythonAnywhere** (free tier) — optional |

Do the website first. It is the one that matters, it is the easiest, and
the payroll app is a nice-to-have that you can add later.

---

## 1. The website on GitHub Pages

GitHub Pages serves static files straight from your repository. No build
step, no server, nothing to maintain — every push updates the site.

### Step 1 — the repository

Already done:

```
https://github.com/vcfvz22rk5-debug/sa-payroll-tax-suite
```

It is public (the free Pages plan needs that) and `main` is the default
branch.

### Step 2 — push the code

```bash
git add -A
git commit -m "SA payroll, tax and compliance suite"
git branch -M main
git remote add origin https://github.com/vcfvz22rk5-debug/sa-payroll-tax-suite.git
git push -u origin main
```

### Step 3 — the site publishes itself

The repository has a workflow, `.github/workflows/pages.yml`, that
publishes the `portfolio` folder to GitHub Pages every time you push to
it. The first push starts it automatically.

The site is live at:

```
https://vcfvz22rk5-debug.github.io/sa-payroll-tax-suite/
```

You can watch it happen in the repository under **Actions**. If it ever
needs re-running, open the workflow and press **Re-run all jobs**.

> **Why a workflow and not "Deploy from a branch"?**
> GitHub Pages will only publish the root of a branch or a `/docs`
> folder — it cannot point at an arbitrary folder like `portfolio`.
> A workflow can, and it also means the site is only rebuilt when
> something in it actually changes.

### Step 4 — fix the social preview

The preview picture that WhatsApp, LinkedIn and X show when someone
shares your link has to be an **absolute** url, and it has to match
where the site actually is. Two places to change:

**`portfolio/index.html`** — the `<head>`:

```html
<meta property="og:url" content="https://vcfvz22rk5-debug.github.io/sa-payroll-tax-suite/" />
<meta property="og:image" content="https://vcfvz22rk5-debug.github.io/sa-payroll-tax-suite/assets/img/og-image.png" />
<meta name="twitter:image" content="https://vcfvz22rk5-debug.github.io/sa-payroll-tax-suite/assets/img/og-image.png" />
<link rel="canonical" href="https://vcfvz22rk5-debug.github.io/sa-payroll-tax-suite/" />
```

Those are already set to that URL, so **you only need to change them if
you move the site**. If you do change the site, the picture will not
update straight away — social networks cache them, and you can force it
at [developers.facebook.com/tools/debug](https://developers.facebook.com/tools/debug/).

---

## 2. A custom domain (also free)

A `.dev` domain costs about R100 a year, and GitHub Pages will host it
with free HTTPS.

1. Buy a domain anywhere (Cloudflare, Namecheap, GoDaddy)
2. In **Settings** → **Pages** → **Custom domain**, type the domain and
   **Save**
3. GitHub tells you the four nameservers to set at your registrar
4. Wait for the DNS to propagate — usually under an hour, sometimes a day
5. Tick **Enforce HTTPS** when it appears

Do **not** tick "Enforce HTTPS" before DNS is working, or you will lock
yourself out.

---

## 3. Other ways to publish the site

If you would rather not use GitHub, all of these are free and take the
same folder:

| Host | How |
|---|---|
| **Netlify** | [app.netlify.com/drop](https://app.netlify.com/drop) — drag the `portfolio` folder onto the page. Done. |
| **Cloudflare Pages** | New project → connect the repo → build command *(leave empty)* → output directory `portfolio` |
| **Vercel** | New project → import the repo → framework "Other" → output directory `portfolio` |

Netlify's drag-and-drop is the fastest way to get something online in
about thirty seconds. Use it if you just want to see the site live.

---

## 4. The payroll app on a free host (optional)

The payroll suite is a Python server, so it needs a host that can run a
process. The free tier of **PythonAnywhere** is the easiest.

**On PythonAnywhere:**

1. Create a free account at [pythonanywhere.com](https://www.pythonanywhere.com)
2. **Files** → upload the project, or use a Bash console and `git clone`
3. **Web** → **Add a new web app** → **Manual configuration** → Python 3.11
4. Set the **working directory** to your project folder
5. Edit the **WSGI configuration file** and replace its contents with:

```python
import sys
sys.path.insert(0, '/home/yourusername/sa-salary-tax-calculator/payroll-suite')

from payroll_suite.wsgi import application
```

6. Set the database path (in the same file, before the import):

```python
import os
os.environ['PAYROLL_DB'] = '/home/yourusername/sa-salary-tax-calculator/payroll-suite/data/payroll.db'
```

7. **Reload** the web app

Your dashboard is live at `https://yourusername.pythonanywhere.com`.

**Two things to know about the free tier:**

- The database file has to be somewhere that persists. The
  `/home/yourusername/` folder does; a temporary folder does not.
- On the free tier you get **one** web app and the domain is
  `yourusername.pythonanywhere.com`. A custom domain needs the paid
  plan.

**Other free hosts that work:**

| Host | What to do |
|---|---|
| **Render** | New → Web Service → point at the repo → build `pip install -e .` → start `gunicorn payroll_suite.wsgi:application`. Free, but the free tier **sleeps after 15 minutes idle** and the filesystem is **ephemeral**, so the database resets on every deploy. |
| **Fly.io** | Similar to Render, with a small free allowance. |

For a portfolio, the honest advice is: **host the website on GitHub
Pages, and run the payroll app from your own machine when you demo it.**
The app needs a database and a long-running process, which is where the
free tiers start to hurt.

---

## 5. A checklist before you share the link

- [ ] `PROFILE.email` in `portfolio/assets/js/data.js` is your real address
      (it is the one in the contact card and the one people will copy)
- [ ] The GitHub and LinkedIn links in `PROFILE` point at your profiles
- [ ] The `og:url` and `og:image` lines match where the site really is
- [ ] The project cards link to your real repositories
- [ ] You have replaced `ayanda.shongwe@example.com` in
      `portfolio/index.html` too (the fallback in the contact card)
- [ ] You have read the disclaimer — it says this is study work, not
      advice, and that is worth keeping

---

## 6. If something does not work

**The site is blank.** Open the browser console (F12). If it says
`404` for a file, the `og:image` or asset path is wrong — remember
these are relative paths, so they work at any sub-folder.

**The site works locally but not on Pages.** You almost certainly
picked the wrong source folder. It must be `/portfolio`, not `/ (root)`.

**The fonts look different.** Google Fonts is loaded from the internet.
Offline, the browser falls back to a system font. Nothing is broken.

**The database keeps resetting.** The host's filesystem is ephemeral.
Move the database to a path that persists, or accept that the demo data
is rebuilt each time.

**The demo data is missing on the live site.** The database file is
deliberately not in git (it is in `.gitignore`). Run
`python3 -m payroll_suite.cli init` on the host to create it.
