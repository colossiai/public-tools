理解JDK 21的内存区域分布，对于优化应用性能和排查内存问题至关重要。下面这个表格汇总了主要的内存区域及其关键细节：

| 内存区域 | 存储内容 | 特点与管理 | 相关VM参数/工具 |
| :--- | :--- | :--- | :--- |
| **Java堆 (Heap)** | 对象实例、数组 | - **所有线程共享**，GC主要区域<br>- **分代设计**：年轻代（Eden, Survivor）、老年代<br>- **可固定大小或动态扩展** | `-Xms`, `-Xmx`, `-XX:+HeapDumpOnOutOfMemoryError`, `jmap` |
| **堆外内存 (Non-Heap)** | | | |
| ├─ **元空间 (Metaspace)** | 类元数据、方法信息、常量池等 | - **取代永久代 (PermGen)**<br>- **使用本地内存**，默认无上限<br>- **类加载器卸载时回收** | `-XX:MaxMetaspaceSize`, `-XX:MetaspaceSize` |
| ├─ **代码缓存 (Code Cache)** | JIT编译后的本地代码 | - 存放**热点代码的编译结果**<br>- 内存不足时触发**清理** | `-XX:ReservedCodeCacheSize`, `-XX:InitialCodeCacheSize` |
| ├─ **线程栈 (Thread Stack)** | 栈帧、局部变量、方法调用 | - **每个线程私有**<br>- 栈帧伴随方法调用/结束入栈/出栈<br>- **溢出**导致`StackOverflowError` | `-Xss` |
| ├─ **直接内存 (Direct Memory)** | `DirectByteBuffer`引用的数据 | - **NIO操作使用**，避免Java堆与本地堆间复制<br>- **受JVM管控**，但不在堆上<br>- **分配失败可触发GC** | `-XX:MaxDirectMemorySize`, **NMT** |
| **其他/本地内存** | JVM自身、第三方库（如JNI）分配 | - **不受JVM内存参数直接限制**<br>- 排查需借助**系统工具** | **NMT**, `pmap`, `jemalloc` |

### 🔍 如何监控与分析内存

了解内存分布后，掌握监控和分析方法很重要：

- **开启NMT监控堆外内存**：在启动参数中添加 `-XX:NativeMemoryTracking=detail`，然后使用 `jcmd <pid> VM.native_memory detail` 命令查看。NMT报告能清晰显示各内存区域的提交和保留内存。

- **生成堆转储分析堆内存**：设置 `-XX:+HeapDumpOnOutOfMemoryError` 参数，在内存溢出时自动生成堆转储文件。也可以使用 `jmap -dump:format=b,file=heap.bin <pid>` 手动生成，然后用MAT、JProfiler等工具分析。

- **使用系统工具辅助分析**：当怀疑是JVM之外的内存问题（例如由本地库分配）时，可以借助 `pmap`、`jemalloc` 等操作系统层面的工具来排查。

### 💎 重要提示

请注意，**直接内存（Direct Memory）的占用在NMT中通常被归类在"Other"项下**。所以，如果你在代码中大量使用了`DirectByteBuffer`，当发现"Other"区域的内存增长时，应优先考虑是否是直接内存使用所致。

希望这份说明能帮助你。如果你在实际应用中遇到了具体的内存问题，例如频繁的Full GC或堆外内存缓慢增长，欢迎提供更多细节，我们可以一起探讨更具体的优化方案。