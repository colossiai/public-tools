# java maven 如何管理多模塊項目


Maven 是一个强大的项目管理和构建工具，尤其擅长管理多模块项目（multi-module projects）。多模块项目通常将一个大型系统拆分成多个较小的、可重用的模块，每个模块负责独立的功能，最后组合成一个完整的应用。这样做有助于代码复用、职责分离、并行开发和独立构建。

下面详细介绍 Maven 如何管理多模块项目。

---

## 1. 多模块项目的结构

Maven 多模块项目有一个**父模块（parent）** 和多个**子模块（module）**。父模块本身通常不包含源代码，其 `pom.xml` 的打包类型（packaging）必须是 `pom`。子模块可以是任意打包类型（如 `jar`、`war`、`pom` 等）。

典型的目录结构如下：
```
my-multi-module-project/
├── pom.xml                (父 POM)
├── module-common/
│   └── pom.xml            (子模块，打包为 jar)
├── module-core/
│   └── pom.xml            (子模块，打包为 jar)
└── module-web/
    └── pom.xml            (子模块，打包为 war，依赖 common 和 core)
```

---

## 2. 父 POM 的配置

父 POM 的核心作用是**聚合模块**和**管理依赖/插件**。

### 2.1 聚合模块
通过 `<modules>` 元素声明子模块，告诉 Maven 哪些目录是模块。当在父模块目录执行构建命令时，Maven 会自动按顺序构建这些子模块。
```xml
<project>
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>my-parent</artifactId>
    <version>1.0.0</version>
    <packaging>pom</packaging>   <!-- 必须为 pom -->

    <modules>
        <module>module-common</module>
        <module>module-core</module>
        <module>module-web</module>
    </modules>
</project>
```

### 2.2 依赖管理（dependencyManagement）
在父 POM 中使用 `<dependencyManagement>` 可以统一声明项目中所有可能用到的依赖的版本，但**不会立即引入依赖**。子模块需要显式声明依赖，但可以省略版本号，从而保证版本一致性。
```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>5.3.20</version>
        </dependency>
    </dependencies>
</dependencyManagement>
```

### 2.3 插件管理（pluginManagement）
类似地，`<pluginManagement>` 用于统一管理插件的配置和版本，子模块声明插件时可省略版本和公共配置。
```xml
<build>
    <pluginManagement>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.10.1</version>
                <configuration>
                    <source>11</source>
                    <target>11</target>
                </configuration>
            </plugin>
        </plugins>
    </pluginManagement>
</build>
```

### 2.4 公共属性定义
在父 POM 中定义常用属性，方便子模块引用。
```xml
<properties>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <maven.compiler.source>11</maven.compiler.source>
    <maven.compiler.target>11</maven.compiler.target>
</properties>
```

---

## 3. 子模块的配置

每个子模块都有自己的 `pom.xml`，并声明父模块。

### 3.1 继承父 POM
使用 `<parent>` 元素指向父模块。
```xml
<project>
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>com.example</groupId>
        <artifactId>my-parent</artifactId>
        <version>1.0.0</version>
        <relativePath>../pom.xml</relativePath>   <!-- 父POM的相对路径 -->
    </parent>

    <artifactId>module-common</artifactId>
    <packaging>jar</packaging>   <!-- 子模块可以是 jar/war/pom 等 -->
</project>
```
子模块会继承父 POM 中的 `groupId` 和 `version`（除非显式覆盖），但通常需要指定自己的 `artifactId`。

### 3.2 模块间依赖
一个子模块可以依赖另一个子模块，直接在 `<dependencies>` 中引入即可。由于版本已在父 POM 的 dependencyManagement 中定义（通常使用 `{project.version}` 引用），可以省略版本号。
```xml
<dependencies>
    <dependency>
        <groupId>com.example</groupId>
        <artifactId>module-common</artifactId>
        <version>${project.version}</version>   <!-- 通常版本号与父模块一致 -->
    </dependency>
</dependencies>
```

---

## 4. 构建命令

Maven 提供了灵活的构建选项来操作多模块项目。

- **构建所有模块**：在父模块目录执行
  ```bash
  mvn clean install
  ```
  这会递归地构建所有子模块，按模块间依赖顺序执行。

- **仅构建指定模块**：使用 `-pl`（--projects）指定模块列表，`-am`（--also-make）同时构建依赖的模块。
  ```bash
  mvn clean install -pl module-web -am
  ```
  该命令会构建 `module-web` 以及它所依赖的模块（如 `module-common`）。

- **跳过某些模块**：可以使用 `-rf`（--resume-from）从某个模块继续构建。

- **查看依赖关系**：
  ```bash
  mvn dependency:tree
  ```

---

## 5. 最佳实践与注意事项

1. **版本管理**：所有子模块通常使用与父模块相同的版本，保持一致性。如果需要独立版本，可以在子模块中显式声明 `<version>`。
2. **依赖范围**：合理使用 scope（如 `provided`、`test`），避免在子模块中引入多余的传递依赖。
3. **避免循环依赖**：模块之间不能形成循环依赖，否则 Maven 无法确定构建顺序。
4. **父模块不包含代码**：父模块的 `src/main/java` 目录通常为空，它只负责聚合和管理。
5. **使用 `relativePath`**：如果子模块的父 POM 不在标准位置（如当前目录的 `../pom.xml`），需要正确设置 `<relativePath>`。

---

## 6. 实际示例

假设有一个电商项目，拆分为三个模块：
- `ecommerce-parent`（父模块）
- `ecommerce-common`（工具类、常量）
- `ecommerce-service`（业务逻辑，依赖 common）
- `ecommerce-web`（Web 层，依赖 service）

父 POM 聚合并管理依赖版本，子模块继承父 POM，并声明各自的依赖。构建时只需在父目录运行 `mvn clean package`，即可生成对应的 jar/war 文件。

---

通过以上方式，Maven 能够清晰、高效地管理多模块项目，提升大型项目的可维护性和构建效率。


# mvn install 不是安裝模塊在 ~/.m2 嗎？

是的，您理解得完全正确！`mvn install` 会将模块构建并**安装到本地 Maven 仓库（通常是 `~/.m2/repository`）**。这是 Maven 生命周期中的一个核心阶段，下面详细解释一下它的作用以及为什么在多模块项目中很重要。

---

## `mvn install` 的作用

当您在某个模块上执行 `mvn install` 时，Maven 会依次执行以下阶段：
1. `validate`：验证项目是否正确且所有必要信息可用。
2. `compile`：编译源代码。
3. `test`：运行测试（可选，可跳过）。
4. `package`：将编译后的代码打包成指定格式（如 jar、war）。
5. `verify`：运行集成测试等检查。
6. **`install`**：将打包好的构件（jar/war 等）复制到本地仓库 `~/.m2/repository` 中，按照坐标（groupId、artifactId、version）存放。

执行完 `install` 后，您的模块就“安装”到了本地仓库，可以被**其他本地项目**或**同一台机器上的其他 Maven 构建**作为依赖引用。

---

## 在多模块项目中的意义

在多模块项目中，模块之间常常有依赖关系，比如 `module-web` 依赖 `module-common`。当您直接在 `module-web` 目录下执行 `mvn compile` 时，Maven 需要解析 `module-common` 这个依赖。

如果 `module-common` **尚未安装到本地仓库**，Maven 会尝试从远程中央仓库下载，但那里显然没有您的私有模块，构建就会失败。  
因此，为了让模块间的依赖正常工作，**必须先 install 被依赖的模块**。

当您在父模块目录执行 `mvn install` 时，Maven 会按照模块依赖顺序（由 Maven 自动计算）依次执行：
1. 先构建并 install 底层模块（如 `module-common`）。
2. 然后构建并 install 上层模块（如 `module-web`）。

这样，所有模块都被安装到了本地仓库，模块之间的依赖就可以通过本地仓库顺利解析，构建才能成功。

---

## `install` 与 `package` 的区别

- **`mvn package`**：只将模块打包到该模块的 `target/` 目录下（如 `target/my-module-1.0.jar`），但**不会放入本地仓库**。其他模块如果依赖它，可能无法找到该构件（除非在 IDE 中通过项目依赖配置解决，但纯命令行构建通常会失败）。
- **`mvn install`**：在 package 的基础上，将打包好的构件复制到本地仓库，使其成为可被其他 Maven 项目引用的正式依赖。

因此，在多模块开发中，**install 是让模块间依赖生效的关键步骤**。

---

## 补充说明

- **`~/.m2/repository` 的结构**：安装后的模块会按照 groupId 的包名结构存放，例如 `com/example/module-common/1.0.0/module-common-1.0.0.jar`。
- **其他命令**：如果您的项目最终需要部署到远程仓库（如公司私服或 Maven Central），会用到 `mvn deploy`，它将构件部署到远程仓库，供其他开发人员或 CI 服务器使用。
- **IDE 中的行为**：在 IntelliJ IDEA 或 Eclipse 中，如果导入的是多模块 Maven 项目，IDE 通常会直接通过项目引用（而非本地仓库）处理模块间依赖，因此可能不需要显式 install。但在纯命令行构建或 CI 环境中，install 是必不可少的。

所以，您的理解非常准确：`mvn install` 确实是将模块安装到 `~/.m2` 仓库中，使得其他模块能够依赖它。

# 如何跑其中一個模塊呢？ module-web

在多模块 Maven 项目中，单独运行其中一个模块（如 `module-web`）通常涉及两个步骤：**构建该模块**（及其依赖）和**执行该模块**。具体如何运行取决于模块的类型（例如是 Spring Boot 应用、普通 Web 应用还是其他）。

以下是几种常见的方法：

---

## 1. 构建指定模块

### 方法一：在父项目目录使用 `-pl` 指定模块
在包含父 `pom.xml` 的根目录下执行：
```bash
mvn clean package -pl module-web -am
```
- `-pl module-web`：指定要构建的模块列表（`-pl` 即 `--projects`）。
- `-am`：`--also-make`，同时构建该模块所依赖的其他模块（如 `module-common`），确保依赖已构建。
- 如果不加 `-am`，只构建 `module-web` 本身，但如果 `module-web` 依赖其他模块且它们尚未安装到本地仓库，则会失败。

### 方法二：直接进入子模块目录
进入 `module-web` 目录：
```bash
cd module-web
mvn clean package
```
此时，Maven 会在当前模块内执行构建。但要注意，如果 `module-web` 依赖同一项目的其他模块，这些依赖的模块**必须已经安装到本地仓库**（即之前执行过 `mvn install`），否则会报错找不到依赖。

建议初次构建时先在父目录执行一次 `mvn install`，确保所有模块都被安装到本地仓库。之后就可以直接在子模块目录进行增量构建。

---

## 2. 运行模块

运行方式取决于模块的打包类型和框架。

### 情况 A：模块是 Spring Boot 应用（打包为可执行 jar）
如果 `module-web` 是一个 Spring Boot 项目，其 `pom.xml` 中包含了 `spring-boot-maven-plugin`，则可以直接运行：
```bash
# 在 module-web 目录下
mvn spring-boot:run
```
或者在父目录指定模块运行：
```bash
mvn spring-boot:run -pl module-web
```

### 情况 B：模块是普通 Web 应用（打包为 war）
如果是一个标准的 war 项目，通常需要部署到外部 Servlet 容器（如 Tomcat、Jetty）中运行。您可以使用 Maven 插件来简化：

- **使用 Tomcat Maven 插件**（在 `module-web` 的 `pom.xml` 中配置 `tomcat7-maven-plugin` 或 `tomcat10-maven-plugin`）：
  ```bash
  mvn tomcat7:run -pl module-web
  ```
- **使用 Jetty Maven 插件**：
  ```bash
  mvn jetty:run -pl module-web
  ```

需要先在 `pom.xml` 中添加对应插件的配置（通常放在 `module-web` 的 `build` 中）。

### 情况 C：模块是一个普通 Java 应用（有 main 类）
如果模块包含可执行的 main 类，可以使用 `exec-maven-plugin`：
```bash
mvn exec:java -Dexec.mainClass="com.example.Main" -pl module-web
```
或者先在模块的 `pom.xml` 中配置好插件，然后直接运行 `mvn exec:java`。

---

## 3. 使用 IDE 运行（推荐开发时使用）

在 IntelliJ IDEA 或 Eclipse 中，您可以直接在项目结构中找到 `module-web`，然后：

- 如果是 Spring Boot 应用，直接右键点击主类运行。
- 如果是 Web 应用，配置 Tomcat 等服务器，将 war 部署后运行。
- IDE 会自动处理模块间的依赖（通过项目依赖而非本地仓库），无需手动 install。

这种方式对开发调试更友好。

---

## 4. 注意依赖一致性

如果模块间的依赖频繁变动，建议在父目录执行 `mvn clean install` 更新本地仓库，或者始终使用 `-am` 参数构建以确保依赖是最新的。

例如：
```bash
mvn clean install -pl module-web -am
```
这会先构建所有依赖模块（`module-common` 等）并安装到本地仓库，然后构建 `module-web`。构建完成后，再按需运行。

---

## 总结

| 目标 | 命令示例 |
|------|----------|
| 只构建 module-web（含依赖） | `mvn clean package -pl module-web -am` |
| 进入子模块目录构建 | `cd module-web; mvn clean package` |
| 运行 Spring Boot 模块 | `mvn spring-boot:run -pl module-web` |
| 运行 Web 模块（Tomcat） | `mvn tomcat7:run -pl module-web` |
| 运行普通 Java 主类 | `mvn exec:java -pl module-web -Dexec.mainClass=...` |

根据您的实际项目类型，选择合适的方式即可。如果有具体的框架或需求，可以进一步说明，以便提供更精确的指导。