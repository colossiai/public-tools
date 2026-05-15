# #In git merge conflicts, how to pick "theirs" without manual resolve?


To accept all changes from the other branch (“theirs”) during a merge conflict:

```bash
git checkout --theirs .
git add .
git commit
```

Explanation:

* `--theirs` = the branch you are merging **into your current branch**
* `.` = apply to all conflicted files

Typical flow:

```bash
git merge feature-branch

# conflicts happen

git checkout --theirs .
git add .
git commit
```

---

For a single file:

```bash
git checkout --theirs path/to/file
git add path/to/file
```

---

Important distinction:

During merge:

* `ours` = your current checked-out branch
* `theirs` = incoming branch being merged

Example:

```bash
git checkout main
git merge feature
```

* `ours` = `main`
* `theirs` = `feature`

---

Modern Git equivalent (`restore`):

```bash
git restore --source=MERGE_HEAD -- .
```

But `checkout --theirs` is still the most common and readable for conflict resolution.

---

If you want Git to automatically prefer theirs for the whole merge:

```bash
git merge -X theirs feature-branch
```

Notes:

* `-X theirs` only resolves conflicting hunks automatically
* non-conflicting changes from both sides are still merged normally
* different from completely replacing your branch

There is also:

```bash
git checkout feature-branch .
```

but that overwrites files directly and is not specifically conflict-aware.
