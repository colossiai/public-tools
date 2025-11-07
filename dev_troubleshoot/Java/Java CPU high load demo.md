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