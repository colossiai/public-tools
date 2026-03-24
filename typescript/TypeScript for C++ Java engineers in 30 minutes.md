# TypeScript for C++/Java engineers in 30 minutes


Below is a **30-minute crash course of TypeScript specifically for senior C++ / Java / Go backend engineers**.
It focuses only on things that **differ from strongly typed backend languages**.

---

# 0. Mental Model (Most Important)

**TypeScript is not a runtime language.**

Pipeline:

```
TypeScript  →  JavaScript  →  Node.js runtime
(tsc compile)
```

Example:

```ts
function add(a: number, b: number): number {
  return a + b
}
```

Compiles to:

```js
function add(a, b) {
  return a + b;
}
```

Types **disappear at runtime**.

Runtime is **Node.js**, not TypeScript.

---

# 1. Structural Typing (Biggest Difference)

Languages like **Java** use **nominal typing**.

TypeScript uses **structural typing**.

### Example

```ts
type User = { id: number }
type Customer = { id: number }

let u: User = { id: 1 }
let c: Customer = u
```

This is valid.

Why?

```
if shape matches → type matches
```

Think:

```
duck typing + static check
```

---

# 2. Basic Types (Quick)

```ts
let a: number = 1
let b: string = "hello"
let c: boolean = true
```

Array:

```ts
let nums: number[] = [1,2,3]
```

Object:

```ts
let user: {id:number, name:string}
```

---

# 3. Interfaces (Like Java Interfaces but Structural)

```ts
interface User {
  id: number
  name: string
}
```

Usage:

```ts
function getName(u: User) {
  return u.name
}
```

Objects only need **matching fields**.

---

# 4. Union Types (Very Important)

One of the most powerful TS features.

```ts
function print(x: string | number) {
  console.log(x)
}
```

Equivalent in Java:

```
Object
+ instanceof checks
```

Better example:

```ts
type Result =
  | { ok: true; value: number }
  | { ok: false; error: string }
```

Usage:

```ts
if (r.ok) {
  console.log(r.value)
}
```

This is called **discriminated unions**.

---

# 5. Generics

Very similar to **Java generics**.

```ts
function identity<T>(v: T): T {
  return v
}
```

Usage:

```
identity<number>(1)
identity("hello")
```

Generic interface:

```ts
interface Box<T> {
  value: T
}
```

---

# 6. Async Programming

JavaScript uses **event loop concurrency**.

No threads like **Go** or **C++**.

Core abstraction:

```
Promise<T>
```

Example:

```ts
function fetchUser(): Promise<User> {
  ...
}
```

Modern style:

```ts
async function fetchUser() {
  return {id:1, name:"eric"}
}
```

Usage:

```ts
const u = await fetchUser()
```

---

# 7. The Event Loop (Critical)

JS executes:

```
single thread
+
event loop
+
non blocking IO
```

Example:

```ts
console.log("A")

setTimeout(() => console.log("B"),0)

Promise.resolve().then(()=>console.log("C"))

console.log("D")
```

Output:

```
A
D
C
B
```

Why:

```
Promise → microtask queue
setTimeout → macrotask queue
```

This model powers **Node.js** scalability.

---

# 8. Classes (JS Version)

```ts
class User {
  constructor(public name: string) {}

  greet() {
    console.log(this.name)
  }
}
```

Differences vs Java:

| Feature             | Java   | TypeScript   |
| ------------------- | ------ | ------------ |
| runtime enforcement | yes    | no           |
| private             | strict | compile-only |
| method overload     | yes    | limited      |

Example:

```ts
private id:number
```

This disappears after compile.

---

# 9. Modules

Modern style:

```ts
export function foo() {}
```

Import:

```ts
import { foo } from "./util"
```

Equivalent of Java packages.

---

# 10. Runtime Environment

Backend TypeScript runs on **Node.js**.

Example HTTP server:

```ts
import http from "http"

http.createServer((req,res)=>{
  res.end("hello")
}).listen(3000)
```

---

# 11. Package Ecosystem

Everything is distributed via **npm**.

Example:

```
package.json
```

```json
{
 "dependencies": {
   "express": "^4.0"
 }
}
```

---

# 12. tsconfig (Build System)

Key file:

```
tsconfig.json
```

Example:

```json
{
 "compilerOptions": {
  "target": "ES2020",
  "module": "commonjs",
  "strict": true
 }
}
```

Compiler:

```
tsc
```

From **TypeScript Compiler**.

---

# 13. Typical Backend Stack

Common stack:

```
TypeScript
   ↓
Node.js
   ↓
Web framework
```

Frameworks:

* **Express.js**
* **Fastify**
* **NestJS**

For Java engineers:

```
NestJS ≈ Spring Boot
```

---

# 14. Common Functional Patterns

JS ecosystem uses functional style heavily.

Example:

```ts
users
  .filter(u => u.active)
  .map(u => u.name)
```

Instead of loops.

---

# 15. Things That Shock Backend Engineers

### 1. Types disappear at runtime

```
TS = compile-time only
```

---

### 2. Structural typing

Types are **shapes**, not classes.

---

### 3. Everything async

Even:

```
file IO
database
network
```

---

### 4. Package ecosystem huge

Millions of packages.

---

### 5. Runtime errors still possible

TypeScript improves safety but does **not eliminate runtime errors**.

---

# Minimal Backend Example

```ts
import express from "express"

const app = express()

app.get("/hello", (req,res)=>{
  res.json({msg:"hello"})
})

app.listen(3000)
```

Using **Express.js**.

---

# 30-Minute Learning Checklist

If you understand these, you can start writing TS immediately.

✅ structural typing
✅ union types
✅ generics
✅ async/await
✅ event loop
✅ modules
✅ npm ecosystem
✅ Node runtime

---

💡 If you'd like, I can also show a **“TypeScript mental model for Go / Java engineers”** that explains why many backend engineers initially **misuse TypeScript architecture**. It helps avoid the most common design mistakes.
