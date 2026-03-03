# Show comprehensive advanced java troubleshooting skills


Absolutely — let’s go deep into **advanced Java troubleshooting skills**, covering a range of practical techniques, tools, and methodologies that experienced Java engineers use to diagnose, debug, and optimize complex applications. I’ll break this into structured areas for clarity.

---

## 1. **Understanding and Analyzing Logs**

* **Structured logging**: Use frameworks like **SLF4J + Logback** or **Log4j2** with JSON outputs to allow centralized aggregation.
* **Log correlation**: Always include **trace IDs** in microservices or async workflows.
* **Dynamic log level**: Many frameworks support runtime log-level changes without restarting.
* **Pattern identification**: Look for:

  * Repeated exceptions
  * Unexpected thread states
  * Slow request traces

**Example**:

```java
logger.info("Order processed successfully. orderId={}, userId={}", orderId, userId);
```

This allows easier filtering for specific transactions.

---

## 2. **Memory Troubleshooting**

* **Heap analysis**:

  * Use `jmap -dump:format=b,file=heap.hprof <pid>` to generate a heap dump.
  * Analyze with **Eclipse MAT** or **VisualVM**.
* **Common problems**:

  * Memory leaks → persistent object retention
  * High GC overhead → frequent Full GCs
  * PermGen / Metaspace exhaustion (Java 8+ uses Metaspace)
* **Tips**:

  * Enable GC logging:

    ```bash
    -Xlog:gc*,gc+age=trace:file=gc.log:time,uptime,level,tags
    ```
  * Use **Flight Recorder / Mission Control** for real-time memory profiling.

---

## 3. **Thread and Concurrency Issues**

* **Deadlocks**:

  * Detect with `jstack <pid>` and look for cycles in thread locks.
* **Thread dumps**:

  * Useful for detecting live threads, stuck locks, or high CPU consumers.
  * Analyze blocked, waiting, and runnable threads.
* **Tools**:

  * **VisualVM**, **JConsole**, **Async-profiler**, **YourKit**
* **Common patterns to check**:

  * Misuse of `synchronized` blocks
  * Thread starvation due to fixed thread pool exhaustion
  * Improper use of `CompletableFuture` causing infinite blocking

**Example command**:

```bash
jstack -l <pid> > threaddump.txt
```

---

## 4. **Performance Profiling and Hotspots**

* **Profiling tools**:

  * **JFR (Java Flight Recorder)** + **JMC (Java Mission Control)**
  * **Async-profiler** for CPU, allocation, and lock profiling
  * **YourKit / VisualVM** for method-level hotspot analysis
* **Symptoms to investigate**:

  * High latency in microservices
  * Excessive GC pause times
  * CPU-bound tasks vs IO-bound tasks
* **Tactics**:

  * Compare production vs local dev metrics
  * Instrument suspicious methods with **Stopwatch** or **AOP logging**

---

## 5. **GC Tuning and Garbage Collection Troubleshooting**

* **Monitor GC metrics**:

  * `-XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:gc.log`
* **Common issues**:

  * Frequent minor GCs → consider larger young generation
  * Long Full GCs → consider **G1 GC** or **ZGC** for low-latency
* **Heap analysis strategy**:

  1. Identify object retention patterns.
  2. Look for "phantom reachable" objects.
  3. Adjust `-Xms`, `-Xmx`, and GC parameters accordingly.

---

## 6. **Deadlocks, Live Locks, and Starvation**

* **Deadlocks**:

  * Detect from thread dumps: threads waiting on each other’s locks
* **Live locks**:

  * Threads constantly yielding to each other but making no progress
* **Starvation**:

  * Thread pool exhaustion causing requests to queue indefinitely
* **Resolution strategies**:

  * Use `java.util.concurrent.locks` instead of `synchronized`
  * Add proper timeout and fallback mechanisms
  * Implement **backpressure** in reactive streams

---

## 7. **Classloading and Reflection Issues**

* **Common errors**:

  * `ClassNotFoundException` / `NoClassDefFoundError` → version mismatch
  * PermGen / Metaspace leak due to custom classloaders
* **Debugging**:

  * Use `-verbose:class` to trace class loading
  * Use `jcmd <pid> VM.class_hierarchy` for classloader hierarchy
* **Reflection pitfalls**:

  * Slow `Method.invoke()` for high-frequency calls
  * SecurityManager restrictions (if used)

---

## 8. **I/O, Network, and Database Troubleshooting**

* **Database**:

  * Use slow query logs and connection pool metrics
  * Monitor `HikariCP` or `DBCP` active/idle connections
* **Network**:

  * Detect socket leaks via `lsof -p <pid>` or `netstat`
  * Latency spikes → check DNS resolution, TCP backlog
* **I/O threads**:

  * Check NIO selectors for blocked or busy loops

---

## 9. **Native Memory and JNI Issues**

* **Symptoms**:

  * `OutOfMemoryError: Direct buffer memory`
  * Segmentation faults in native libraries
* **Analysis tools**:

  * `NMT (Native Memory Tracking)` via `-XX:NativeMemoryTracking=summary`
  * `valgrind` or `AddressSanitizer` for JNI code
* **Best practice**:

  * Always free native buffers (e.g., `ByteBuffer.allocateDirect` → `Cleaner.clean()`)

---

## 10. **Advanced Debugging Techniques**

* **Attach debugger to live process**:

  ```bash
  jcmd <pid> JDWP.start
  ```

* **Conditional breakpoints**: Trigger only under certain conditions to reduce noise.

* **Async debugging**:

  * Log async flow using **ThreadLocal trace IDs**
  * `CompletableFuture.whenComplete` or AOP advice for tracing

* **Hot patching / Runtime inspection**:

  * Use **BTrace** or **Byteman** for dynamic method tracing without stopping the JVM.

---

## 11. **Diagnostic Commands Cheat Sheet**

| Command                                     | Purpose                                    |
| ------------------------------------------- | ------------------------------------------ |
| `jstack <pid>`                              | Thread dump for deadlocks and live threads |
| `jmap -heap <pid>`                          | Heap usage summary                         |
| `jmap -dump:format=b,file=heap.hprof <pid>` | Full heap dump                             |
| `jcmd <pid> VM.flags`                       | JVM flags in use                           |
| `jcmd <pid> GC.heap_info`                   | Heap size & usage                          |
| `jcmd <pid> VM.native_memory summary`       | Native memory usage                        |
| `jconsole / jvisualvm`                      | GUI monitoring                             |

---

## 12. **Proactive Practices**

1. **Add metrics**: Micrometer + Prometheus for JVM metrics like GC, threads, memory.
2. **Chaos testing**: Simulate failures to uncover hidden deadlocks or resource leaks.
3. **Load testing**: Tools like **Gatling** or **JMeter** to stress-test threading and GC.
4. **Static analysis**: **SpotBugs**, **PMD**, **SonarQube** for catching concurrency and memory issues early.
5. **Dependency management**: Keep libraries updated to avoid subtle memory leaks or classloader issues.

---

Mastering these areas turns troubleshooting into a **systematic skill** instead of guesswork. Experienced Java engineers often combine:

* Logs → to understand symptoms
* Thread/heap dumps → to find root causes
* Profiling → to confirm hotspots
* JVM tuning → to prevent recurrence

---

If you want, I can make an **“Advanced Java Troubleshooting Workflow Diagram”**, showing exactly **which tools and steps to use depending on the problem symptom**, like memory, CPU, deadlock, or performance. It’s a very handy cheat sheet.

Do you want me to do that?
