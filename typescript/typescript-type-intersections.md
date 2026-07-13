# typescript 交叉类型 &

TypeScript 的 **交叉类型（Intersection Types）** 使用 `&` 符号表示。

它的作用是：

> **把多个类型合并成一个类型，新的类型必须同时满足所有类型的要求。**

可以理解为：

> `A & B` = **既是 A，也是 B**

---

## 最简单的例子

```ts
type Person = {
    name: string;
};

type Employee = {
    employeeId: number;
};

type Staff = Person & Employee;
```

现在：

```ts
const s: Staff = {
    name: "Alice",
    employeeId: 1001,
};
```

因为 `Staff` 同时拥有：

```
Person
---------
name

Employee
---------
employeeId
```

最终变成

```
Staff
---------
name
employeeId
```

---

# 与联合类型 `|` 对比

很多人都会混淆。

## 联合类型

```ts
type Cat = {
    meow(): void;
};

type Dog = {
    bark(): void;
};

type Animal = Cat | Dog;
```

意思是：

```
Animal

可能是 Cat
也可能是 Dog
```

所以

```ts
const a: Animal = ...
```

不能直接：

```ts
a.meow();   // ❌
```

因为它可能其实是 Dog。

---

而

## 交叉类型

```ts
type Animal = Cat & Dog;
```

表示

```
Animal

必须既能 meow()
又能 bark()
```

所以

```ts
const a: Animal = {
    meow() {},
    bark() {},
};

a.meow();
a.bark();
```

都可以。

---

# 实际开发最常见用途

## 1. 合并多个对象类型

例如：

```ts
interface Base {
    id: number;
}

interface Timestamp {
    createdAt: Date;
}

interface UserInfo {
    name: string;
}
```

组合：

```ts
type User = Base & Timestamp & UserInfo;
```

得到

```ts
{
    id: number;
    createdAt: Date;
    name: string;
}
```

这比复制字段方便很多。

---

## 2. 给已有类型增加字段

例如 API 返回：

```ts
type User = {
    id: number;
    name: string;
};
```

页面需要：

```ts
type UserWithSelected = User & {
    selected: boolean;
};
```

得到

```ts
{
    id
    name
    selected
}
```

非常常见。

---

## 3. React Props

例如

```ts
type ButtonProps = {
    text: string;
};

type Clickable = {
    onClick(): void;
};

type Props = ButtonProps & Clickable;
```

就是

```
text
onClick
```

---

# 如果字段冲突怎么办？

例如：

```ts
type A = {
    id: number;
};

type B = {
    id: string;
};

type C = A & B;
```

这里很多初学者以为：

```
id: number | string
```

其实**不是**。

而是：

```
id: number & string
```

但是：

```
number
&
string
```

没有任何共同值。

因此

```ts
id: never
```

所以：

```ts
const c: C = {
    id: 123
};
```

报错。

甚至：

```ts
const c: C = {
    id: "abc"
};
```

也报错。

因为

```
number & string
```

不存在。

---

# 为什么叫 Intersection（交集）

数学集合：

```
A = {1,2,3}

B = {3,4,5}

A ∩ B

=

{3}
```

TypeScript 借用了这个概念。

例如

```
number

所有数字
```

```
string

所有字符串
```

它们没有交集：

```
number ∩ string

=

∅
```

所以

```
number & string

=

never
```

---

如果是：

```ts
type A = 1 | 2 | 3;
type B = 2 | 3 | 4;

type C = A & B;
```

则：

```
C

=

2 | 3
```

因为：

```
{1,2,3}
∩
{2,3,4}

=

{2,3}
```

---

# 与 interface extends 的区别

很多人问：

```ts
interface A {
    a: number;
}

interface B {
    b: string;
}

interface C extends A, B {}
```

和

```ts
type C = A & B;
```

有什么区别？

对于对象来说，大多数情况下效果相同：

```ts
{
    a: number;
    b: string;
}
```

但 `&` 更灵活，因为它不仅可以组合对象，还可以组合其他类型，例如：

```ts
type A = string & {};
```

或者与泛型、条件类型等高级特性结合使用。

---

# 总结

| 写法       | 含义                                 |
| -------- | ---------------------------------- |
| `A \| B` | **联合类型**：值可以是 A 或 B                |
| `A & B`  | **交叉类型**：值必须同时满足 A 和 B             |
| 对象交叉     | 合并属性                               |
| 属性冲突     | 属性类型也会做交叉，可能得到 `never`             |
| 常见用途     | 合并接口、扩展对象类型、React Props、API 返回类型扩展 |

**一句话记忆：**

* `|`（联合）= **二选一（或更多选一）**
* `&`（交叉）= **全部都要，同时满足所有类型**


# 有点像golang 的 embedded type

对，**很像 Go 的 embedded type（匿名嵌入字段）**，但它们的作用层面并不完全相同。

## 相似之处

Go：

```go
type Person struct {
    Name string
}

type Employee struct {
    Person      // embedded type
    EmployeeID int
}
```

使用时：

```go
e := Employee{
    Person: Person{
        Name: "Alice",
    },
    EmployeeID: 1001,
}

fmt.Println(e.Name) // 自动提升 (promoted field)
```

可以理解为：

```
Employee
├── Name
└── EmployeeID
```

这和 TypeScript 的

```ts
type Person = {
    name: string
}

type Employee = {
    employeeId: number
}

type Staff = Person & Employee
```

得到的效果很接近：

```ts
const s: Staff = {
    name: "Alice",
    employeeId: 1001,
}
```

最终类型都是：

```
Staff
├── name
└── employeeId
```

---

## 最大区别

### Go Embedded

Go 的 embedded type 是**结构体组合（composition）**。

真正的数据仍然是：

```go
Employee
    Person
        Name
```

只是 Go 编译器帮你做了字段提升（field promotion），因此：

```go
e.Name
```

实际上等价于：

```go
e.Person.Name
```

所以内存里仍然有一个 `Person`。

---

### TypeScript Intersection

TypeScript 的

```ts
type Staff = Person & Employee
```

**没有任何运行时对象。**

它只是告诉 TypeScript 编译器：

> 这个对象必须同时符合 `Person` 和 `Employee` 的类型。

JavaScript 最终仍然只是：

```js
{
    name: "Alice",
    employeeId: 1001
}
```

没有 `Person` 对象，也没有嵌套结构。

因此它属于**类型系统（compile-time）**的能力，而不是运行时的数据结构。

---

## Go 更接近的 TypeScript 写法

如果要对应 Go 的真正嵌套结构：

```go
type Employee struct {
    Person
    EmployeeID int
}
```

更接近的是：

```ts
type Employee = {
    person: Person
    employeeId: number
}
```

使用：

```ts
employee.person.name
```

只是 Go 自动帮你省略了 `person` 这一层，所以可以直接写：

```go
employee.Name
```

---

## 一个容易理解的对比

| Go                 | TypeScript                  |           |
| ------------------ | --------------------------- | --------- |
| Embedded type      | `&`（Intersection）有相似的"组合"效果 |           |
| `extends`（接口嵌入）    | 更接近 Go 的接口嵌入                |           |
| Struct Composition | 运行时真实存在                     | 编译时类型检查   |
| Field Promotion    | 有                           | 没有这个概念    |
| 内存布局               | 有实际结构                       | 无（类型会被擦除） |

## 更准确的类比

如果从**设计思想**来看：

* Go 的 **embedded struct** = **对象组合（Composition）**
* TypeScript 的 **`&`（Intersection Type）** = **类型组合（Type Composition）**

两者都遵循了"**把多个能力组合成一个更大的整体**"这一思想，只是 Go 组合的是**数据结构**，TypeScript 组合的是**静态类型**。

所以，如果你熟悉 Go，可以把 `A & B` 初步理解为：

> **"像把两个 struct 的能力组合到一起"，但它只发生在 TypeScript 的类型系统里，没有 Go 那样的运行时嵌入和字段提升。**

这个类比对于理解 `&` 的用途是很有帮助的。
