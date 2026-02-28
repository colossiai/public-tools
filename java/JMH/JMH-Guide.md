# How to properly write JMH test


Writing a **proper JMH (Java Microbenchmark Harness) test** requires following a few rules because microbenchmarking in Java is tricky due to **JIT compilation, dead code elimination, and CPU optimizations**. Here's a comprehensive guide.

---

## 1. Add JMH dependency

If you use **Maven**:

```xml
<dependency>
    <groupId>org.openjdk.jmh</groupId>
    <artifactId>jmh-core</artifactId>
    <version>1.43</version>
</dependency>
<dependency>
    <groupId>org.openjdk.jmh</groupId>
    <artifactId>jmh-generator-annprocess</artifactId>
    <version>1.43</version>
    <scope>provided</scope>
</dependency>
```

For **Gradle**:

```gradle
dependencies {
    implementation 'org.openjdk.jmh:jmh-core:1.43'
    annotationProcessor 'org.openjdk.jmh:jmh-generator-annprocess:1.43'
}
```

---

## 2. Create a benchmark class

```java
import org.openjdk.jmh.annotations.*;
import java.util.concurrent.TimeUnit;
import java.util.ArrayList;
import java.util.List;

@BenchmarkMode(Mode.Throughput) // Measures operations per second
@OutputTimeUnit(TimeUnit.MILLISECONDS)
@State(Scope.Thread) // Each thread has its own state
public class MyBenchmark {

    private List<Integer> list;

    @Setup(Level.Iteration)
    public void setUp() {
        list = new ArrayList<>();
        for (int i = 0; i < 1000; i++) {
            list.add(i);
        }
    }

    @Benchmark
    public int sumList() {
        int sum = 0;
        for (int i : list) {
            sum += i;
        }
        return sum;
    }
}
```

---

### Key Annotations

| Annotation             | Description                                                                  |
| ---------------------- | ---------------------------------------------------------------------------- |
| `@Benchmark`           | Marks the method to benchmark                                                |
| `@BenchmarkMode`       | Mode of benchmarking: `Throughput`, `AverageTime`, `SampleTime`, `All`       |
| `@OutputTimeUnit`      | Unit of measurement                                                          |
| `@State`               | Holds state across benchmark invocations (`Thread`, `Benchmark`, or `Group`) |
| `@Setup` / `@TearDown` | Initialize or clean up resources. `Level.Iteration` or `Level.Trial`         |

---

## 3. Avoid common pitfalls

1. **Dead Code Elimination**
   Always **consume results**, otherwise JVM may optimize away your code.

```java
@Benchmark
public void sumListBlackhole(Blackhole bh) {
    int sum = 0;
    for (int i : list) sum += i;
    bh.consume(sum); // Prevents dead code elimination
}
```

2. **Warmup**
   JVM JIT optimizes code after a few iterations. Use warmup iterations:

```java
@Warmup(iterations = 5)
@Measurement(iterations = 10)
```

3. **Isolation**
   Avoid shared mutable state unless testing concurrency. Prefer `Scope.Thread` for state.

---

## 4. Running the benchmark

**Via Maven:**

```bash
mvn clean install
java -jar target/benchmarks.jar
```

**Via main method:**

```java
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.Options;
import org.openjdk.jmh.runner.options.OptionsBuilder;

public class BenchmarkRunner {
    public static void main(String[] args) throws Exception {
        Options opt = new OptionsBuilder()
                .include(MyBenchmark.class.getSimpleName())
                .forks(1)
                .build();

        new Runner(opt).run();
    }
}
```

---

## 5. Tips for Accurate Benchmarks

* **Fork your JVM** (`@Fork`) to isolate benchmark from other JVM effects.
* **Avoid using `System.nanoTime()` inside benchmark methods**; let JMH handle timing.
* **Minimize external side effects** like I/O, logging, or random numbers.
* **Use `Blackhole`** to consume results that would otherwise be optimized away.

---

If you want, I can write a **ready-to-run JMH benchmark template** that includes **warmup, measurement, forks, and Blackhole usage**, which you can just drop into any project. This is usually the best starting point.

Do you want me to do that?


# write a ready-to-run JMH benchmark template

Here’s a **ready-to-run JMH benchmark template** with all the best practices included: warmup, measurement, forks, Blackhole usage, and proper state handling. You can drop this into any Java project.

```java
import org.openjdk.jmh.annotations.*;
import org.openjdk.jmh.infra.Blackhole;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.Options;
import org.openjdk.jmh.runner.options.OptionsBuilder;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

// Benchmark configuration
@BenchmarkMode(Mode.Throughput)          // Options: Throughput, AverageTime, SampleTime, All
@OutputTimeUnit(TimeUnit.MILLISECONDS)  // Time unit for results
@Warmup(iterations = 5, time = 1)       // Warmup: 5 iterations, 1 second each
@Measurement(iterations = 10, time = 1) // Measurement: 10 iterations, 1 second each
@Fork(2)                                // Fork 2 separate JVMs to reduce JIT bias
@State(Scope.Thread)                     // Each thread has its own state
public class MyBenchmark {

    private List<Integer> list;

    // Setup before each iteration
    @Setup(Level.Iteration)
    public void setUp() {
        list = new ArrayList<>();
        for (int i = 0; i < 1000; i++) {
            list.add(i);
        }
    }

    // Example benchmark: sum all elements
    @Benchmark
    public void sumList(Blackhole bh) {
        int sum = 0;
        for (int i : list) {
            sum += i;
        }
        bh.consume(sum); // Prevents dead code elimination
    }

    // Another example: multiply elements
    @Benchmark
    public void multiplyList(Blackhole bh) {
        long product = 1;
        for (int i : list) {
            product *= (i + 1); // Avoid multiply by zero
        }
        bh.consume(product);
    }

    // Main method to run benchmark directly
    public static void main(String[] args) throws Exception {
        Options opt = new OptionsBuilder()
                .include(MyBenchmark.class.getSimpleName())
                .forks(2)
                .build();

        new Runner(opt).run();
    }
}
```

---

### ✅ Features included:

1. **Warmup & measurement** – ensures JIT optimizations settle before measuring.
2. **Forking** – isolates benchmark in a fresh JVM.
3. **Blackhole** – prevents dead code elimination.
4. **State management** – `Scope.Thread` ensures thread-safe independent data.
5. **Multiple benchmark methods** – easy to add more tests.

---

If you want, I can also make a **concurrent version** that tests multiple threads safely, which is great for testing data structures or algorithms under load. It uses `@Threads` and `Scope.Group` properly.

Do you want me to create that too?


# for the above function sumList(), how JMH call sumList() internally? using a loop or some other logic?

Ah, this is a subtle but **very important question** for understanding how JMH works. JMH does **not just call your `@Benchmark` method once per iteration**—it uses a sophisticated harness to properly measure performance while avoiding JVM optimizations like **dead code elimination, inlining, and loop unrolling**. Here’s the breakdown.

---

## 1. How JMH actually invokes `sumList()`

When you write:

```java
@Benchmark
public void sumList(Blackhole bh) { ... }
```

JMH generates **bytecode at build time** (through annotation processing) that looks roughly like this internally:

```java
for (long i = 0; i < targetNumberOfOps; i++) {
    // call your benchmark method
    sumList(blackhole);
}
```

But with **extra machinery**:

1. **Looping is dynamic**:

   * JMH does **not hard-code a fixed loop count**. It uses **adaptive sampling** to decide how many times to call your method in one “measurement batch” so that the timer resolution is meaningful (you don’t measure a single method call that’s too fast to time accurately).

2. **Blackhole injection**:

   * JMH automatically passes a `Blackhole` instance (if your benchmark accepts it) to ensure the return value is consumed. Otherwise, the JVM might optimize away the method body entirely.

3. **Warmup vs. measurement**:

   * During **warmup**, JMH repeatedly calls your benchmark method to let the **JIT compiler optimize** the code.
   * During **measurement**, it calls the method many times per measurement batch and records the time.

4. **Forking**:

   * Each fork is a separate JVM. JMH repeats the loop inside each fork to **isolate the measurement from JIT optimizations or other JVM state**.

---

## 2. Simplified illustration

Imagine you benchmark `sumList()` with **throughput mode**:

```text
Warmup iteration 1: call sumList() 1000 times
Warmup iteration 2: call sumList() 2000 times
...
Measurement iteration 1: call sumList() 10000 times, measure time
Measurement iteration 2: call sumList() 12000 times, measure time
```

JMH handles all of this **under the hood**—you never see the loop, but the generated harness is effectively looping and timing your method.

---

## 3. Key points

* **Your method may be called millions of times** in a single measurement iteration.
* JMH **randomizes and pads calls** to prevent JIT from making misleading optimizations (e.g., loop unrolling).
* You don’t need to write a `for` loop in your benchmark method unless you want to measure **internal loops specifically**.
* JMH ensures **each benchmark call is as isolated as possible** for precise timing.

---

If you want, I can **show the actual JMH-generated harness pseudo-code for `sumList()`**, so you can see exactly how it calls your method internally and manages loops, warmup, and blackholes.

Do you want me to do that?

