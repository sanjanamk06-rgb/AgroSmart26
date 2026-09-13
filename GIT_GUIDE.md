# Git Guide — AgroSmart26

You don't need to "learn git." You need these ~10 commands, in this order, for the next two days. Everything else in this doc is here so the commands make sense, not so you memorize theory.

## The idea in one paragraph

GitHub is a shared folder in the cloud (called a **repo**). You **clone** it (download a copy to your laptop), make changes inside **your own folder**, and **push** those changes back up so everyone else can see them. A **branch** is your own private lane inside the repo — you work in your lane, then merge it into the main lane (`main`) when it's ready, so you're never directly editing what everyone else sees until you're done.

---

## One-time setup (do this once)

**1. Clone the repo** — downloads it to your laptop:
```
git clone https://github.com/sanjanamk06-rgb/AgroSmart26.git
cd AgroSmart26
```

**2. Create your own `.env` file** — this holds the shared API key. It will NOT be visible on GitHub (that's intentional, it's a secret).
- In VS Code, right-click the `AgroSmart26` folder → New File → name it exactly `.env`
- Paste inside it: `OPENWEATHER_API_KEY=<ask Sanjana for the actual key over chat>`
- Never type the real key anywhere except this file.

**3. Create your own branch** — your personal lane, named after you:
```
git checkout -b yourname
```
(replace `yourname` with your actual name, e.g. `git checkout -b thanushka`)

---

## The daily loop (do this every time you sit down to work)

**Before you start working — pull the latest changes:**
```
git pull origin main
```
This downloads whatever teammates have added since you last checked. Do this every time, even if you think nothing changed — skipping it is the #1 cause of "why is my code suddenly broken."

**While working:** only edit files inside your own module folder (`/forecasting`, `/detection`, `/gis`, `/knowledge-base`, `/dashboard`, `/backend`, `/mobile-app`). Staying in your own lane means nobody's changes overwrite anyone else's.

**When you've made progress — save and upload it:**
```
git add .
git commit -m "short description of what you changed"
git push origin yourname
```
- `git add .` — stages everything you changed (tells git "include this")
- `git commit -m "..."` — saves a snapshot, with a short note describing it
- `git push origin yourname` — uploads it to YOUR branch on GitHub (not `main` — that's intentional, see below)

**Then, on GitHub.com:** go to the repo → you'll see a banner offering to "Compare & pull request" for your branch → click it → click "Create pull request." This is just asking "can my changes be merged into main?" Sanjana or John will review and click merge.

---

## Terms, explained once

| Term | What it actually means |
|---|---|
| Repo | The shared project folder, living on GitHub |
| Clone | Downloading a copy of the repo to your laptop |
| Commit | A saved snapshot of your changes, with a note attached |
| Push | Uploading your commits to GitHub |
| Pull | Downloading teammates' commits from GitHub |
| Branch | Your own private lane to work in, separate from `main` |
| Pull Request (PR) | A request to merge your branch into `main`, reviewed before it happens |
| Merge conflict | Git found two people changed the same lines and needs a human to pick |
| `.gitignore` | A list of files git should never track (like `.env`, which holds secrets) |

---

## When something looks broken (it usually isn't)

**"python3 not recognized" (Windows)** — use `python`, not `python3`, for every command.

**Terminal looks frozen, shows `>>` and won't respond** — you pasted multiple lines as one block and it's still waiting for you to finish. Press `Ctrl + C` to cancel, then type commands one line at a time instead of pasting blocks.

**Screen goes mostly blank with `~` down the left side** — that's a text editor called Vim that git opened by accident. Press `Esc`, type `:q!`, press Enter. This exits without changing anything.

**Push rejected: "failed to push... tip of your branch is behind"** — someone else pushed changes you don't have yet. Run `git pull origin main` first, then push again.

**Push rejected: "Push cannot contain secrets"** — you accidentally committed an API key or password. Never type a real key directly into a `.py` or `.js` file — it always goes in `.env`, which git is told to ignore.

**Merge conflict** (you'll see `<<<<<<<`, `=======`, `>>>>>>>` inside a file) — this means you and someone else edited the same lines. Open the file, read both versions, delete the ones you don't want along with the `<<<<<<<` / `=======` / `>>>>>>>` markers themselves, save, then `git add .`, `git commit -m "resolve conflict"`, `git push`.

---

## Three rules that prevent 90% of problems

1. **Pull before you start, push when you finish.** Every session.
2. **Only touch files in your own module folder.** If you need to change something in someone else's folder, message them first.
3. **Never paste multi-line command blocks — type one line, press Enter, wait, then the next.**
