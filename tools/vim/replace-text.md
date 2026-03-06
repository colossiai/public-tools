# Common ways to replace text in vim


Here are the **most common and practical ways to replace text in Vim**, from simplest to more advanced.

---

# ✅ **Basic Replace (current line)**

Replace the first occurrence of `foo` with `bar` on the current line:

```
:s/foo/bar
```

Replace **all occurrences** on the current line:

```
:s/foo/bar/g
```

---

# ✅ **Replace in Entire File**

Replace first occurrence per line:

```
:%s/foo/bar
```

Replace **every occurrence in the whole file**:

```
:%s/foo/bar/g
```

---

# ✅ **Confirm Each Replacement**

Ask for confirmation (`y/n`) each time:

```
:%s/foo/bar/gc
```

---

# ✅ **Case-Insensitive Replace**

```
:%s/foo/bar/gi
```

Case-sensitive override (`\C` forces case-sensitive):

```
:%s/\Cfoo/bar/g
```

---

# ✅ **Replace Only in a Visual Selection**

1. Select text (Visual mode: `v` or `V`)
2. Run:

```
:s/foo/bar/g
```

Or explicitly:

```
:'<,'>s/foo/bar/g
```

---

# ✅ **Replace in Specific Line Range**

Lines 10–20:

```
:10,20s/foo/bar/g
```

From current line (`.`) to end of file (`$`):

```
:.,$s/foo/bar/g
```

---

# ✅ **Use Regex Groups**

Swap "hello world" → "world hello":

```
:%s/\(hello\) \(world\)/\2 \1/g
```

---

# ✅ **Replace Using Very Magic Mode (simplifies regex)**

Use `\v` at start to simplify escaping:

```
:%s/\vfoo(bar|baz)/repl/g
```

---

# ✅ **Replace Whole Word Only**

```
:%s/\<foo\>/bar/g
```

---

# ✅ **Replace Across Multiple Files**

Open files via `:args`, `:grep`, etc.

Example using args:

```
:args *.txt
:argdo %s/foo/bar/ge | update
```

---

# 🔥 Bonus: *Repeat Last Substitution*

Repeat `:s` from normal mode:

```
&
```

Repeat and confirm:

```
g&
```

---


