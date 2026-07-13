# 解读 TypeScript 类型

`typescript/unique-features/src/03-type-level-programming.ts`

这是一个**非常高质量**的 TypeScript Type-level Programming 示例，几乎把 TypeScript 类型系统最重要的能力都浓缩进来了。

结合你之前学习的 **Go 泛型、交叉类型、LLM 数学（矩阵、投影、Transformer）**，我建议把它理解成：

> **运行时（Runtime）写的是程序；类型系统（Type System）写的是另一个程序。**

这个文件其实是在展示：

> **TypeScript 的类型系统本身就是一门函数式语言（Functional Language）。**

---

# 0. 为什么 TypeScript 独一无二？

文件开头说：

> Types as a computation language (the crown jewel)

意思就是：

> Type 可以计算（Compute），不仅仅是描述（Describe）。

很多语言：

```
Go
Java
C#
```

泛型只是：

```
List<T>

T = int
↓

List<int>
```

只是替换。

没有计算。

---

TypeScript 可以：

```
Input Type
      │
      ▼
Pattern Match
      │
      ▼
Extract
      │
      ▼
Transform
      │
      ▼
Generate New Type
```

这就是 Type-level Programming。

---

# 第一部分：keyof

```ts
interface User {
    id: number;
    name: string;
    admin: boolean;
}
```

编译器看到的是：

```
User

┌─────────────┐
│ id    number│
│ name  string│
│ admin bool  │
└─────────────┘
```

然后

```ts
type UserKey = keyof User;
```

相当于

```
取所有 key

↓

"id"
"name"
"admin"

↓

"id" | "name" | "admin"
```

所以

```
keyof

≈

Object.keys()

但是

发生在编译时期
```

而不是运行时。

---

# 第二部分：Indexed Access

```ts
type NameType = User["name"];
```

就是：

```
User

↓

找字段

↓

name

↓

string
```

像数组：

```
arr[3]
```

这里变成：

```
Type["field"]
```

所以：

```
User["id"]

↓

number
```

```
User["admin"]

↓

boolean
```

---

# 第三部分：真正的泛型 getter

这是第一个值得深入理解的地方。

```ts
function get<T, K extends keyof T>(
    obj: T,
    key: K
): T[K]
```

拆开看。

---

## 第一步

```
T

↓

User
```

---

## 第二步

```
K extends keyof T
```

意思：

```
K

必须属于

"id"
"name"
"admin"
```

所以：

```
get(user,"abc")
```

编译器：

```
abc

是不是

keyof User ?

×

报错
```

所以：

```
编译器提前发现错误
```

而 Go：

```
map[string]any
```

很多错误只能运行时发现。

---

## 第三步

返回值：

```
T[K]
```

例如：

```
get(user,"name")
```

推导：

```
T

↓

User

K

↓

"name"

↓

User["name"]

↓

string
```

所以：

```
name

自动就是 string
```

无需类型断言。

---

# 第四部分：Mapped Type

这里开始进入 Type Programming。

```ts
type MyPartial<T> = {
    [K in keyof T]?: T[K]
}
```

第一次看到的人都会觉得：

```
？？？
```

其实它就是：

```
for every key

↓

生成新的类型
```

可以画成：

```
User

id
name
admin

↓

for each K

↓

id?
name?
admin?
```

最后：

```
{
   id?:number
   name?:string
   admin?:boolean
}
```

是不是就像：

```go
for _, k := range keys {

}
```

只是：

发生在编译器里面。

---

# MyReadonly

```ts
readonly [K in keyof T]
```

就是：

```
for each field

↓

加 readonly
```

得到：

```
readonly id

readonly name

readonly admin
```

---

# DeepReadonly

这是一个经典面试题。

```ts
type DeepReadonly<T>
```

为什么叫 Deep？

因为：

```
普通 readonly

↓

只能第一层
```

例如：

```
A

↓

a

↓

b

↓

c
```

普通：

```
readonly a

×

b还能改
```

Deep：

```
readonly a

↓

readonly b

↓

readonly c
```

---

它怎么做到？

第一步：

```
是不是数组？
```

```ts
T extends (infer E)[]
```

如果：

```
number[]
```

匹配：

```
(infer E)[]
```

得到：

```
E

=

number
```

然后：

```
ReadonlyArray<
    DeepReadonly<E>
>
```

继续递归。

---

否则：

```
是不是 object？
```

```
T extends object
```

如果：

```
{
   a:{
      b:number
   }
}
```

继续：

```
每一个字段

↓

DeepReadonly
```

一直递归。

最后：

```
number

↓

不是 object

↓

结束
```

---

整个流程：

```
Object

↓

遍历字段

↓

Object ?

↓

继续

↓

Array ?

↓

继续

↓

Primitive ?

↓

Stop
```

这就是递归。

---

# infer

这是 TS 最神奇的关键字。

例如：

```ts
type ElementOf<T>

=
T extends (infer E)[]
    ? E
    : never
```

如果：

```
string[]
```

拿去匹配：

```
(infer E)[]
```

就像：

```
string[]

=

(E)[]
```

所以：

```
E

=

string
```

返回：

```
string
```

---

它其实像：

Python：

```python
head,*tail = arr
```

或者：

Rust

```
match
```

或者：

C++ Template Deduction。

所以作者说：

```
infer

≈

Template Argument Deduction
```

---

# ReturnType

```ts
F extends (...args)=>infer R
```

例如：

```
() => User
```

去匹配：

```
(...args)=>infer R
```

得到：

```
R

=

User
```

结束。

所以：

```
ReturnType<Fn>

其实就是：

把返回值拆出来。
```

---

# Template Literal Types

这是 TS 独创的。

例如：

```
type Route

=

`/${string}`
```

任何：

```
/abc

/users

/settings
```

都是合法。

但：

```
abc
```

非法。

这是：

**类型系统里的字符串模式匹配。**

---

# Getters

这个最精彩。

```ts
[K in keyof T
 as
 `get${Capitalize<K>}`]
```

可以画成：

```
id

↓

Capitalize

↓

Id

↓

get

↓

getId
```

再：

```
name

↓

Name

↓

getName
```

最终：

```
{
 getId()
 getName()
 getAdmin()
}
```

整个类型都是自动生成。

---

# Split

这是整个文件最厉害的一段。

```ts
Split<
"user.address.city",
"."
>
```

第一轮：

```
Head

=

user

Tail

=

address.city
```

得到：

```
["user", ...Split<Tail>]
```

继续：

```
address.city

↓

Head

address

Tail

city
```

得到：

```
["address", ...Split<city>]
```

继续：

```
city

没有 "."
```

结束：

```
["city"]
```

拼起来：

```
["user",
 "address",
 "city"]
```

注意：

整个过程：

**没有任何 JavaScript 执行。**

全部：

```
TypeScript Compiler

完成
```

---

# 为什么作者说这是 TS 的 Crown Jewel？

因为这些能力可以组合。

例如：

```
Input Type
      │
      ▼
keyof
      │
      ▼
Mapped Type
      │
      ▼
Conditional Type
      │
      ▼
infer
      │
      ▼
Template Literal
      │
      ▼
Recursive Type
      │
      ▼
Brand New Type
```

这就是 **Type-level Pipeline**。

---

# 为什么 Zod、Prisma、tRPC 都依赖这些能力？

例如在 Zod 中：

```ts
const User = z.object({
  name: z.string(),
  age: z.number(),
});
```

你并没有手写：

```ts
type User = {
  name: string;
  age: number;
};
```

而是通过：

```ts
type User = z.infer<typeof User>;
```

`z.infer` 内部正是利用了 **条件类型（conditional types）+ `infer` + 递归映射类型（recursive mapped types）**，从 Schema 自动推导出对应的 TypeScript 类型。

类似地：

* **Prisma**：根据数据库 Schema 推导模型类型、查询返回值类型。
* **tRPC**：根据后端路由和输入输出类型，自动生成前端 API 类型。
* **TanStack Router**：根据路由定义推导 URL 参数和 Loader 返回值类型。

这些库真正强大的地方，并不只是泛型，而是把这一整套类型计算能力组合起来，在**编译期**完成复杂的类型推导，从而提供几乎零成本的类型安全和自动补全。

---

## 给你的学习建议

结合你最近一直在深入学习 Go 泛型和 TypeScript，我建议按下面的顺序掌握这些能力：

1. **`keyof` 与 Indexed Access (`T[K]`)** —— 学会读取和索引类型。
2. **Mapped Types (`[K in keyof T]`)** —— 学会“遍历”类型并生成新类型。
3. **Conditional Types (`T extends U ? X : Y`)** —— 学会在类型层面做条件判断。
4. **`infer`** —— 学会从匹配的类型中提取（解构）信息。
5. **Template Literal Types** —— 学会生成和解析字符串类型。
6. **Recursive Types** —— 学会递归地组合前面所有能力。

掌握这六部分后，再去阅读 **Zod**、**Prisma**、**tRPC**、**TanStack** 的类型定义，就会发现它们基本都是这些基础能力的不同组合，而不是新的语法。
