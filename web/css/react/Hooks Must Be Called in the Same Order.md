# #Hooks Must Be Called in the Same Order

This rule is one of the **most important rules of React Hooks**:

> **Hooks must always be called in the same order on every render.**

The reason comes directly from **how React stores hook state internally**.

---

# 1. React identifies hooks by **position**, not by name

In the simplified implementation we saw earlier:

```javascript
let hooks = []
let hookIndex = 0
```

When a component runs:

```javascript
function Component() {
  const [count, setCount] = useState(0)
  const [name, setName] = useState("Eric")
}
```

React internally stores:

```
hooks = [
  0,        // hook #0 → count
  "Eric"    // hook #1 → name
]
```

React **does NOT store variable names** like `count` or `name`.

Instead it remembers:

```
hook 0
hook 1
hook 2
...
```

---

# 2. How React reads the hooks on the next render

Every render React resets:

```
hookIndex = 0
```

Then executes the component again.

```
useState() → hooks[0]
useState() → hooks[1]
```

Example:

```javascript
function Component() {
  const [count] = useState(0)
  const [name] = useState("Eric")
}
```

Render flow:

```
hookIndex=0 → useState → hooks[0]
hookIndex=1 → useState → hooks[1]
```

Everything lines up correctly.

---

# 3. What breaks when order changes

Example **BAD code**:

```javascript
function Component() {

  const [count, setCount] = useState(0)

  if (count > 5) {
    const [name, setName] = useState("Eric")  // ❌ conditional hook
  }

  const [age, setAge] = useState(20)
}
```

### First render (`count = 0`)

Execution:

```
useState(count) → hooks[0]
skip conditional hook
useState(age) → hooks[1]
```

State storage:

```
hooks = [
  0,     // count
  20     // age
]
```

---

### Later render (`count = 6`)

Now the conditional executes.

Execution order:

```
useState(count) → hooks[0]
useState(name) → hooks[1]  ❌ WRONG
useState(age) → hooks[2]
```

But React thinks:

```
hooks[1] = age
```

So now everything is misaligned.

```
name gets age value
age becomes undefined
```

This breaks the component.

---

# 4. Visual example of the bug

### First render

```
hooks = [
  0,     // count
  20     // age
]
```

### Second render (order changed)

React expects:

```
hooks = [
  count,
  name,
  age
]
```

But actual storage is:

```
hooks = [
  0,
  20
]
```

Now:

```
name = 20 ❌
age = undefined ❌
```

---

# 5. The **correct pattern**

Hooks must always run **unconditionally at the top level**.

✅ Good:

```javascript
function Component() {

  const [count, setCount] = useState(0)
  const [name, setName] = useState("Eric")
  const [age, setAge] = useState(20)

  if (count > 5) {
    console.log(name)
  }
}
```

Hook order:

```
1 useState
2 useState
3 useState
```

Always the same.

---

# 6. Same rule applies to **all hooks**

This includes:

* `useState`
* `useEffect`
* `useMemo`
* `useRef`
* `useReducer`
* custom hooks

Example:

❌ Bad:

```javascript
if (loggedIn) {
  useEffect(() => {})
}
```

✅ Correct:

```javascript
useEffect(() => {
  if (loggedIn) {
    // logic here
  }
})
```

---

# 7. The official React rule

From the React docs:

> **Only call hooks at the top level. Never call hooks inside loops, conditions, or nested functions.**

Allowed places:

```
React function component
Custom hook
```

Not allowed:

```
if
for
while
nested functions
event handlers
```

---

# 8. Backend engineer mental model

Think of hooks like this structure:

```
ComponentInstance {
   hooks[0]
   hooks[1]
   hooks[2]
}
```

Each render just **reads sequentially**:

```
cursor++
cursor++
cursor++
```

If you skip one, everything shifts.

---

✅ **Simple rule to remember**

```
Hooks = array slots
Order = identity
```

Change the order → React reads the wrong slot.

---

If you'd like, I can also show you a **mind-blowing fact about React hooks**:

👉 **Why React uses an array instead of a map (like `{count:..., name:...}`)** and how that decision makes React **much faster.**
