### [**<u>https://github.com/Snailclimb/JavaGuide/blob/main/docs/tools/maven/maven-core-concepts.md</u>**](https://github.com/Snailclimb/JavaGuide/blob/main/docs/tools/maven/maven-core-concepts.md)

### **依赖范围**

classpath 用于指定 .class 文件存放的位置，类加载器会从该路径中加载所需的 .class 文件到内存中。

Maven 在编译、执行测试、实际运行有着三套不同的 classpath：

- 编译 classpath：编译主代码有效

- 测试 classpath：编译、运行测试代码有效

- 运行 classpath：项目运行时有效

Maven 的依赖范围如下：

- <span class="mark">compile</span>：编译依赖范围（默认），使用此依赖范围对于编译、测试、运行三种都有效，即在编译、测试和运行的时候都要使用该依赖 Jar 包。

- <span class="mark">test</span>：测试依赖范围，从字面意思就可以知道此依赖范围只能用于测试，而在编译和运行项目时无法使用此类依赖，典型的是 JUnit，它只用于编译测试代码和运行测试代码的时候才需要。

- <span class="mark">Provided：= compile + test</span> 此依赖范围，对于编译和测试有效，而对运行时无效。比如 servlet-api.jar 在 Tomcat 中已经提供了，我们只需要的是编译期提供而已。

- <span class="mark">runtime</span>：运行时依赖范围，对于测试和运行有效，但是在编译主代码时无效，典型的就是 JDBC 驱动实现。

- <span class="mark">system</span>：系统依赖范围，使用 system 范围的依赖时必须通过 systemPath 元素显示地指定依赖文件的路径，不依赖 Maven 仓库解析，所以可能会造成建构的不可移植

**2、项目的两个依赖同时引入了某个依赖。**

举个例子，项目存在下面这样的依赖关系：

依赖链路一：A -\> B -\> C -\> X(1.0)

依赖链路二：A -\> D -\> X(2.0)

<span class="mark">路径最短优先</span>

依赖链路一：A -\> B -\> C -\> X(1.0) // dist = 3

依赖链路二：A -\> D -\> X(2.0) // dist = 2

依赖链路二的路径最短，因此，X(2.0)会被解析使用。

<span class="mark">声明顺序优先</span>

在依赖路径长度相等的前提下，在 pom.xml 中依赖声明的顺序决定了谁会被解析使用，顺序最前的那个依赖优胜。该例中，如果 B 的依赖声明在 D 之前，那么 X (1.0)就会被解析使用。

\<!-- A pom.xml --\>

\<dependencies\>

...

dependency B

...

dependency D

\</dependencies\>

## **Maven 仓库**

Maven 仓库分为：

- <span class="mark">本地仓库</span>：运行 Maven 的计算机上的一个目录，它缓存远程下载的构件并包含尚未发布的临时构件。settings.xml 文件中可以看到 Maven 的本地仓库路径配置，默认本地仓库路径是在 <span class="mark">\${user.home}/.m2/repository</span>。

- <span class="mark">远程仓库</span>：官方或者其他组织维护的 Maven 仓库。

Maven 远程仓库可以分为：

- 中央仓库：这个仓库是由 Maven 社区来维护的，里面存放了绝大多数开源软件的包，并且是作为 Maven 的默认配置，不需要开发者额外配置。另外为了方便查询，还提供了一个[<u>查询地址</u>](https://search.maven.org/)，开发者可以通过这个地址更快的搜索需要构件的坐标。

- 私服：私服是一种特殊的远程 Maven 仓库，它是<span class="mark">架设在局域网内的仓库服务</span>，私服一般被配置为互联网远程仓库的镜像，供局域网内的 Maven 用户使用。

- 其他的公共仓库：有一些公共仓库是为了加速访问（比如阿里云 Maven 镜像仓库）或者部分构件不存在于中央仓库中。

Maven 依赖包寻找顺序：

1.  先去本地仓库找寻，有的话，直接使用。

2.  本地仓库没有找到的话，会去远程仓库找寻，下载包到本地仓库。

3.  远程仓库没有找到的话，会报错。
