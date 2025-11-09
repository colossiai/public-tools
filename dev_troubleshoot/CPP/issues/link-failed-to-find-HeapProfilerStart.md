
# undefined reference to `HeapProfilerStart'

```
g++ leak_live.cpp -o leak_live -pthread -lprofiler       
/usr/bin/ld: /tmp/ccFTwglJ.o: in function `main':
leak_live.cpp:(.text+0xcf): undefined reference to `HeapProfilerStart'
collect2: error: ld returned 1 exit status

I have installed: sudo apt install libgoogle-perftools-dev

and #include <gperftools/heap-profiler.h> in my code

my system is 6.6.87.2-microsoft-standard-WSL2
```





It’s a link-time issue: the symbol HeapProfilerStart isn’t being found in the library you’re linking. Common causes and fixes:

1) Link the correct library and order
- HeapProfiler* lives in libprofiler, so -lprofiler is right, but GCC is sensitive to library order: libraries should come after the objects that use them.
- Put -lprofiler at the end of the command line, after your source/object files and -pthread.

Example:
g++ leak_live.cpp -pthread -o leak_live -lprofiler

2) Ensure the right libprofiler is installed and visible
- You have libgoogle-perftools-dev, which should provide /usr/lib/x86_64-linux-gnu/libprofiler.so and headers in /usr/include/gperftools.
- Verify:
  - ls -l /usr/lib/x86_64-linux-gnu/libprofiler.so
  - nm -D /usr/lib/x86_64-linux-gnu/libprofiler.so | grep HeapProfilerStart
    - You should see a T HeapProfilerStart (or similar). If not, you might be pulling a stub or incompatible version.

3) Make sure you’re not mixing tcmalloc-only packages
- Some builds of gperftools may be split; ensure libgoogle-perftools4 (runtime) is installed too:
  - sudo apt-get install libgoogle-perftools4
- On Debian/Ubuntu, dev pulls in the runtime, but double-check.

4) WSL-specific quirks
- WSL2 generally works fine. But if you have multiple toolchains or custom /usr/local/lib versions, ensure no conflicting libprofiler is ahead in LD_LIBRARY_PATH.
- Try a clean link with explicit path:
  - g++ leak_live.cpp -pthread -o leak_live /usr/lib/x86_64-linux-gnu/libprofiler.so

5) C vs C++ name mangling
- HeapProfilerStart is a C function, but the header already handles extern "C". Make sure you included the correct header:
  - #include <gperftools/heap-profiler.h>
- Do not declare it yourself.

6) Minimal test to isolate
Create test.cpp:
#include <gperftools/heap-profiler.h>
int main() {
  HeapProfilerStart("hp.out");
  HeapProfilerStop();
  return 0;
}

Compile:
g++ test.cpp -pthread -o test -lprofiler
If this fails, it’s a system setup/linking issue. If it succeeds, the problem may be link order or another library flag in your original command.

7) Runtime usage tips
- Run with HEAPPROFILE or HEAPPROFILE=<file-prefix> if you don’t call HeapProfilerStart yourself. Since you do, ensure the process has write perms to the current directory.
- You may want to link tcmalloc to get richer allocation symbols:
  - g++ leak_live.cpp -pthread -o leak_live -lprofiler -ltcmalloc
  - or pre-load at runtime: LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libtcmalloc.so.4 ./leak_live

8) If still unresolved, collect diagnostics
- Show compiler/linker command with -Wl,--verbose
- Show which lib is picked: g++ ... -Wl,-t 2>&1 | grep profiler
- Check pkg-config (sometimes available): pkg-config --libs --cflags libprofiler
- Confirm architecture matches: file /usr/lib/x86_64-linux-gnu/libprofiler.so and file your .o files (both should be x86-64)

Most likely quick fix: move -lprofiler to the end:
g++ leak_live.cpp -pthread -o leak_live -lprofiler


## Eventual solution:

```

g++ leak_live.cpp -pthread -o leak_live -lprofiler -ltcmalloc

# or

g++ -g leak_live.cpp -o leak_live -ltcmalloc_and_profiler 

```

![alt text](HeapProfilerStart%20symbol.png)