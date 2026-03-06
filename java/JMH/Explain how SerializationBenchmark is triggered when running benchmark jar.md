# Explain how SerializationBenchmark is triggered when running benchmark.jar


```
⏺ How SerializationBenchmark is Triggered

Here's the complete flow from building to running the benchmark:

1. Build-Time: Annotation Processing (pom.xml:77-84)

<annotationProcessorPaths>
    <path>
        <groupId>org.openjdk.jmh</groupId>
        <artifactId>jmh-generator-annprocess</artifactId>
        <version>${jmh.version}</version>
    </path>
</annotationProcessorPaths>

During mvn compile, JMH's annotation processor scans for:
- @Benchmark annotated methods (lines 117, 122, 129, 134, 141, 171, 197)
- @State, @BenchmarkMode, @Warmup, etc. configurations

It generates:
- Metadata files in META-INF/BenchmarkList
- Generated benchmark harness code in target/generated-sources/annotations/

2. Package: Creating Fat JAR (pom.xml:165-201)

<plugin>
    <artifactId>maven-shade-plugin</artifactId>
    <configuration>
        <finalName>benchmarks</finalName>
        <transformers>
            <transformer>
                <mainClass>org.openjdk.jmh.Main</mainClass>  ← KEY!
            </transformer>
        </transformers>
    </configuration>
</plugin>

The shade plugin creates benchmarks.jar with:
- Main-Class: org.openjdk.jmh.Main in META-INF/MANIFEST.MF
- All dependencies bundled (JMH, SBE, Protobuf, Jackson)
- META-INF/BenchmarkList containing discovered benchmarks

3. Runtime: Executing the JAR

java -jar benchmarks.jar

This triggers the following sequence:

Step 3.1: JVM starts JMH Main

JVM reads MANIFEST.MF → Finds Main-Class: org.openjdk.jmh.Main → Executes main()

Step 3.2: JMH discovers benchmarks

// JMH internals (simplified)
org.openjdk.jmh.Main.main()
→ BenchmarkList.find()  // Reads META-INF/BenchmarkList
→ Discovers: com.benchmark.SerializationBenchmark

Step 3.3: JMH processes annotations

// From SerializationBenchmark.java
@State(Scope.Benchmark)           → Creates ONE instance for all iterations
@BenchmarkMode(Mode.Throughput)   → Measures ops/time
@OutputTimeUnit(TimeUnit.MICROSECONDS) → Reports in ops/μs
@Warmup(iterations = 5, time = 1)  → 5 warmup rounds
@Measurement(iterations = 10)      → 10 measured rounds
@Fork(value = 2)                   → Run in 2 separate JVM processes

Step 3.4: JMH executes benchmark lifecycle

For each @Fork:
1. Spawn new JVM with -Xms2G -Xmx2G
2. @Setup methods execute (setup() at line 41-81)
    → Initializes JSON/Protobuf/SBE test data
3. Warmup phase (5 iterations):
    → Run @Benchmark methods (no results saved)
    → Let JIT compiler optimize hot code
4. Measurement phase (10 iterations):
    → Run each @Benchmark method:
        - serializeJson()
        - deserializeJson()
        - serializeProtobuf()
        - deserializeProtobuf()
        - serializeSbe()
        - deserializeSbe()
        - compareSerializedSizes()
    → Collect throughput data (ops/μs)
5. @TearDown methods (if any)

Step 3.5: JMH aggregates results

Combine results from 2 forks × 10 iterations = 20 samples
Calculate: Mean, Error (±), Units
Output formatted table

Visual Flow Diagram

┌────────────────────────────────────────────────────────────┐
│  mvn clean package                                          │
└────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌─────────────────────┐
    │ Annotation Processor │ Scans @Benchmark methods
    └─────────────────────┘
            │
            ▼
    ┌─────────────────────┐
    │ Generates Metadata   │ → META-INF/BenchmarkList
    └─────────────────────┘
            │
            ▼
    ┌─────────────────────┐
    │  Maven Shade Plugin  │ Creates benchmarks.jar
    └─────────────────────┘
            │
            ▼
    ┌─────────────────────────────────────────┐
    │  MANIFEST.MF                             │
    │  Main-Class: org.openjdk.jmh.Main       │
    └─────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  java -jar benchmarks.jar                                   │
└────────────────────────────────────────────────────────────┘
            │
            ▼
    ┌─────────────────────┐
    │  JVM loads Main      │ org.openjdk.jmh.Main
    └─────────────────────┘
            │
            ▼
    ┌─────────────────────┐
    │  JMH discovers       │ Reads META-INF/BenchmarkList
    │  benchmarks          │ Finds SerializationBenchmark
    └─────────────────────┘
            │
            ▼
    ┌─────────────────────┐
    │  Fork 2 JVMs         │ -Xms2G -Xmx2G
    └─────────────────────┘
            │
    ┌───────┴───────┐
    ▼               ▼
    Fork 1          Fork 2
    │               │
    ▼               ▼
@Setup()        @Setup()
    │               │
    ▼               ▼
Warmup          Warmup
(5 iter)        (5 iter)
    │               │
    ▼               ▼
Measure         Measure
(10 iter)       (10 iter)
    │               │
    └───────┬───────┘
            ▼
    ┌─────────────────────┐
    │  Aggregate Results   │ 20 total samples
    │  Print Report        │ Mean ± Error
    └─────────────────────┘

Key Configuration Points

┌──────────────────────┬──────────────────────────────────┬──────────────────────────────────────┐
│    Configuration     │             Location             │               Purpose                │
├──────────────────────┼──────────────────────────────────┼──────────────────────────────────────┤
│ @Benchmark           │ SerializationBenchmark.java:116+ │ Marks methods to benchmark           │
├──────────────────────┼──────────────────────────────────┼──────────────────────────────────────┤
│ Annotation Processor │ pom.xml:77-84                    │ Discovers benchmarks at compile time │
├──────────────────────┼──────────────────────────────────┼──────────────────────────────────────┤
│ Main-Class           │ pom.xml:179                      │ Entry point: org.openjdk.jmh.Main    │
├──────────────────────┼──────────────────────────────────┼──────────────────────────────────────┤
│ Fat JAR              │ pom.xml:165-201                  │ Bundles all dependencies             │
├──────────────────────┼──────────────────────────────────┼──────────────────────────────────────┤
│ Fork JVMs            │ SerializationBenchmark.java:20   │ Isolated execution                   │
└──────────────────────┴──────────────────────────────────┴──────────────────────────────────────┘

Run with Options

# Run all benchmarks
java -jar benchmarks.jar

# Run specific benchmark
java -jar benchmarks.jar SerializationBenchmark.serializeSbe

# Run with regex
java -jar benchmarks.jar ".*Sbe.*"

# List available benchmarks
java -jar benchmarks.jar -l

# Help
java -jar benchmarks.jar -h

The magic is: JMH Main → Discovers benchmarks → Forks JVMs → Runs methods → Reports results ⚡

```