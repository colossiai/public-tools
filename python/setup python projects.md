# use uv to create a python project depends on "requests" lib

To create a new Python project using [`uv`](https://github.com/astral-sh/uv) (a fast Python package manager), and add a dependency on the `requests` follow these steps:

### ✅ Step-by-step Instructions

1. **Initialize a new project directory:**

   ```bash
   mkdir my_project
   cd my_project
   ```

2. **Initialize the Python project using `uv`:**

   ```bash
   uv venv
   ```

3. **Activate the virtual environment:**

   * On **Linux/macOS**:

     ```bash
     source .venv/bin/activate
     ```
   * On **Windows (PowerShell)**:

     ```powershell
     .venv\Scripts\Activate.ps1
     ```

4. **Add the `requests` library as a dependency:**

   ```bash
   uv pip install requests
   ```

   This installs `requests` and creates a `requirements.txt` automatically if needed.

5. (Optional) **Export your dependencies:**

   ```bash
   uv pip freeze > requirements.txt
   ```

---

### 🧪 Verifying the Setup

Create a `main.py` to test it:

```python
# main.py
import requests

response = requests.get("https://httpbin.org/get")
print(response.json())
```

Run it:

```bash
python main.py
```

---

Let me know if you want to use `pyproject.toml` or `uv pip install --upgrade` workflows instead.


# What is the usage of pyproject.toml? given that we can use requirements.txt


Great question! Both `pyproject.toml` and `requirements.txt` are used for managing Python dependencies, but they serve **different purposes** and are part of different stages in the Python packaging and dependency management ecosystem.

---

### 📄 `requirements.txt` — For Pinning Dependencies

* **Purpose:** Used to **pin** exact versions of packages, often for deployment or CI environments.

* **Format:** Simple, flat list of packages like:

  ```txt
  ipython==8.24.0
  numpy==1.26.4
  ```

* **Common Usage:**

  * Freeze your current environment (`pip freeze > requirements.txt`)
  * Install with `pip install -r requirements.txt`
  * Ensures exact reproducibility

* **Limitation:** Doesn't support dependency metadata, like project name, version, authors, etc.

---

### 📄 `pyproject.toml` — Modern Python Project Specification

* **Purpose:** A standardized file (PEP 518/621) that defines:

  * Project metadata (name, version, authors)
  * Build system requirements (e.g., setuptools, hatch, poetry, etc.)
  * Dependencies (like in Poetry or uv)
  * Entry points, plugins, scripts

* **Used by Tools Like:**

  * `poetry`, `hatch`, `uv`, `flit`, `pdm`, etc.
  * Also used for building wheels and source distributions

* **Example:**

  ```toml
  [project]
  name = "myproject"
  version = "0.1.0"
  dependencies = ["ipython"]

  [build-system]
  requires = ["setuptools"]
  build-backend = "setuptools.build_meta"
  ```

* **Benefits:**

  * Single-file, declarative project configuration
  * Tool-agnostic format
  * Supports richer metadata
  * Plays nicely with modern packaging and publishing tools

---

### 🧠 Summary: Which Should You Use?

| Use Case                  | Use `requirements.txt` | Use `pyproject.toml`        |
| ------------------------- | ---------------------- | --------------------------- |
| Production environment    | ✅ Yes                  | Optional                    |
| Development environment   | ✅ Yes                  | ✅ Yes (recommended)         |
| Dependency pinning        | ✅ Yes (`==version`)    | ❌ Not ideal (use lockfiles) |
| Defining a Python package | ❌ No                   | ✅ Yes                       |
| Publishing to PyPI        | ❌ No                   | ✅ Required                  |
| Using tools like `uv`     | ✅ Optional             | ✅ Recommended               |

---

If you just want to **run `ipython` in a virtualenv**, a `requirements.txt` is fine.

But if you're treating this as a **structured project**, `pyproject.toml` is the modern way to go. Tools like `uv`, `poetry`, and `hatch` use it as their core config.

