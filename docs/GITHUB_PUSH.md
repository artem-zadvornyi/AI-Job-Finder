# GitHub push — fix authentication (401 / Permission denied)

If `git push` fails with **401**, **Missing or invalid credentials**, or **Permission denied (publickey)**, the project code is fine — Git is not logged into GitHub.

## Fast fix (recommended): GitHub CLI

Run in **Terminal.app** (not only Cursor), from the project folder:

```bash
cd "/Users/artem/Desktop/Programming/My Projects/job_finder_bot"

# Log in (browser opens — paste the one-time code)
gh auth login
```

Choose:

1. **GitHub.com**
2. **HTTPS**
3. **Yes** — authenticate Git with GitHub credentials
4. **Login with a web browser** — complete login (do not press Ctrl+C)

Then wire Git to use `gh`:

```bash
gh auth setup-git
git push -u origin main
```

## If Cursor terminal still shows 401

Cursor may override Git credentials. In the same terminal:

```bash
unset GIT_ASKPASS
unset SSH_ASKPASS
gh auth setup-git
git push -u origin main
```

## Alternative: SSH key

```bash
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/id_ed25519 -N ""
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
```

Copy the output → GitHub → **Settings** → **SSH and GPG keys** → **New SSH key**.

```bash
git remote set-url origin git@github.com:artem-zadvornyi/AI-Job-Finder.git
ssh -T git@github.com
git push -u origin main
```

## Checklist

- [ ] Repo exists: https://github.com/artem-zadvornyi/AI-Job-Finder
- [ ] `gh auth status` shows logged in
- [ ] `git remote -v` points to your repo
- [ ] `.env` is **not** in `git status` before push
