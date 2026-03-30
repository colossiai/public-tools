**`flex-grow`** is a **Flexbox property** that controls **how much a flex item expands to fill extra space** inside a flex container.

---

# Core idea

When a container has **extra space**, `flex-grow` determines **how that space is distributed between items**.

```css
flex-grow: <number>;
```

* `0` → do **not grow**
* `1` → grow normally
* `2` → grow **twice as much as items with 1**

Think of it like **weights for sharing leftover space**.

---

# Example

```html
<div style="display:flex; width:600px;">
  <div style="flex-grow:1;">A</div>
  <div style="flex-grow:2;">B</div>
</div>
```

Layout result:

```
|---- A ----|--------- B ---------|
```

Because:

```
A grow weight = 1
B grow weight = 2
```

Total weight = 3

So space is divided:

```
A gets 1/3
B gets 2/3
```

---

# Example with 3 items

```html
<div style="display:flex;">
  <div style="flex-grow:1;">A</div>
  <div style="flex-grow:1;">B</div>
  <div style="flex-grow:1;">C</div>
</div>
```

Result:

```
|   A   |   B   |   C   |
```

Equal widths.

---

# If `flex-grow` is 0

```html
<div style="display:flex;">
  <div style="flex-grow:0;">A</div>
  <div style="flex-grow:1;">B</div>
</div>
```

Result:

```
|A|-------------------B-------------------|
```

A stays content size.
B expands.

---

# Relationship with `flex`

The `flex` shorthand includes **three properties**:

```css
flex: grow shrink basis;
```

Example:

```css
flex: 1 1 0%;
```

means

```
flex-grow: 1
flex-shrink: 1
flex-basis: 0%
```

That’s exactly what **`flex-1`** in **Tailwind CSS** uses.

---

# Mental model (important)

1️⃣ Layout items at their **base size**
2️⃣ Calculate **remaining space**
3️⃣ Distribute space based on **flex-grow ratio**

---

# Backend engineer analogy

Think of it like **CPU scheduling weights**.

```
container = CPU time
flex-grow = process weight
```

Example:

```
A weight = 1
B weight = 3
```

CPU share:

```
A = 25%
B = 75%
```

Same idea.

---

# One-line definition

**`flex-grow` controls how much a flex item expands relative to its siblings when extra space is available.**

---

If you'd like, I can also show the **Flexbox rule that explains 95% of layout bugs** (why `flex-1` sometimes doesn't work and why `min-width:0` suddenly fixes everything).
