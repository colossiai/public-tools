# Java virtual thread best practices.

Java virtual threads, introduced as a preview feature and stabilized in JDK 21, are designed to help you write, maintain, and debug high-throughput concurrent applications more easily. Their power comes from efficiently handling a massive number of concurrent tasks, but to get the best results, it's important to follow established best practices.

The table below summarizes the key guidelines for using virtual threads effectively.

| Practice Category | Do's | Don'ts |
| :--- | :--- | :--- |
| **Task Selection & Application** | Use for **I/O-bound** tasks (e.g., HTTP clients, JDBC queries). | Don't use for **CPU-intensive** tasks; use platform threads or parallel streams instead. |
| **Thread Management** | Use `Executors.newVirtualThreadPerTaskExecutor()` for one virtual thread per task. | **Never pool virtual threads**; they are cheap and designed to be ephemeral. |
| **Resource Limitation** | Use **`Semaphore`** to control access to limited resources (e.g., database connections). | Don't use a fixed-size pool of virtual threads to limit concurrency. |
| **Synchronization & Pinning** | Replace `synchronized` with `ReentrantLock` for long I/O operations to avoid pinning. | Avoid running blocking I/O inside `synchronized` blocks or methods. |
| **State Management** | Use **`Scoped Values`** for immutable data sharing; be cautious with `ThreadLocal` to avoid memory leaks. | Don't cache large, expensive objects in `ThreadLocal` variables. |

### 🚀 How to Use Virtual Threads Effectively

Adopting the right patterns is crucial for leveraging the scalability of virtual threads.

- **Embrace Structured Concurrency**: For managing multiple related tasks, use `StructuredTaskScope` from the `java.util.concurrent` package. This model treats groups of related tasks as a single unit of work, ensuring that if one task fails, others are cancelled, and that the main thread waits for all subtasks to complete before continuing, leading to more robust and maintainable code.
- **Migrate from Reactive Programming**: If your codebase uses complex reactive frameworks like Reactor or RxJava primarily for scalability, virtual threads can offer a compelling simplification. You can often migrate back to a simpler, synchronous blocking style without sacrificing throughput, making the code easier to write, read, and debug.

### 🔧 Monitoring and Debugging

To ensure your application is running smoothly with virtual threads, you need the right observability tools.

- **Detect Pinning with JFR**: Use Java Flight Recorder (JFR) to monitor for the `jdk.VirtualThreadPinned` event, which is enabled by default. This helps identify instances where a virtual thread is pinned to its carrier thread for longer than a threshold (default: 20ms), highlighting potential scalability bottlenecks.
- **Debug with Command-Line Flags**: For immediate feedback during development, you can use the JVM flag `-Djdk.tracePinnedThreads=full` (or `=short`). This will print stack traces when a virtual thread is pinned, helping you quickly locate the problematic `synchronized` block.

By following these best practices, you can fully harness the power of virtual threads to build highly scalable and maintainable Java applications. I hope this guide provides a solid foundation. If you have a more specific scenario in mind, feel free to ask