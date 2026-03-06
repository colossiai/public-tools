# Likely Causes When META-INF/BenchmarkList is Missing


```

If META-INF/BenchmarkList is not found after packaging, here are the most common causes:

1. JMH Annotation Processor Not Running ⚠️ (Most Common)

The annotation processor must run during compilation to generate the BenchmarkList.

Check if configured:
<plugin>
    <artifactId>maven-compiler-plugin</artifactId>
    <configuration>
        <annotationProcessorPaths>
            <path>
                <groupId>org.openjdk.jmh</groupId>
                <artifactId>jmh-generator-annprocess</artifactId>
                <version>${jmh.version}</version>
            </path>
        </annotationProcessorPaths>
    </configuration>
</plugin>

Without this, the @Benchmark annotations are ignored!

2. Missing JMH Dependencies

Both runtime and annotation processor dependencies must be present:

<dependencies>
    <!-- JMH Core (runtime) -->
    <dependency>
        <groupId>org.openjdk.jmh</groupId>
        <artifactId>jmh-core</artifactId>
        <version>${jmh.version}</version>
    </dependency>

    <!-- JMH Annotation Processor (compile-time) -->
    <dependency>
        <groupId>org.openjdk.jmh</groupId>
        <artifactId>jmh-generator-annprocess</artifactId>
        <version>${jmh.version}</version>
    </dependency>
</dependencies>

3. No @Benchmark Methods Found

If your class has no @Benchmark methods, nothing gets generated.

Check:
- Methods are public
- Methods have @Benchmark annotation
- Class is public and not abstract
- Package is not excluded by compiler

4. Incremental Compilation Issues

Maven may skip annotation processing if it thinks nothing changed.

Fix:
mvn clean compile  # Force full rebuild

5. Shade Plugin Not Including META-INF

The shade plugin might exclude META-INF files.

Check your shade configuration doesn't have:
<filters>
    <filter>
        <artifact>*:*</artifact>
        <excludes>
            <exclude>META-INF/**</exclude>  <!-- DON'T DO THIS! -->
        </excludes>
    </filter>
</filters>

6. Wrong Java Version

JMH requires Java 8+. Check:
<properties>
    <maven.compiler.source>17</maven.compiler.source>
    <maven.compiler.target>17</maven.compiler.target>
</properties>

7. IDE Annotation Processing Disabled

If using IntelliJ/Eclipse, annotation processing might be disabled.

IntelliJ: Settings → Build → Compiler → Annotation Processors → ✅ Enable annotation processing

Diagnostic Steps

Step 1: Check if generated sources exist

ls -la target/generated-sources/annotations/
Should contain JMH-generated test classes.

Step 2: Check if BenchmarkList exists in classes

find target/classes -name "BenchmarkList"
Should return: target/classes/META-INF/BenchmarkList

Step 3: Check compilation logs

mvn clean compile -X | grep -i "annotation\|jmh"
Should show annotation processor running.

Step 4: Verify JAR contents

jar tf target/benchmarks.jar | grep BenchmarkList
Should return: META-INF/BenchmarkList

Quick Fix Checklist

1. ✅ Add jmh-generator-annprocess to <annotationProcessorPaths>
2. ✅ Add both JMH dependencies (jmh-core + jmh-generator-annprocess)
3. ✅ Ensure @Benchmark methods are public
4. ✅ Run mvn clean compile (not just mvn compile)
5. ✅ Check target/classes/META-INF/BenchmarkList exists before packaging
6. ✅ Verify shade plugin includes META-INF resources

Example Error When Missing

If you run the JAR without BenchmarkList:
$ java -jar benchmarks.jar
ERROR: Unable to find the resource: /META-INF/BenchmarkList

Root cause: Annotation processor never ran, so no benchmarks were discovered.

Solution: Follow checklist above, most likely need to add <annotationProcessorPaths> configuration.

```