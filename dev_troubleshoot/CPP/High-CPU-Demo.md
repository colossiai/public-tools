# C++ demo program with high CPU spin

here are **minimal C++ demo programs** you can compile and run to **practice diagnosing CPU spin** problem using Linux tools like `top`, `gdb`, `perf`

---

# 🧩 1. High CPU Demo — *Busy Loop Bug*

### 🧱 `cpu_spin.cpp`

```cpp
#include <iostream>
#include <thread>
#include <chrono>
#include <atomic>

std::atomic<bool> running{true};

// Simulates a bug: spinning loop instead of proper sleep
void busy_worker() {
    while (running.load()) {
        // Wrong: missing std::this_thread::sleep_for or condition variable wait
        int x = 0;
        for (int i = 0; i < 1000; ++i)
            x += i;
        // no sleep here -> 100% CPU
    }
}

int main() {
    std::cout << "Starting busy worker..." << std::endl;
    std::thread t(busy_worker);

    std::this_thread::sleep_for(std::chrono::seconds(20)); // let it spin
    running = false;
    t.join();
    std::cout << "Stopped." << std::endl;
}
```

### ⚙️ Compile & Run

```bash
g++ -O2 -std=c++17 cpu_spin.cpp -o cpu_spin -pthread
./cpu_spin
```

### 🧪 Try diagnosing:

1. Run `top` — notice 100% CPU.
2. Run `top -H -p <pid>` — see one thread fully loaded.
3. Attach:

   ```bash
   sudo gdb -p <pid>

   #  instructs GDB to take a snapshot of the call stack for every thread 
   (gdb) thread apply all bt
   ```


    ```bash
    Thread 2 (Thread 0x75d3289ff6c0 (LWP 2711) "cpu_spin"):
    #0  0x00005a4e16b254a8 in busy_worker() ()                  <--------------------------
    #1  0x000075d328eecdb4 in ?? () from /lib/x86_64-linux-gnu/libstdc++.so.6
    #2  0x000075d328a9caa4 in start_thread (arg=<optimized out>) at ./nptl/pthread_create.c:447
    #3  0x000075d328b29c6c in clone3 () at ../sysdeps/unix/sysv/linux/x86_64/clone3.S:78

    Thread 1 (Thread 0x75d32907e740 (LWP 2710) "cpu_spin"):
    #0  0x000075d328aecadf in __GI___clock_nanosleep (clock_id=clock_id@entry=0, flags=flags@entry=0, req=0x7fffcb6905f0, rem=0x7fffcb6905f0) at ../sysdeps/unix/sysv/linux/clock_nanosleep.c:78
    #1  0x000075d328af9a27 in __GI___nanosleep (req=<optimized out>, rem=<optimized out>) at ../sysdeps/unix/sysv/linux/nanosleep.c:25
    #2  0x00005a4e16b2532b in main ()
    ```

   → You’ll see it looping inside `busy_worker()`.
4. (Optional) Profile:

   ```bash
   sudo perf record -p 4706 -g -- sleep 5
   sudo perf report
   ```


    ### 🛠️ Command Breakdown

    The table below explains each part of the command:

    | Command Component | Explanation |
    | :--- | :--- |
    | `sudo` | Runs the command with root privileges, necessary for profiling system-wide performance and kernel functions. |
    | `perf record` | The main command to sample and record performance data into a file (default: `perf.data`). |
    | `-p 4706` | Attaches the profiler to the existing process with the Process ID (PID) **4706**. |
    | `-g` | Short for `--call-graph`. This enables call stack recording, allowing you to see the full chain of function calls leading to a sample. |
    | `--` | Separates `perf` options from the command to be executed. This is good practice but optional in this case. |
    | `sleep 10` | A simple command that runs for 10 seconds, determining the data collection duration. |

    ### Generate the Report: 
    Following command to open an interactive analysis interface:

    ```bash
    sudo perf report
    ```


    Look for top functions:

    ![alt text](images/perf-report-cpu_spin.png)


   → The function `busy_worker()` will dominate CPU samples.

✅ *Fix:* Add `std::this_thread::sleep_for(10ms)` or use condition variables.
