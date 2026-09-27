C++11标准原子库内存顺序memory_order_consume与memory_order_acquire的差异示例

贺志国

在C++11标准原子库中，大多数函数接收一个memory_order参数：

enum memory_order {

memory_order_relaxed,

memory_order_consume,

memory_order_acquire,

memory_order_release,

memory_order_acq_rel,

memory_order_seq_cst

};

1

2

3

4

5

6

7

8

**<span class="mark">上述枚举变量虽然有六个选项，但仅代表三种内存模型：</span>**

**<span class="mark">（1）顺序一致序(sequentially consistent，即memory_order_seq_cst)</span>**

**<span class="mark">（2）获取-释放序(memory_order_consume, memory_order_acquire, memory_order_release、memory_order_acq_rel)</span>**

**<span class="mark">（3）自由序(或者叫松弛序，memory_order_relaxed)。</span>**

除非为特定的操作指定一个内在顺序选项，内存顺序默认都是memory_order_seq_cst。

memory_order_consume和memory_order_acquire都为了同一个目的：帮助非原子信息在线程间安全的传递。就像获取操作（memory_order_acquire）一样，消费操作（memory_order_consume）必须与另一个线程的释放操作（memory_order_acquire）一起使用。它们的差异在于：memory_order_acquire保证配对使用的 memory_order_release操作之前的所有原子和非原子的写入操作有效，但memory_order_consume仅保证配对使用的 memory_order_release操作之前的所有原子的写入操作和依赖原子写入的非原子操作有效。

这段话听起来很拗口，下面使用一个示例来说明：

\#include \<atomic\>

\#include \<cassert\>

\#include \<iostream\>

\#include \<string\>

\#include \<thread\>

int a;

std::atomic\<std::string\*\> ptr;

void Write() {

std::string\* p = new std::string("Hello World.");

a = 30;

ptr.store(p, std::memory_order_release);

}

void Read() {

// std::memory_order_acquire保证

// ptr.store(p, std::memory_order_release);

// 之前的a = 30; 一定会先执行，

// 但std::memory_order_consume无法保证这点。

std::string\* p2;

while (!(p2 = ptr.load(std::memory_order_acquire))) {

// Do nothing, it is just busy waiting!

}

std::cout \<\< "\*p2 must be 'Hello World'.\n";

assert(\*p2 == "Hello World.");

delete p2;

// 注意：

// X86平台上所有内存顺序无差别，第22行代码使用任何内存顺序获取原子变量的值，

// 下述断言都会成功。但在ARM平台上，如果前面使用

// std::memory_order_consume， 断言可能失败。

std::cout \<\< "a must be 30.\n";

assert(a == 30);

}

int main() {

a = 0;

ptr.store(nullptr, std::memory_order_relaxed);

std::thread write_thread(Write);

std::thread read_thread(Read);

write_thread.join();

read_thread.join();

return 0;

}

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

21

22

23

24

25

26

27

28

29

30

31

32

33

34

35

36

37

38

39

40

41

42

43

44

45

46

47

48

上述代码中，p2 = ptr.load(std::memory_order_acquire)中的获取序确保了与之配对的ptr.store(p, std::memory_order_release);（写入序）之前所有原子与非原子操作代码：

std::string\* p = new std::string("Hello World.");

a = 30;

1

2

全部生效。实际上，std::memory_order_acquire有点类似于互斥锁的lock操作，而std::memory_order_release类似于互斥锁的unlock操作。因此两个断言：

assert(\*p2 == "Hello World.");

assert(a == 30);

1

2

一定会成功。

如果将上述代码片段

while (!(p2 = ptr.load(std::memory_order_acquire))) {

// Do nothing, it is just busy waiting!

}

1

2

3

中的内存序由std::memory_order_acquire（获取序）换成std::memory_order_consume（消费序），即Read() 函数变为如下片段：

void Read() {

std::string\* p2;

while (!(p2 = ptr.load(std::memory_order_consume))) {

// Do nothing, it is just busy waiting!

}

// 绝不可能失败，\*p2 从 ptr 携带依赖\*p，ptr更新时，\*p中的内容一定会更新。

std::cout \<\< "\*p2 must be 'Hello World'.\n";

assert(\*p2 == "Hello World.");

delete p2;

// 可能失败，也可能不失败：a不从 ptr 携带依赖

std::cout \<\< "a must be 30.\n";

assert(a == 30);

}

15

则第一个断言assert(\*p2 == "Hello World.");绝不可能失败，虽然\*p2是非原子变量，但它从原子变量ptr 携带依赖\*p，p虽然是非原子变量，但其值要赋给原子变量ptr，于是在原子变量ptr更新时，确保了p中的内容一定会更新。第二个断言assert(a == 30);可能失败也可能不会失败，因为非原子变量a 不从原子变量ptr 携带依赖，所以无法保证a的值已被更新。

CMake构建文件如下：

cmake_minimum_required(VERSION 3.0.0)

project(memory_order VERSION 0.1.0)

set(CMAKE_CXX_STANDARD 14)

add_executable(\${PROJECT_NAME} \${PROJECT_NAME}.cpp)

find_package(Threads REQUIRED)

target_link_libraries(\${PROJECT_NAME} \${CMAKE_THREAD_LIBS_INIT})

include(CTest)

enable_testing()

set(CPACK_PROJECT_NAME \${PROJECT_NAME})

set(CPACK_PROJECT_VERSION \${PROJECT_VERSION})

include(CPack)

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

在X86平台上的运行结果如下（事实上，在X86平台上使用任何内存序都会成功）：

./memory_order

\*p2 must be 'Hello World'.

a must be 30.

1

2

3

注意：<span class="mark">memory_order_consume这个内存序非常特殊，主流编译器直接将它当成memory_order_acquire处理</span>。**<span class="mark">“C++ Concurrency In Action”（第二版，2019）一书作者认为memory_order_consume不应该出现在实际的代码中，即使在C++17中也不推荐使用。</span>**

————————————————

版权声明：本文为博主原创文章，遵循 CC 4.0 BY-SA 版权协议，转载请附上原文出处链接和本声明。

原文链接：https://blog.csdn.net/davidhopper/article/details/131245310
