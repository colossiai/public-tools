# Provide an example to troubleshoot CPU high load.

Here’s a practical, step-by-step example to troubleshoot high CPU usage in a Java app using JDK tools. It focuses on quickly mapping hot OS threads to Java stacks, identifying hot code paths, and confirming with lightweight profiling.

Prereqs
- You have JDK tools on the host (jcmd, jstack, jfr or JMC optional).
- You can run commands as the same user as the Java process.
- Replace <pid> with your JVM PID.

1) Find the target JVM
- List Java PIDs:
  - jcmd -l
  - or jps -l -v

2) Confirm CPU is actually high and find hot OS threads
Linux/macOS:
- Get overall CPU and the hot process:
  - top -H -p <pid>           # per-thread view (Linux)
  - or: ps -L -p <pid> -o pid,tid,psr,pcpu,pmem,comm
- Note the hottest thread’s TID (lightweight thread id). On Linux, convert it to hex to match jstack’s nid:
  - printf "0x%x\n" <TID>
- Optional: capture several samples:
  - for i in {1..5}; do date; top -H -b -n1 -p <pid> | head -n 40; sleep 2; done > top-samples.txt

Windows:
- Use Process Explorer or:
  - wmic path win32_perfformatteddata_perfos_thread where "IDProcess=<pid>" get Name,PercentProcessorTime,IDThread

3) Take multiple thread dumps and correlate
- Capture several jstack dumps a few seconds apart (while CPU is high):
  - jstack -l <pid> > jstack1.txt
  - sleep 3; jstack -l <pid> > jstack2.txt
  - sleep 3; jstack -l <pid> > jstack3.txt
- In each dump, search for the nid of the hot thread (e.g., nid=0x1a3b). Look for:
  - Thread state RUNNABLE with repeated identical top frames.
  - Tight loops in your code.
  - Hot library calls (e.g., regex, JSON parsing, logging).
  - Excessive lock spinning (parking/contended monitors).
  - Native hotspots (e.g., compression, crypto) if using -m with jstack.

Tips:
- If you see many threads BLOCKED on the same monitor, check the monitor owner and their stack.
- If the hot frames are in GC or JIT compiler threads, it may be GC pressure or compilation.

4) Quick GC/VM health check with jcmd
- Check heap usage and GC activity:
  - jcmd <pid> GC.heap_info
  - jcmd <pid> GC.run            # optional: see if CPU drops after a full GC
  - jcmd <pid> GC.class_histogram > histo.txt  # if suspect allocation churn
- Check safepoint/VM stats:
  - jcmd <pid> VM.uptime
  - jcmd <pid> VM.system_properties
  - jcmd <pid> VM.command_line
- If CPU is from allocations (allocation rate spikes), you’ll often see many RUNNABLE threads in new-object paths and frequent young GCs in jstat:
  - jstat -gc <pid> 1000

5) Low-overhead confirmation with Java Flight Recorder (JFR)
- Start a short profiling recording to capture CPU and allocation stacks:
  - jcmd <pid> JFR.start name=cpucheck settings=profile duration=120s filename=/tmp/cpu.jfr
- Exercise the workload during the window.
- Open cpu.jfr in Java Mission Control:
  - Check “Method Profiling (CPU)” or “Hot Methods/Hot Packages.”
  - Correlate hot methods with the thread dump findings.

6) Optional: On-CPU stack sampling without JFR (Linux)
- perf (requires root or perf_event perms):
  - perf top -p <pid>            # live view of hottest symbols
  - perf record -F 199 -g -p <pid> -- sleep 30
  - perf script | flamegraph.pl > flame.svg
- Async-profiler (if available) is excellent:
  - ./profiler.sh -d 30 -e cpu -f /tmp/cpu.svg <pid>

7) Common patterns and quick fixes
- Tight loop polling:
  - Symptom: Same app frames in RUNNABLE across dumps, no sleeps or waits.
  - Fix: Add backoff/sleep, use blocking queues/selectors, or condition waits.
- Hot regex or JSON parsing:
  - Symptom: Stacks show Pattern$Matcher or parser hot paths.
  - Fix: Precompile regex; reuse parsers; avoid unnecessary serialization.
- Excessive logging:
  - Symptom: Logging frameworks dominate stacks; I/O saturation.
  - Fix: Reduce log level; async appenders; batch writes.
- Lock contention/spinning:
  - Symptom: Many threads BLOCKED or parking around the same monitor; one thread RUNNABLE.
  - Fix: Reduce critical section; use concurrent data structures; finer-grained locks.
- GC thrash:
  - Symptom: GC threads hot; frequent young collections; high allocation rate.
  - Fix: Reduce temporary allocations; right-size heap; tune GC; investigate allocation hotspots via JFR.
- Native CPU (crypto/compression):
  - Symptom: jstack shows native or JNI frames; perf shows libc/libjvm/bouncycastle.
  - Fix: Use hardware-accelerated libs; batch operations; reduce compression level.

8) Minimal end-to-end command sequence
- Identify PID:
  - jcmd -l
- Find hot thread (Linux):
  - top -H -p <pid>       # get TID; convert to hex for nid
- Take dumps:
  - jstack -l <pid> > j1.txt; sleep 2; jstack -l <pid> > j2.txt; sleep 2; jstack -l <pid> > j3.txt
- Search for nid=0x<hex_tid> in j1/j2/j3 to see hot frames.
- Check GC:
  - jstat -gc <pid> 1000
- Run short JFR:
  - jcmd <pid> JFR.start name=cpu settings=profile duration=60s filename=/tmp/cpu.jfr
- Analyze and act on the top hot methods.




Notes
- Always capture evidence while the CPU is high; after the fact, stacks may look normal.
- On containers/Kubernetes, run these commands inside the container. Use jcmd <pid> inside the pod; ensure tools are present.
- Some commands (e.g., heap dump) may briefly impact the app; the above steps are generally safe and low overhead.


### jstack + grep 

```bash
#another example
jps -l # lookup process id, assume 437246
top -Hp 437246 # lookup high loading thread-id, assume 832643
printf "0x%x\n" 832643 # convert thread-id to hex, output 0xcb483
jstack 437246 | grep 0xcb483 -A 5 # search thread stack and print following 5 rows

```


# Another Java troubleshoot CPU high load example with sample code


Here’s a **complete, realistic example** showing how to troubleshoot **CPU high load** in a running **Java service**, step by step — including sample code that causes the issue and how to analyze it.

---

## 🧩 1. Example Java Code That Causes High CPU Usage

Let’s start with a simple example of a service that has a **CPU leak** (an infinite loop burning CPU).

```java
// HighCpuExample.java
public class HighCpuExample {

    public static void main(String[] args) {
        System.out.println("Starting CPU-hungry app...");
        new Thread(new BusyWorker(), "worker-1").start();
        new Thread(new BusyWorker(), "worker-2").start();

        // Simulate normal work
        while (true) {
            try {
                Thread.sleep(1000);
                System.out.println("Main thread alive");
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    static class BusyWorker implements Runnable {
        @Override
        public void run() {
            while (true) {
                // simulate CPU leak (forgot to sleep or block)
                double x = Math.random() * Math.random();
            }
        }
    }
}
```

Run it:

```bash
javac HighCpuExample.java
java HighCpuExample
```

You’ll notice your CPU fans start spinning — two threads are burning 100% CPU each.

---

## 🔍 2. Identify High CPU Process

Find the Java process:

```bash
ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head
```

You’ll see something like:

```
12345  1 java HighCpuExample  2.5 200.0
```

The PID (here `12345`) is the process consuming high CPU.

---

## 🧭 3. Identify the Hot Thread Inside the JVM

List threads and their CPU usage:

```bash
top -H -p 12345
```

Sample output:

```
PID   USER   PR  NI  VIRT  RES  SHR S %CPU %MEM  TIME+   COMMAND
12345 eric   20   0  300m  60m  15m R 100.0 2.5  0:30.01 java
12346 eric   20   0  300m  60m  15m R 100.0 2.5  0:30.02 java
```

Here `12346` is a Java thread ID in the OS (aka **native thread ID**).

Convert it to **hexadecimal**, since Java thread dumps use hex thread IDs:

```bash
printf "%x\n" 12346
```

→ e.g. `303a`

---

## 🧱 4. Get a Thread Dump

Use `jstack` to dump the stack of the Java process:

```bash
jstack 12345 > thread_dump.txt
```

Then search for your thread ID in hex:

```bash
grep -A30 "nid=0x303a" thread_dump.txt
```

You might see something like:

```
"worker-1" #12 prio=5 os_prio=0 tid=0x00007f9d5800b000 nid=0x303a runnable [0x00007f9d2c0fe000]
   java.lang.Thread.State: RUNNABLE
        at java.lang.Math.random(Native Method)
        at HighCpuExample$BusyWorker.run(HighCpuExample.java:23)
        at java.lang.Thread.run(Thread.java:748)
```

✅ You’ve found the **exact function causing high CPU** (`Math.random()` in an infinite loop).

---

## 🧠 5. Fix or Optimize

In this case, the issue is a **busy loop**:

```java
while (true) {
    double x = Math.random() * Math.random();
}
```

Fix it by adding a delay or blocking condition:

```java
while (true) {
    double x = Math.random() * Math.random();
    try {
        Thread.sleep(10);
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    }
}
```

---

## 🧰 6. Tools for CPU Profiling

| Tool                           | Description                    | Use                                                        |
| ------------------------------ | ------------------------------ | ---------------------------------------------------------- |
| `top`, `ps`, `htop`            | Check process-level CPU usage  | Linux built-in                                             |
| `top -H -p <pid>`              | See per-thread CPU             | Identify hot threads                                       |
| `jstack <pid>`                 | JVM thread dump                | See Java call stacks                                       |
| **VisualVM**                   | GUI profiler                   | Attach to process, see CPU hotspots                        |
| **async-profiler**             | Low-overhead sampling profiler | `./profiler.sh -d 30 -e cpu <pid>`                         |
| **JFR (Java Flight Recorder)** | Built-in from JDK 11+          | `jcmd <pid> JFR.start duration=30s filename=recording.jfr` |

---

## 🧾 7. Summary

| Step               | Command / Tool                | Purpose                       |
| ------------------ | ----------------------------- | ----------------------------- |
| Identify process   | `ps`, `top`                   | Find high CPU Java process    |
| Identify thread    | `top -H -p <pid>`             | Find hot thread ID            |
| Map thread to Java | Convert TID → hex             | Needed for `jstack`           |
| Get stack trace    | `jstack <pid>`                | Find which function burns CPU |
| Fix code           | Add sleep, block, or optimize | Resolve infinite computation  |

---

Would you like me to show a **version that leaks CPU only occasionally (intermittent spike)** — useful for simulating production-like issues?
