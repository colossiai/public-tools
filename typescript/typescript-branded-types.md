# 什么是branded types

TypeScript Branded Types（有时候也被称为 Opaque Types 或者是 Nominal Types）是 TypeScript 中一种非常聪明的“障眼法”。
简单来说，它的作用是在编译阶段，强行把两个结构完全一样的数据类型拆分成两个不同的类型，从而避免代码中出现低级的设计失误（比如把 UserId 误当成 PostId 传入了函数）。

### 1. 为什么需要 Branded Type？

TypeScript 的类型系统是结构化的（Structural Typing）。这意味着，只要两个类型的结构长得一样，TypeScript 就认为它们是同一种类型。
看一个最常见的翻车现场：

```typescript
type UserId = string;
type PostId = string;

function deleteUser(id: UserId) {
  console.log(`Deleting user ${id}`);
}

const myPostId: PostId = "post_12345";

// 🚨 糟糕！这里完全不会报错，因为它们在底层都是 string！
deleteUser(myPostId); 在上面的代码中，我们本意是想让 UserId 和 PostId 独立开来，但因为它们本质上都是 string，TypeScript 没能帮我们拦住这个低级错误。
```

### 2. 什么是 Branded Type 的原理？
为了解决这个问题，我们可以给原有的类型打上一个独一无二的“烙印”（Brand）。
我们在原有类型（比如 string）的基础上，联合一个永远不可能在真实运行时存在的幽灵属性。

// 1. 定义烙印类型

```typescript
type Brand<K, T> = K & { __brand: T };
```

// 2. 创造专属的 Branded Types

```typescript
type UserId = Brand<string, 'UserId'>;
type PostId = Brand<string, 'PostId'>;这里的 { brand: 'UserId' } 就是那个烙印。在实际写代码时，没有任何一个真实的字符串会带有 brand 属性，它纯粹是给 
```
TypeScript 编译器看的。


### 3. 如何使用它？
既然真实的数据没有 __brand 属性，我们要怎么生成这种类型呢？通常需要使用类型断言（Type Assertion）来当做“类型转换器”：
// 类型转换函数（通常封装在专门的工具函数中）

```typescript
function createUserId(id: string): UserId {
  return id as UserId;
}

function createPostId(id: string): PostId {
  return id as PostId;
}

// 实际使用：
const myUserId = createUserId("user_999");
const myPostId = createPostId("post_888");

function deleteUser(id: UserId) {
  console.log(`用户已删除: ${id}`);
}

// 示例：
deleteUser(myUserId); // ✓ 完美通过！

// deleteUser(myPostId); 
// 🚨 报错：类型 'PostId' 的参数不能赋给类型 'UserId' 的参数。
// 因为 'PostId' 的烙印是 'PostId'，而函数需要的是 'UserId'！### 总结
```


> Branded Type 的本质：它没有改变运行时的任何一行数据结构（在打包成 JS 后，它们依然是普通的字符串或数字），但它通过在编译期“无中生有”一个属性，强行让 TypeScript 的结构化类型系统变成了名义化（Nominal）类型系统。
> 
这种技巧在大型项目中非常实用，特别是用于区分：
 * 各种实体的 ID（UserId, OrderId, ItemId）
 * 不同的安全级别字符串（RawHtml 相对 SanitizedHtml）
 * 不同的数值单位（Celsius 相对 Fahrenheit）


# Branded Type 看起来是按shape识别类型的反作用


你直觉非常准，一针见血！
Branded Type 的本质，确实就是对 TypeScript 默认的 “按形状识别类型”（结构化类型系统 / Structural Typing） 的一种反叛和修正。
我们可以从以下两个视角来看待这种“反作用”：

### 1. 结构化类型（Shape）的短板

TypeScript 的核心设计理念是：*如果它走起来像鸭子，叫起来也像鸭子，那它就是鸭子。*
这种设计在前端开发中极其爽快，比如你传一个带有 name 和 age 的对象给函数，只要形状对上了，管你是从哪个类 new 出来的，都能完美运行。
但是在某些场景下，“形状相同”不代表“语义相同”。
 * string 的形状都一样：UserId（"123"）和 PostId（"123"）的形状完全一模一样，都是一个字符串。
 * number 的形状也都一样：USD（100）和 EUR（100），或者 Celsius（37）和 Fahrenheit（37），它们的形状都是数字。
这时候，完全依赖 Shape 识别类型，就会让类型系统失去防御性。


### 2. 强行开启“名义化类型”（Nominal Typing）

世界上还有另一种主流的类型系统，叫做名义化类型系统（Nominal Typing），比如 Java、C++。在这些语言里，即使两个 Class 的属性和方法一模一样，只要类名不同，它们就绝对不能混用。
Branded Type 的骚操作就在于： 它在 TypeScript 这个“按 Shape 识别”的引擎里，利用“给 Shape 强行塞一个独一无二的隐形属性”的手段，硬生生模拟出了 Java 那种“按名字识别”的效果。
所以，它确实是反作用——它是为了在特定逻辑严密的业务场景下，局部关闭 TypeScript 的“按 Shape 识别”特性，转而开启“按名字识别”的防御机制。


> 一句话总结：
> TypeScript 默认是“认衣服不认人”（衣服一样就行）；而 Branded Type 是在衣服上贴了个“工牌”（有工牌才行），硬生生把按衣服识别，变成了按身份识别。
>