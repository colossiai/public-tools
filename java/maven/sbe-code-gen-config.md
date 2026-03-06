# Explain the maven config

```xml
              <!-- SBE Code Generator -->
              <plugin>
                  <groupId>org.codehaus.mojo</groupId>
                  <artifactId>exec-maven-plugin</artifactId>
                  <version>3.1.0</version>
                  <executions>
                      <execution>
                          <id>generate-sbe</id>
                          <phase>generate-sources</phase>
                          <goals>
                              <goal>java</goal>
                          </goals>
                          <configuration>
                              <includeProjectDependencies>true</includeProjectDependencies>
                              <includePluginDependencies>true</includePluginDependencies>
                              <mainClass>uk.co.real_logic.sbe.SbeTool</mainClass>
                              <arguments>
                                  <argument>${project.basedir}/src/main/resources/schema/market-data.xml</argument>
                              </arguments>
                              <systemProperties>
                                  <systemProperty>
                                      <key>sbe.output.dir</key>
                                      <value>${project.build.directory}/generated-sources/sbe</value>
                                  </systemProperty>
                              </systemProperties>
                          </configuration>
                      </execution>
                  </executions>
                  <dependencies>
                      <dependency>
                          <groupId>uk.co.real-logic</groupId>
                          <artifactId>sbe-all</artifactId>
                          <version>${sbe.version}</version>
                      </dependency>
                  </dependencies>
              </plugin>

```


⏺ SBE Maven Plugin Configuration Explained

  This Maven plugin configuration automates SBE code generation from XML schema files during the build process.

  Plugin Breakdown

  1. Plugin Identity

```
  <groupId>org.codehaus.mojo</groupId>
  <artifactId>exec-maven-plugin</artifactId>
  <version>3.1.0</version>
```

  - Uses exec-maven-plugin to execute Java classes during the build
  - Not SBE-specific - it's a generic executor plugin

  2. Execution Phase

```
  <phase>generate-sources</phase>
```
  
  - Runs during Maven's generate-sources phase
  - Happens before compilation, so generated code is available to compile
  - Typical Maven lifecycle order: generate-sources → compile → test → package

  3. Code Generator

```
  <mainClass>uk.co.real_logic.sbe.SbeTool</mainClass>
```

  - Executes SBE's code generator: SbeTool
  - This class reads the XML schema and generates Java encoder/decoder classes

  4. Input Schema

```
  <argument>${project.basedir}/src/main/resources/schema/market-data.xml</argument>
```

  - Points to your SBE XML schema file
  - ${project.basedir} = your project root directory
  - This schema defines your message structures (e.g., MarketData, Order, Trade)

  5. Output Directory
```
  <systemProperty>
      <key>sbe.output.dir</key>
      <value>${project.build.directory}/generated-sources/sbe</value>
  </systemProperty>
```

  - Generated Java classes go to: target/generated-sources/sbe
  - ${project.build.directory} = target/ folder
  - These files are auto-generated and shouldn't be committed to Git

  6. Dependencies

```
  <includeProjectDependencies>true</includeProjectDependencies>
  <includePluginDependencies>true</includePluginDependencies>
  <dependencies>
      <dependency>
          <groupId>uk.co.real-logic</groupId>
          <artifactId>sbe-all</artifactId>
          <version>${sbe.version}</version>
      </dependency>
  </dependencies>
```

  - Makes sbe-all library available to the generator
  - Contains SbeTool class and all SBE code generation logic

  Build Workflow

```
  1. mvn clean compile
     ↓
  2. generate-sources phase triggers
     ↓
  3. exec-maven-plugin runs SbeTool
     ↓
  4. Reads: src/main/resources/schema/market-data.xml
     ↓
  5. Generates Java classes → target/generated-sources/sbe/
     ↓
  6. Maven compiles both:
     - Your source code (src/main/java)
     - Generated SBE code (target/generated-sources/sbe)

```

  Key Benefits

  ✅ Automated: No manual code generation steps  
  ✅ Type-safe: Schema changes = compile errors.  
  ✅ Clean builds: mvn clean removes generated code.  
  ✅ IDE-friendly: IntelliJ/Eclipse recognize generated sources automatically.  

  Common Commands

  # Generate SBE code only
  mvn generate-sources

  # Clean and regenerate
  mvn clean generate-sources

  # Full build with regeneration
  mvn clean compile

  This is the standard pattern for code-generation tools in Maven (similar to Protobuf, gRPC, ANTLR, etc.).
