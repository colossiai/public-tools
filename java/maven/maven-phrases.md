In Apache Maven, a **build lifecycle** is a sequence of **phases executed in order**. When you run a command like `mvn test`, Maven executes **all phases up to that phase**.

The main lifecycle most developers use is the **Default Lifecycle**.

---

# Full Maven Lifecycle Timeline

Below is the **chronological order of phases** from start to finish.

```
1  validate
2  initialize
3  generate-sources
4  process-sources
5  generate-resources
6  process-resources
7  compile
8  process-classes
9  generate-test-sources
10 process-test-sources
11 generate-test-resources
12 process-test-resources
13 test-compile
14 process-test-classes
15 test
16 prepare-package
17 package
18 pre-integration-test
19 integration-test
20 post-integration-test
21 verify
22 install
23 deploy
```

Think of it like a **timeline pipeline**:

```
validate
   ↓
compile main code
   ↓
compile test code
   ↓
run tests
   ↓
package artifact
   ↓
install locally
   ↓
deploy to remote repo
```

---

# Visual Timeline

```
SOURCE PREP
 ├─ validate
 ├─ initialize
 ├─ generate-sources
 └─ process-sources

MAIN BUILD
 ├─ generate-resources
 ├─ process-resources
 ├─ compile
 └─ process-classes

TEST BUILD
 ├─ generate-test-sources
 ├─ process-test-sources
 ├─ generate-test-resources
 ├─ process-test-resources
 ├─ test-compile
 ├─ process-test-classes
 └─ test

PACKAGING
 ├─ prepare-package
 └─ package

INTEGRATION TEST
 ├─ pre-integration-test
 ├─ integration-test
 └─ post-integration-test

FINALIZATION
 ├─ verify
 ├─ install
 └─ deploy
```

---

# Example: What each command runs

### `mvn compile`

Runs phases **1 → 7**

```
validate
initialize
generate-sources
process-sources
generate-resources
process-resources
compile
```

Compiles:

```
src/main/java → target/classes
```

---

### `mvn test-compile`

Runs phases **1 → 13**

Adds:

```
generate-test-sources
process-test-sources
generate-test-resources
process-test-resources
test-compile
```

Compiles:

```
src/main/java → target/classes
src/test/java → target/test-classes
```

---

### `mvn test`

Runs phases **1 → 15**

This triggers the test runner (usually Maven Surefire Plugin).

---

### `mvn package`

Runs phases **1 → 17**

Creates artifact like:

```
target/myapp.jar
target/myapp.war
```

---

### `mvn install`

Runs phases **1 → 22**

Installs artifact to local repo:

```
~/.m2/repository
```

---

### `mvn deploy`

Runs the **entire lifecycle (1 → 23)**

Uploads artifact to a remote repo such as:

* Sonatype Nexus Repository Manager
* JFrog Artifactory

---

# 3 Additional Lifecycles (Often Forgotten)

Maven actually has **3 lifecycles**:

### 1️⃣ Default lifecycle (main build)

The one we listed above.

---

### 2️⃣ Clean lifecycle

```
pre-clean
clean
post-clean
```

Example:

```
mvn clean
```

Deletes:

```
target/
```

---

### 3️⃣ Site lifecycle

Used to generate project documentation.

```
pre-site
site
post-site
site-deploy
```

Produces documentation like:

```
target/site/index.html
```

---

# Senior Java Engineer Tip

Most developers **only remember 6 key phases**:

```
clean
compile
test
package
install
deploy
```

Typical CI/CD pipeline:

```
mvn clean package
mvn clean install
mvn clean deploy
```

---

💡 Since you were debugging **Surefire test discovery errors earlier**, another useful trick is:

```
mvnd -X test
```

This prints **plugin execution per phase**, which helps locate exactly where the build fails.

---

If you want, I can also show **how Maven plugins attach to each phase** (e.g., Surefire, Compiler, Jar plugin). That diagram makes Maven behavior much clearer and is something many senior Java engineers memorize.
