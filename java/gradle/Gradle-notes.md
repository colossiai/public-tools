# Gradle build

* build sub-module: `gradle :<submoduleName>:<taskName>`

example `./gradlew :ipc-core:build`


# Gradle build output 

```
├── build
│   ├── classes
│   │   └── java
│   ├── distributions
│   │   ├── ipc-core.tar
│   │   └── ipc-core.zip
│   ├── generated
│   │   └── sources
│   ├── libs
│   │   └── ipc-core.jar
│   ├── reports
│   │   └── checkstyle
│   ├── resources
│   │   ├── main
│   │   └── test
│   ├── scripts
│   │   ├── ipc-core
│   │   └── ipc-core.bat
│   └── tmp
│       ├── checkstyleMain
│       ├── compileJava
│       └── jar
```


Here’s a breakdown of the folders you see in the build output of your Gradle-built module (e.g. the `ipc-core` subproject) and what they typically contain:

Here’s what each folder means / contains, with some commentary:

---

### `classes/java`

* This is where your compiled `.class` files for the Java source go.
* Under a typical `java` plugin (the default for JVM projects) the `compileJava` task outputs classes under something like `build/classes/java/main` (for the main source set) and `build/classes/java/test` (for test) unless configured differently.
* The `classes` directory essentially holds the “output of compilation” for source code.

---

### `resources/main` and `resources/test`

* These are the processed resource files (e.g., `.properties`, `.xml`, other non­Java resources) for “main” and “test” source sets.
* Anything you placed under `src/main/resources` ends up in `build/resources/main`, etc.
* At runtime or packaging, these resource dirs are merged (or used) together with the class files.

---

### `libs`

* This directory holds produced library artifacts—in your case `ipc-core.jar`.
* The `jar` task (or whichever packaging task is used) bundles your compiled class files + resources into this JAR.
* Having `build/libs/ipc-core.jar` is the convention. (See note: by default JARs go to `build/libs`). ([Stack Overflow][1])

---

### `distributions`

* This folder is created by the `distribution` or `application` plugin (or tasks like `distZip`/`distTar`) if your project is set up to package the project as a runnable or distributable bundle.
* The `.zip` and `.tar` files (e.g. `ipc-core.zip`, `ipc-core.tar`) are zipped/tarred distributions of your module: typically containing the JAR(s) plus startup scripts, configuration, resources, etc.
* For example, when the `application` plugin is applied, you might get `installDist`, `distZip`, `distTar` tasks generating these.

---

### `scripts`

* This folder contains wrapper scripts or start-up scripts generated as part of distribution. For example: `ipc-core` (Unix shell script) and `ipc-core.bat` (Windows batch script).
* These are used when you want to run your application (or module) rather than just use it as a library. Typically distributed in a `bin/` directory in the distribution bundle.

---

### `generated/sources`

* If you have code generation (e.g., via annotation processors, or via some plugin that generates source code at build time), the generated source files are placed here.
* Then they’ll be compiled along with your hand-written source.
* This is helpful for knowing that your build is not only compiling your own code but any generated code.

---

### `reports/checkstyle`

* Build tools like static analysis, linting, checkstyle, etc will output HTML/CSV reports here.
* For example the `checkstyleMain` task might output a report under `build/reports/checkstyle` summarizing findings of style violations.

---

### `tmp`

* Temporary build files (intermediate files) used during build execution.
* E.g., `compileJava` may have a temporary directory storing incremental compile metadata; `jar` may have staging directories, etc.
* These are usually not part of final artifacts, and cleaned up by the `clean` task (which deletes the `build` directory by default).

---

### How this ties into Gradle conventions

* According to the Gradle documentation, the `build/` directory is the standard output directory for a project: all generated stuff, classes, jars, etc go under `build`. ([Gradle Documentation][2])
* The plugin (e.g., `java`, `application`, `distribution`) dictates which tasks run and what gets output where.
* For example, the `java` plugin will generate classes, resources, jars; the `application` + `distribution` plugin will generate distributions (zip/tar) and start scripts.

---

### What you can infer for your `ipc-core` module

Based on the output you posted:

* The module is producing a JAR (`build/libs/ipc-core.jar`), so it’s being built as a library (or at least as a module).
* The module also produces a distribution (`build/distributions/ipc-core.zip` and `.tar`) plus scripts (`build/scripts/…`), so this suggests the module is also set up with the `application` or `distribution` plugin (or custom equivalent) to be runnable/distributable, not just a library.
* The existence of `generated/sources` indicates there’s some code generation in your build (maybe via annotation processors or a custom plugin).
* You get checkstyle reports, so the build includes static analysis.
* Everything is under `build/` which means `./gradlew clean` will remove all these outputs.

---



# Gradle run mainClass

## We can't run mainClass from jar since sometimes it require dependencies

```bash
java -cp aeron-core/build/libs/aeron-core.jar com.aeroncookbook.aeron.rpc.server.Server

Error: Unable to initialize main class com.aeroncookbook.aeron.rpc.server.Server
Caused by: java.lang.NoClassDefFoundError: org/agrona/concurrent/Agent

```

## We need to define mainClass in sub-module's build.gradle.kts: `aeron-core/build.gradle.kts`

```kts


plugins {
    application
}

application {
    mainClass.set(project.findProperty("mainClass")?.toString() ?: "com.example.DefaultMain")
}
```

## then run sub-module `aeron-core`

```bash
./gradlew :aeron-core:build
./gradlew :aeron-core:run -PmainClass=com.aeroncookbook.aeron.rpc.server.Server
```


# Gradle fix UnsafeApi runtime error

* Aeron/argona example

```kts
application {
    /*
    Fix UnsafeApi err:

    ./gradlew :aeron-core:run -PmainClass=com.aeroncookbook.aeron.rpc.server.Server

    > Task :aeron-core:run
    Exception in thread "main" java.lang.IllegalAccessError: class org.agrona.UnsafeApi (in unnamed module @0x21213b92) cannot access class jdk.internal.misc.Unsafe (in module java.base) because module java.base does not export jdk.internal.misc to unnamed module @0x21213b92
            at org.agrona.UnsafeApi.getUnsafe(UnsafeApi.java)
            at org.agrona.UnsafeApi.<clinit>(UnsafeApi.java)
            at org.agrona.BufferUtil.<clinit>(BufferUtil.java:43)
            at org.agrona.concurrent.UnsafeBuffer.wrap(UnsafeBuffer.java:176)
            at org.agrona.concurrent.UnsafeBuffer.<init>(UnsafeBuffer.java:91)
            at io.aeron.driver.Configuration.flowControlGroupTag(Configuration.java:1501)
            at io.aeron.driver.MediaDriver$Context.<init>(MediaDriver.java:511)
            at com.aeroncookbook.aeron.rpc.server.Server.main(Server.java:41)

     */    
     
    applicationDefaultJvmArgs = listOf(
        "--add-opens", "java.base/jdk.internal.misc=ALL-UNNAMED",
        "--add-opens", "java.base/sun.nio.ch=ALL-UNNAMED",
        "--add-opens", "java.base/java.nio=ALL-UNNAMED",
        "--add-opens", "java.base/sun.misc=ALL-UNNAMED"
    )    
}

```