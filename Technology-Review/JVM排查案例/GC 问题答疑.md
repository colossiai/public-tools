**如何监控JVM Full GC, Yeung GC**

监控 JVM 的 Full GC 可以帮助你优化应用程序的性能。以下是一些方法：

1.  **使用垃圾回收日志（GC Log）**：在 JVM 启动时，通过添加以下参数来开启垃圾回收日志：-Xloggc:/path/to/gc.log -XX:+PrintGCDetails。这将记录 Full GC 的次数和时间。

2.  **使用 jstat 工具**：jstat 是 JDK 自带的一个实用监控工具，可以提供关于垃圾回收、类加载和编译的信息。使用 -gc 选项并指定进程 ID，可以更精确地监控 GC 过程。

3.  **使用 Spring Boot Actuator 和 Prometheus**：如果你使用 Spring Boot，可以结合 Spring Boot Actuator、Prometheus 和 Grafana 来监控 GC 状态。这种方案可以提供更全面的监控和图形展示。

总之，监控 Full GC 可以帮助你定位性能问题并采取相应的优化措施。

监控 JVM 的 Young GC 可以帮助你优化应用程序的性能。以下是一些方法：

1.  [<u>**使用 jstat 工具**：jstat 是 JDK 自带的一个实用监控工具，可以提供关于垃圾回收、类加载和编译的信息。使用</u> <u>-gc</u> <u>选项并指定进程 ID，可以更精确地监控 Young GC 过程<sup>1</sup></u>](https://zhuanlan.zhihu.com/p/558750756)。

2.  **查看 GC log**：打印 GC log 需要在 JVM 启动参数里添加如下参数：

    - -XX:+PrintGCDateStamps：打印 GC 发生的时间戳。

    - -XX:+PrintTenuringDistribution：打印 GC 发生时的代龄信息。

    - -XX:+PrintGCApplicationStoppedTime：打印 GC 停顿时长。

    - -XX:+PrintGCApplicationConcurrentTime：打印 GC 间隔的服务运行时长。

    - -XX:+PrintGCDetails：打印 GC 详情，包括 GC 前/内存等。

    - -Xloggc:/path/to/gc.log.date：指定 GC log 的路径。

<u>[总之，通过监控 Young GC，你可以定位性能问题并采取相应的优化措施。](https://zhuanlan.zhihu.com/p/558750756)[<sup>2</sup>](https://zhuanlan.zhihu.com/p/420376874)</u>

**Java 调用system.gc() 会增加 新生代的年龄吗**

[<u>在默认情况下，通过</u> <u>System.gc()</u> <u>或者</u> <u>Runtime.getRuntime().gc()</u> <u>的调用，会显式触发 Full GC，同时对**老年代**和**新生代**进行回收，尝试释放被丢弃对象占用的内存<sup>1</sup>。然而，System.gc()</u> <u>调用附带一个免责声明，无法保证对垃圾收集器的调用（即不能确保立即生效）<sup>1</sup>。JVM 实现者可以通过</u> <u>System.gc()</u> <u>调用来决定 JVM 的 GC 行为。一般情况下，垃圾回收应该是自动进行的，无须手动触发。在一些特殊情况下，如编写性能基准，我们可能需要手动触发 Full GC 来控制内存回收<sup>1</sup></u>](https://blog.csdn.net/qq_49644209/article/details/124544046)。

关于新生代的年龄增加，让我们深入了解一下：

1.  [<u>**年轻代 (Young Generation)**：年轻代用来存放新近创建的对象。它被划分为三个区域：Eden、S0、S1。对象在 Eden 出生后，在经过一次 Minor GC 后，如果对象还存活，并且能够被另外一块 Survivor 区域所容纳，则使用复制算法将这些仍然存活的对象复制到另外一块 Survivor 区域中。然后清理所使用过的 Eden 和 Survivor 区域，并且将这些对象的年龄设置为 1。以后对象在 Survivor 区每熬过一次 Minor GC，就将对象的年龄 + 1。当对象的年龄达到某个值时（默认是 15 岁，可以通过参数</u> <u>-XX:MaxTenuringThreshold</u> <u>来设定），这些对象就会成为老年代。但对于较大的对象，直接进入老年代<sup>2</sup></u>](https://blog.csdn.net/Vermont_/article/details/113804379)。

2.  [<u>**老年代 (Old Generation)**：主要存放应用程序中生命周期长的内存对象。老年代的对象比较稳定，所以 Major GC 不会频繁执行。在进行 Major GC 前一般都先进行了一次 Minor GC，使得有新生代的对象晋身入老年代，导致空间不够用时才触发。当老年代也满了装不下的时候，就会抛出 OOM（Out of Memory）异常<sup>2</sup></u>](https://blog.csdn.net/Vermont_/article/details/113804379)。

[<u>总之，System.gc()</u> <u>调用会触发 Full GC，但具体的 GC 行为由 JVM 实现者决定。新生代的年龄增加是通过对象在 Survivor 区的存活次数来决定的，达到一定年龄后会晋升到老年代。<sup>2</sup></u>](https://blog.csdn.net/Vermont_/article/details/113804379)[<sup><u>3</u></sup>](https://blog.csdn.net/qq_27184497/article/details/117828331)
