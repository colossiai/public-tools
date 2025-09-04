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

# Build fat-jar with maven-assembly-plugin

`注意： maven-assembly-plugin 不能放在 pluginManagement`

```xml
  <properties>
    <maven.compiler.release>17</maven.compiler.release>
  </properties>

  <build>
    <pluginManagement>
      <plugins>
        <plugin>
          <groupId>org.apache.maven.plugins</groupId>
          <artifactId>maven-compiler-plugin</artifactId>
          <version>3.8.1</version>
        </plugin>
      </plugins>
    </pluginManagement>

    <plugins>

      <!-- maven-assembly-plugin can't be put in pluginManagement -->
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-assembly-plugin</artifactId>
        <version>3.1.1</version>

        <configuration>
          <descriptorRefs>
            <descriptorRef>jar-with-dependencies</descriptorRef>
          </descriptorRefs>
        </configuration>

        <executions>
          <execution>
            <id>make-assembly</id>
            <phase>package</phase>
            <goals>
              <goal>single</goal>
            </goals>
          </execution>
        </executions>

      </plugin>

    </plugins>
  </build>

</project>


```

**run fat-jar**

run `mvnd clean package` generate

target/demo-1.0-SNAPSHOT-jar-with-dependencies.jar

```bash
java -cp target/demo-1.0-SNAPSHOT-jar-with-dependencies.jar io.MyApp
```



**set main class in fat-jar**

```xml
        <configuration>
          <descriptorRefs>
            <descriptorRef>jar-with-dependencies</descriptorRef>
          </descriptorRefs>
          <archive>
            <manifest>
              <mainClass>com.grandwill.App</mainClass>
            </manifest>
          </archive>
        </configuration>

```

