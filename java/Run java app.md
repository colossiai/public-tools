To run a Java class file from the `./target/classes/org/example` directory, you have several options depending on your setup:

## Method 1: Using java command with classpath

```bash
# From the project root directory
java -cp ./target/classes org.example.YourClassName
```

## Method 2: Navigate to the classes directory

```bash
# Navigate to the classes directory
cd ./target/classes

# Then run from there
java org.example.YourClassName
```

## Method 3: If you have a main class with package declaration

Make sure your class has the correct package declaration and main method:

```java
package org.example;

public class YourClassName {
    public static void main(String[] args) {
        System.out.println("Hello World!");
    }
}
```

## Method 4: Using Maven (if you built with Maven)

```bash
mvn exec:java -Dexec.mainClass="org.example.YourClassName"
```

## Method 5: If you have dependencies

If your class has external dependencies, you'll need to include them in the classpath:

```bash
java -cp "./target/classes:./target/dependency/*" org.example.YourClassName
```

### Example:
Assuming you have a class called `Main` in the `org.example` package:

```bash
# From project root
java -cp ./target/classes org.example.Main
```

Replace `YourClassName` with the actual name of your class file (without the `.class` extension). Make sure the class has a `public static void main(String[] args)` method to be executable.


# Run java app with maven

**set mainClass**

```xml
<properties>
    <exec.mainClass>com.cruiser.App</exec.mainClass>
</properties>

```

**Run with `exec:java`**
```bash
mvn clean compile exec:java -Dexec.args="arg1 arg2"
```

--------------------------------------

# Build fat-jar with `maven-shade-plugin`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.trading</groupId>
    <artifactId>rocketmq-messaging</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <name>RocketMQ Low-Latency Messaging Demo</name>
    <description>Demo of RocketMQ for low-latency trading system market data messaging</description>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <rocketmq.version>5.2.0</rocketmq.version>
        <slf4j.version>2.0.9</slf4j.version>
        <logback.version>1.4.14</logback.version>
        <jmh.version>1.37</jmh.version>
    </properties>

    <dependencies>
        <!-- RocketMQ Client -->
        <dependency>
            <groupId>org.apache.rocketmq</groupId>
            <artifactId>rocketmq-client-java</artifactId>
            <version>${rocketmq.version}</version>
        </dependency>

        <!-- Logging -->
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-api</artifactId>
            <version>${slf4j.version}</version>
        </dependency>
        <dependency>
            <groupId>ch.qos.logback</groupId>
            <artifactId>logback-classic</artifactId>
            <version>${logback.version}</version>
        </dependency>

        <!-- JMH for benchmarking -->
        <dependency>
            <groupId>org.openjdk.jmh</groupId>
            <artifactId>jmh-core</artifactId>
            <version>${jmh.version}</version>
        </dependency>
        <dependency>
            <groupId>org.openjdk.jmh</groupId>
            <artifactId>jmh-generator-annprocess</artifactId>
            <version>${jmh.version}</version>
            <scope>provided</scope>
        </dependency>

        <!-- HdrHistogram for latency measurement -->
        <dependency>
            <groupId>org.hdrhistogram</groupId>
            <artifactId>HdrHistogram</artifactId>
            <version>2.1.12</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>17</source>
                    <target>17</target>
                </configuration>
            </plugin>

            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-shade-plugin</artifactId>
                <version>3.5.0</version>
                <executions>
                    <!-- Producer Uber JAR -->
                    <execution>
                        <id>producer</id>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                        <configuration>
                            <finalName>rocketmq-producer</finalName>
                            <transformers>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                    <mainClass>com.trading.producer.MarketDataProducer</mainClass>
                                </transformer>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ServicesResourceTransformer"/>
                            </transformers>
                            <filters>
                                <filter>
                                    <artifact>*:*</artifact>
                                    <excludes>
                                        <exclude>META-INF/*.SF</exclude>
                                        <exclude>META-INF/*.DSA</exclude>
                                        <exclude>META-INF/*.RSA</exclude>
                                    </excludes>
                                </filter>
                            </filters>
                        </configuration>
                    </execution>

                    <!-- Consumer Uber JAR -->
                    <execution>
                        <id>consumer</id>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                        <configuration>
                            <finalName>rocketmq-consumer</finalName>
                            <transformers>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                    <mainClass>com.trading.consumer.MarketDataConsumer</mainClass>
                                </transformer>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ServicesResourceTransformer"/>
                            </transformers>
                            <filters>
                                <filter>
                                    <artifact>*:*</artifact>
                                    <excludes>
                                        <exclude>META-INF/*.SF</exclude>
                                        <exclude>META-INF/*.DSA</exclude>
                                        <exclude>META-INF/*.RSA</exclude>
                                    </excludes>
                                </filter>
                            </filters>
                        </configuration>
                    </execution>

                    <!-- Benchmark Uber JAR -->
                    <execution>
                        <id>benchmark</id>
                        <phase>package</phase>
                        <goals>
                            <goal>shade</goal>
                        </goals>
                        <configuration>
                            <finalName>rocketmq-benchmark</finalName>
                            <transformers>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                                    <mainClass>org.openjdk.jmh.Main</mainClass>
                                </transformer>
                                <transformer implementation="org.apache.maven.plugins.shade.resource.ServicesResourceTransformer"/>
                            </transformers>
                            <filters>
                                <filter>
                                    <artifact>*:*</artifact>
                                    <excludes>
                                        <exclude>META-INF/*.SF</exclude>
                                        <exclude>META-INF/*.DSA</exclude>
                                        <exclude>META-INF/*.RSA</exclude>
                                    </excludes>
                                </filter>
                            </filters>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```


**Key features added**:

  - ServicesResourceTransformer - Properly merges META-INF/services files from dependencies (important for RocketMQ)
  - Signature file exclusions - Prevents issues with signed JARs
  - Separate execution IDs for each jar

**Usage**:

## Build all uber jars
```mvn clean package```

## Run producer
```java -jar target/rocketmq-producer.jar```

## Run consumer
```java -jar target/rocketmq-consumer.jar```

## Run benchmarks
```java -jar target/rocketmq-benchmark.jar```

The uber jars will be self-contained and include all RocketMQ client dependencies, making them easy to deploy and run.

