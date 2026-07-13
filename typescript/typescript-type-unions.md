# TypeScript 中的 Union（联合类型） 其实非常直观。你可以把它想象成逻辑上的 “或（OR）”。它允许一个变量在不同的时间点拥有多种不同类型中的一种。
当我们想让代码保持灵活，但又不希望用 any 彻底放弃类型检查时，联合类型就是最佳选择。
## 1. 基础语法
使用竖线 | 来分隔不同的类型：

```typescript
let id: string | number;

id = 101;       // 没问题，是 number
id = "A-101";   // 没问题，是 string
// id = true;   // 报错！布尔值不在 string | number 的范围内## 2. 核心痛点：类型收窄 (Type Narrowing)
```

当你使用联合类型时，TypeScript 会变得非常“谨慎”。如果一个变量可能是 string 也可能是 number，你不能直接对它调用字符串的专属方法（比如 .toUpperCase()），因为如果它此时是数字，程序就会崩溃。
你必须先向 TypeScript 证明当前变量的具体类型。这个过程叫做 类型收窄（Type Narrowing）。
### 常见的收窄方法：typeof 检查

```typescript
function printId(id: string | number) {
  // 如果直接 id.toUpperCase() 会报错

  if (typeof id === "string") {
    // 在这个大括号内部，TypeScript 100% 确定 id 是 string
    console.log(id.toUpperCase());
  } else {
    // 在这个 else 内部，TypeScript 自动推断出 id 只能是 number
    console.log(id.toFixed(2));
  }
}
```

## 3. 高级进阶：可辨识联合 (Discriminated Unions)
当你处理复杂的对象（Object）时，纯靠 typeof 就搞不定了。这时候，业界最常使用的黄金法则叫 “可辨识联合类型”。
做法很简单：在每个对象类型里，放一个同名的字面量字段（通常叫 kind 或 type）作为“标签”，用来区分它们。

```typescript
interface NetworkLoadingState {
  state: "loading"; // 这里的 "loading" 是一个具体的字面量值，而不是普通的 string
}

interface NetworkFailedState {
  state: "failed";
  code: number;
}

interface NetworkSuccessState {
  state: "success";
  data: string;
}

// 组合成一个联合类型
type NetworkState = NetworkLoadingState | NetworkFailedState | NetworkSuccessState;

function handleState(state: NetworkState) {
  // 通过共同的标签字段 'state' 进行收窄
  switch (state.state) {
    case "loading":
      return "正在加载中...";
    case "failed":
      // 此时 TypeScript 知道这里有 code 属性
      return `加载失败，错误码: ${state.code}`;
    case "success":
      // 此时 TypeScript 知道这里有 data 属性
      return `加载成功，数据为: ${state.data}`;
  }
}
```

## 💡 总结与避坑指南
> ⚠️ 记住一个核心逻辑：
>  * 赋值时（放宽限制）： 联合类型是 扩大 了变量可以接受的范围（既能给它字符串，也能给它数字）。
>  * 使用时（严格限制）： 在你真正去调用它的属性或方法时，TypeScript 只允许你访问所有联合类型共同拥有的成员。想用专属功能？必须先用 if 或 switch 进行类型收窄。
>



# TypeScript中Exhaustiveness指什么

在 TypeScript 中，Exhaustiveness（穷举性检查 / 完备性检查） 指的是：确保你在处理一个“联合类型（Union）”时，把所有可能出现的情况都覆盖到了，没有任何遗漏。
如果漏掉了某种情况，TypeScript 应该在编译时就对你发出警告，而不是等到代码在线上运行时报错。这通常在处理 可辨识联合类型（Discriminated Unions） 时配合 switch 或 if-else 使用。
## 1. 为什么要追求 Exhaustiveness？
想象一下，你正在开发一个支付系统，原本只有两种支付方式：

```typescript
interface WeChatPay { type: 'wechat'; }
interface AliPay { type: 'alipay'; }

type PaymentMethod = WeChatPay | AliPay;你在后台写了一个处理支付的函数：
function processPayment(method: PaymentMethod) {
  switch (method.type) {
    case 'wechat': return '处理微信支付';
    case 'alipay': return '处理支付宝';
  }
}
```

半年后，业务扩大，另一个同事在 PaymentMethod 联合类型里加了一个 { type: 'stripe' }。
如果你的 processPayment 函数没有做穷举性检查，TypeScript 默认不会报错。当用户发起 Stripe 支付时，代码会默默跳过 switch，返回一个 undefined，线上故障就此诞生。


## 2. 如何在 TypeScript 中实现穷举检查？
业界最常用、也最推荐的做法，是利用 TypeScript 的 never 类型。
never 类型在 TypeScript 中代表“永远不可能发生的值”。如果一个变量的所有可能类型都被你用 case 或 if 过滤完了，那么最后剩下的变量，它的类型就会自动收窄为 never。
利用这个特性，我们可以写一个保底的 default 分支：

```typescript
interface WeChatPay { type: 'wechat'; }
interface AliPay { type: 'alipay'; }
interface StripePay { type: 'stripe'; } // 新增的类型

type PaymentMethod = WeChatPay | AliPay | StripePay;

function processPayment(method: PaymentMethod) {
  switch (method.type) {
    case 'wechat':
      return '处理微信支付';
    case 'alipay':
      return '处理支付宝';
    // ❌ 假设我们忘记写 case 'stripe' 了
    
    default:
      // 报错！因为 method 此时还有可能是 StripePay，不能赋值给 never
      const _exhaustiveCheck: never = method; 
      return _exhaustiveCheck;
  }
}
```

### 为什么会报错？
因为你漏掉了 stripe，所以在 default 分支里，TypeScript 认为 method 的类型此时是 StripePay。你试图把一个 StripePay 赋值给 never 类型的变量 _exhaustiveCheck，这违反了类型安全，TS 就会在编译时大喊：“你漏掉东西了！”
只要你加上 case 'stripe'，default 里的 method 就会真正变成 never，报错瞬间消失。

## 3. 另外两种实现方案

除了声明一个 never 变量，还有两种很常见的手段：

### 方案 A：封装一个断言函数 (AssertNever)
为了代码更优雅，你可以封装一个全局的辅助函数：

```typescript
function assertNever(x: never): never {
  throw new Error("Unexpected object: " + x);
}

// 在 switch 中使用：
switch (method.type) {
  case 'wechat': return '微信';
  case 'alipay': return '支付宝';
  default: 
    return assertNever(method); // 如果漏写了，这里也会在编译时报错
}

*这样做的好处是，不仅编译时能检查，万一以后有人用原生 JS 绕过了类型检查传进错的值，运行时也会立刻抛错，双重保险。*


### 方案 B：开启 noImplicitReturns 编译选项
在你的 tsconfig.json 中，可以开启这个配置：

```json
{
  "compilerOptions": {
    "noImplicitReturns": true
  }
}
```

开启后，如果你的函数有返回类型（比如上面代码隐式返回字符串），而你的 switch 漏掉了某种情况导致有些路径没有 return 值，TypeScript 就会直接报错。不过这个属于全局配置，不如 never 断言那么精准。


> 💡 核心总结：
> Exhaustiveness 就像是给你的代码装了一个安全警报器。当你利用 never 类型做好了完备性检查，以后无论团队怎么修改、增加联合类型，TypeScript 都会逼着大家把所有配套的逻辑都补齐，极大地提升了大型项目的重构安全性。
>