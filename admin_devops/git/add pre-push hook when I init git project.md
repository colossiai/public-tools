# #I want to add pre-push hook when I init git project


When you run `git init`, Git **does not automatically create active hooks**. It only includes **sample hook files** in `.git/hooks/` (usually with `.sample` suffix). To add a **`pre-push` hook automatically when initializing a repo**, you have a few common options.

---

# Option 1 — Use a Global Git Hook Template (Best Practice)

Git allows defining a **template directory**. Any repo created with `git init` will copy hooks from there.

### 1. Create a template directory

```bash
mkdir -p ~/.git-template/hooks
```

### 2. Add your `pre-push` hook

```bash
touch ~/.git-template/hooks/pre-push
chmod +x ~/.git-template/hooks/pre-push
```

Example hook:

```bash
#!/bin/sh

echo "Running pre-push checks..."

# prevent push to main
branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$branch" = "main" ]; then
  echo "❌ Direct push to main is not allowed"
  exit 1
fi
```

### 3. Tell Git to use this template

```bash
git config --global init.templateDir ~/.git-template
```

Now every time you run:

```bash
git init
```

Git will automatically copy the hook into:

```
.git/hooks/pre-push
```

---

# Option 2 — Use `core.hooksPath` (Better for teams)

Instead of copying hooks into `.git/hooks`, point Git to a shared directory.

### 1. Create a hooks folder

```bash
mkdir -p ~/.githooks
```

### 2. Add `pre-push`

```bash
touch ~/.githooks/pre-push
chmod +x ~/.githooks/pre-push
```

### 3. Configure Git

```bash
git config --global core.hooksPath ~/.githooks
```

Now **all repositories automatically use these hooks**.

Advantages:

* hooks version-controlled
* no copying needed
* easy to update

---

# Option 3 — Project-level hooks (committed in repo)

Common pattern in teams:

```
repo/
  .githooks/
    pre-push
```

Then configure:

```bash
git config core.hooksPath .githooks
```

---

# Recommended Setup

For **personal workflow**:

```
git config --global core.hooksPath ~/.githooks
```

For **team repositories**:

```
repo/.githooks/
git config core.hooksPath .githooks
```

---

# Bonus — Prevent pushing a local-only branch

Since you previously asked about **keeping a branch local only**, a `pre-push` hook can enforce that:

```bash
#!/bin/sh

protected="local"

branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$branch" = "$protected" ]; then
  echo "🚫 Branch '$protected' must stay local."
  exit 1
fi
```

---

If you want, I can also show a **production-grade pre-push hook used in large repos** that runs:

* lint
* tests
* branch protection
* commit message validation
  in **<100ms** using parallel execution.


# #this will take effect when I clone project?

Short answer: **No.**

Neither **`init.templateDir`** nor **`core.hooksPath` configured locally in the repo** will automatically apply when someone **clones a project**.

This is a **Git security design**:
Git intentionally **does NOT transfer hooks during clone** to avoid running arbitrary code from remote repositories.

---

# What happens in each case

## 1️⃣ `init.templateDir`

Only affects:

```
git init
```

It copies hooks when **creating a new repo**, but **`git clone` bypasses it**.

So cloned repo:

```
.git/hooks/
   pre-push.sample
```

Your hook **won't exist**.

---

## 2️⃣ Global `core.hooksPath`

If a developer runs:

```bash
git config --global core.hooksPath ~/.githooks
```

Then **all repos on their machine (including cloned ones)** will use that path.

But:

* This depends on **each developer configuring it**
* It is **not controlled by the repository**

---

# Recommended Team Pattern (Most Common)

Store hooks **inside the repository**, then activate them.

Example repo:

```
repo/
  .githooks/
    pre-push
  scripts/
    setup-hooks.sh
```

### `.githooks/pre-push`

```bash
#!/bin/sh
echo "Running pre-push checks..."
```

Make executable:

```bash
chmod +x .githooks/pre-push
```

---

### `scripts/setup-hooks.sh`

```bash
git config core.hooksPath .githooks
```

After clone:

```bash
git clone repo
cd repo
./scripts/setup-hooks.sh
```

Now hooks work.

---

# Alternative: Auto-setup via Makefile (common in Go repos)

```
Makefile
```

```make
setup:
	git config core.hooksPath .githooks
```

Run:

```
make setup
```

---

# What Large Companies Do

Many companies use tools like:

* pre-commit
* Husky
* Lefthook

These tools automatically install hooks after clone.

Example (very common):

```
pre-commit install
```

---

# Best approach for your use case

Since you're building **Go backend projects**, I recommend:

```
repo/
  .githooks/
  Makefile
```

Setup command:

```
make dev
```

Which runs:

```
git config core.hooksPath .githooks
```

---

✅ **Summary**

| Method                          | Works on clone | Notes                |
| ------------------------------- | -------------- | -------------------- |
| `init.templateDir`              | ❌              | Only `git init`      |
| `core.hooksPath (global)`       | ✅              | Requires user setup  |
| Repo `.githooks` + setup script | ✅              | Most common          |
| Git transferring hooks          | ❌              | Security restriction |

---

If you want, I can also show a **very clean pattern used in Go monorepos** where:

```
git clone
make dev
```

automatically installs **hooks + linters + formatters + pre-push tests** in one step.
