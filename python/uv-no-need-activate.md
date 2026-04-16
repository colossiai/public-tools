```
project created by `uv init` doesn't need to activate?
just use "uv add", "uv run" to manage project?
```


--- 

Short answer: **yes — you typically don’t need to manually “activate” a virtualenv when using `uv`**.

Here’s how it works:

### 1. What `uv init` sets up

When you run `uv init`, it creates a project with:

* `pyproject.toml`
* an **automatically managed virtual environment** (usually `.venv/`)

### 2. No manual activation needed

Unlike traditional workflows (`venv`, `virtualenv`, `poetry shell`), `uv`:

* **automatically detects and uses the project’s `.venv`**
* runs commands inside it transparently

So instead of:

```bash
source .venv/bin/activate
pip install requests
python main.py
```

You just do:

```bash
uv add requests
uv run python main.py
```

### 3. Key commands

* `uv add <pkg>` → install dependency into project
* `uv remove <pkg>` → uninstall
* `uv run <cmd>` → run inside project environment
* `uv sync` → sync dependencies from lockfile

### 4. When activation is still useful

You *might* still activate manually if:

* you want to run tools directly (`python`, `ipython`, `pytest`) without prefixing `uv run`
* you’re using an editor/IDE that expects an activated env (though most detect `.venv` automatically)

Example:

```bash
source .venv/bin/activate
```

### 5. Mental model

Think of `uv` as combining:

* `pip` + `virtualenv` + `pip-tools/poetry`
* with **implicit environment handling**

---

If you want, I can compare `uv` vs `poetry` vs `pip + venv` in terms of speed, reproducibility, and DX — the differences are pretty interesting in 2026.
