# **Key takeaways**

- emplace_back(“str”): inplace-new, no emptobject, no copy, no move

- push_back(std::move(tmp_str)) almost equal to emplace_back(std::move(tmp_str))

emplace_back 的核心优势是 **<span class="mark">直接构造 + 完美转发</span>**，避免不必要的拷贝/移动。

源码层面，它通过 placement new + std::forward 实现高效构造。

在空间不足时，扩容逻辑和 push_back 类似（2 倍增长 + 元素移动）

# 

# **C++ vector push_back() 和 emplace_back() 区别**

在 C++ 中，push_back() 和 emplace_back() 都是 std::vector 的成员函数，用于在容器的末尾添加元素，但它们在实现方式和效率上有一些关键区别：

### **1. 参数传递方式**

- **push_back()**  
  接受一个 **已经构造好的对象**（或临时对象），然后通过 **拷贝构造** 或 **移动构造** 将其添加到 vector 末尾。

> std::vector\<std::string\> vec;
>
> std::string s = "hello";
>
> vec.push_back(s); // 拷贝构造
>
> vec.push_back(std::move(s)); // 移动构造（C++11）
>
> vec.push_back("world"); // 构造临时 string，再移动构造

- **emplace_back()**（C++11 引入）  
  直接在 vector 的内存中 **原地构造（in-place construction）** 对象，接受的是 **构造参数**，而非对象本身。

> std::vector\<std::string\> vec;
>
> vec.emplace_back("hello"); // 直接调用 std::string(const char\*)，无需拷贝或移动

### **2. 性能差异**

- 对于 **非平凡类型（如 std::string、自定义类）**，emplace_back() 通常更高效，因为它避免了 **临时对象的构造和拷贝/移动**。

- 对于 **基本类型（如 int、double）**，两者性能几乎相同。

**示例对比：**

std::vector\<std::pair\<int, std::string\>\> vec;

// push_back: 需要构造临时 pair，再移动

vec.push_back({1, "foo"}); // 构造临时 pair，再移动

// emplace_back: 直接构造

vec.emplace_back(1, "foo"); // 直接在 vector 内存中构造 pair

### **3. 异常安全性**

- push_back() 在拷贝/移动时可能抛出异常。

- emplace_back() 在构造时可能抛出异常，但少了一次潜在拷贝/移动的异常风险。

### **4. 使用场景**

- **优先用 emplace_back()**：

  - 当传递的是构造参数（而非对象本身）时。

  - 对象类型较复杂（如 std::string、自定义类）。

- **仍然可以用 push_back()**：

  - 代码需要兼容 C++98/03。

  - 已经有一个现成的对象（直接传递对象更清晰）。

### **5. 示例代码**

\#include \<vector\>

\#include \<string\>

int main() {

std::vector\<std::string\> vec;

// push_back

std::string s = "hello";

vec.push_back(s); // 拷贝构造

vec.push_back(std::move(s)); // 移动构造

vec.push_back("world"); // 构造临时 string，再移动构造

// emplace_back

vec.emplace_back("emplace"); // 直接构造，无临时对象

return 0;

}

### **总结**

| **特性**       | **push_back()**     | **emplace_back()**       |
|----------------|---------------------|--------------------------|
| **参数类型**   | 对象（拷贝/移动）   | 构造参数（直接构造）     |
| **性能**       | 可能多一次拷贝/移动 | 通常更高效               |
| **适用场景**   | C++98/03，已有对象  | C++11+，直接传递构造参数 |
| **代码清晰度** | 明确表示插入对象    | 明确表示就地构造         |

在 C++11 及以后，**优先使用 emplace_back()**，除非有特殊需求（如兼容旧代码或语义更清晰）。

# **比较emplace_back(std::move(tmp)); and push_back(std::move(tmp));**

# 

1\)

string tmp("str);

vec.emplace_back(std::move(tmp));

2\)

string tmp("str);

vec.push_back(std::move(tmp));

你列出的两个代码片段都使用了 std::move 来转移 tmp 的所有权，但它们的底层行为仍然有所不同。下面详细分析它们的区别：

## **1. vec.emplace_back(std::move(tmp))**

### **行为**

- std::move(tmp) 将 tmp 转换为右值引用（std::string&&）。

- emplace_back 接受变长参数包（Args&&... args），并 **直接转发给 std::string 的构造函数**。

- 由于参数是 std::string&&，它会调用 **移动构造函数（std::string(std::string&&)）**，在 vector 的内存中直接构造新 string。

### **代码等效**

vec.emplace_back(std::move(tmp));

// 近似于：

vec.emplace_back(std::string(std::move(tmp))); // 直接调用移动构造

### **效率**

- **1 次移动构造**（无临时对象，直接在 vector 内存中构造）。

## **2. vec.push_back(std::move(tmp))**

### **行为**

- std::move(tmp) 同样将 tmp 转为右值引用（std::string&&）。

- push_back 的重载版本接受 std::string&&，并调用 **移动构造函数** 插入 vector。

### **代码等效**

vec.push_back(std::move(tmp));

// 近似于：

vec.push_back(std::string(std::move(tmp))); // 调用移动构造

### **效率**

- **1 次移动构造**（和 emplace_back 相同）。

## **关键区别**

| **特性** | **emplace_back(std::move(tmp))** | **push_back(std::move(tmp))** |
|----|----|----|
| **底层调用** | 直接转发参数，调用移动构造 | 显式调用移动构造 |
| **临时对象** | ❌ 无 | ❌ 无 |
| **适用场景** | 更通用（支持变长参数） | 仅适用于已有对象 |
| **编译器优化** | 可能更易优化 | 优化机会较少 |

## **结论**

- **在 std::move 的情况下，两者性能几乎相同**，都会调用移动构造。

- **emplace_back 的优势在于更灵活的构造方式**（如 emplace_back(1, "str") 构造 std::pair）。

- **push_back 适用于已有对象**，语义更明确。

### **推荐写法**

- 如果只是移动一个已有对象，两者均可：

> vec.push_back(std::move(tmp)); // 清晰表明“移动插入”
>
> vec.emplace_back(std::move(tmp)); // 同样高效，但稍显冗余

- 如果是直接构造（无临时对象），优先 emplace_back：

> vec.emplace_back("str"); // 直接构造，无拷贝/移动
