# Introduce java diagnostic tools like jstack, jmap

Here’s a concise introduction to core Java diagnostic tools you’ll find in the JDK for troubleshooting and performance analysis. These tools are typically used against local JVM processes and require appropriate permissions. Most are in the JDK’s bin directory.

Key tools
- jps (Java Virtual Machine Process Status)
  - What it does: Lists running Java processes and their PIDs.
  - When to use: First step to identify the target JVM for other tools.
  - Example: jps -l -v

- jstack (Thread dump)
  - What it does: Captures thread stacks of a JVM. Shows thread states, locks, deadlocks, and where time might be spent.
  - When to use: Investigate deadlocks, stuck threads, high CPU (look for threads in RUNNABLE with hot frames), application hangs.
  - Examples:
    - jstack <pid>
    - jstack -l <pid>        # includes lock info
    - jstack -m <pid>        # includes native frames (useful with JNI)
  - Tip: Take multiple dumps a few seconds apart to see if stacks change.

- jmap (Heap maps, heap dumps)
  - What it does: Inspects heap usage and produces heap dumps.
  - When to use: Memory leaks, OutOfMemoryError investigation, object histogram by class.
  - Examples:
    - jmap -heap <pid>       # heap configuration and summary
    - jmap -histo <pid>      # object histogram (count, size by class)
    - jmap -dump:format=b,file=heap.hprof <pid>  # full heap dump
  - Tip: Analyze dumps with tools like Eclipse MAT, VisualVM, YourKit, or jdk.jcmd.gc.class_histogram.

- jcmd (Unified diagnostic command interface)
  - What it does: Sends diagnostic commands to a running JVM; encompasses many jmap/jstack/jinfo features and more.
  - When to use: Preferred modern interface for HotSpot; supports GC, JFR, thread, heap, and VM flags operations.
  - Examples:
    - jcmd <pid> help
    - jcmd <pid> Thread.print
    - jcmd <pid> GC.heap_info
    - jcmd <pid> GC.class_histogram
    - jcmd <pid> GC.heap_dump filename=heap.hprof
    - jcmd <pid> VM.flags
    - jcmd <pid> JFR.start name=diag settings=profile filename=recording.jfr duration=300s

- jstat (JVM statistics)
  - What it does: Samples and reports GC and class-loading statistics.
  - When to use: Monitor GC behavior and memory pool trends over time.
  - Examples:
    - jstat -gc <pid> 1000    # GC metrics every second
    - jstat -gccapacity <pid> 2000
    - jstat -class <pid>

- jinfo (JVM configuration)
  - What it does: Displays and, in some cases, sets VM flags on a running JVM.
  - When to use: Inspect system properties and JVM flags; toggle some diagnostic flags.
  - Examples:
    - jinfo -flags <pid>
    - jinfo -sysprops <pid>
    - jinfo -flag +PrintGC <pid>   # if supported

- jfr (Java Flight Recorder; via jcmd JFR.* or jfr tool)
  - What it does: Low-overhead continuous profiling and event recording.
  - When to use: Performance profiling in production, intermittent issues.
  - Examples:
    - jcmd <pid> JFR.start settings=profile name=prod duration=5m filename=rec.jfr
    - jfr print --events jdk.CPULoad rec.jfr   # JDK 14+ standalone jfr tool

Typical workflows
- High CPU
  1) Find PID: jps -l
  2) Map OS thread using top/ps to Java thread ID (nid) from jstack -l <pid>.
  3) Take multiple jstack dumps; identify hot methods. Optionally start a short JFR.

- Memory leak / OOME
  1) jcmd <pid> GC.class_histogram or jmap -histo <pid>
  2) Trigger heap dump: jcmd <pid> GC.heap_dump filename=heap.hprof
  3) Analyze with Eclipse MAT; look for dominator tree and leak suspects.

- Application hang / deadlock
  1) jstack -l <pid> or jcmd <pid> Thread.print
  2) Look for BLOCKED threads and deadlock section.
  3) Check monitor/lock owners and waiting threads.

Notes and best practices
- Prefer jcmd when available; jmap/jstack are older interfaces.
- Some operations are intrusive or can pause the JVM (heap dump, histo on large heaps). Use during maintenance windows or with caution.
- On containers/Kubernetes: ensure tools exist in the image; you may need to jcmd inside the container or use jattach. Map host PIDs if needed.
- Security/permissions: same user as the target JVM, or root. On some OSes, ptrace or process attach restrictions apply.
- For Windows, run an elevated shell if needed.
- For remote analysis, enable JMX or use JFR for low-overhead recording and pull the file later.


