**Arthas线上监控诊断工具**

- 替换运行中的class: <span class="mark">retransform</span>

jad --source-only com.example.demo.arthas.user.UserController \> /tmp/UserController.java

\<compile\>

retransform /tmp/com/example/demo/arthas/user/UserController.class

<span class="mark">恢复</span>

retransform --deleteAll

retransform --classPattern demo.MathGame

- 动态执行代码 ognl 命令

在Arthas里，有一个单独的ognl命令，可以动态执行代码。这个有点秀啊😯😯😯

- 调用static函数

ognl '@java.lang.System@out.println("hello ognl")'

- 获取静态类的静态字段

获取UserController类里的logger字段：

ognl --classLoaderClass org.springframework.boot.loader.LaunchedURLClassLoader @com.example.demo.arthas.user.UserController@logger

通过-x参数控制返回值的展开层数。比如：

ognl --classLoaderClass org.springframework.boot.loader.LaunchedURLClassLoader -x 2 @com.example.demo.arthas.user.UserController@logger

执行多行表达式，赋值给临时变量，返回一个List

ognl '#value1=@System@getProperty("java.home"), \#value2=@System@getProperty("java.runtime.name"), {#value1, \#value2}'

OGNL特殊用法请参考：https://github.com/alibaba/arthas/issues/71

OGNL表达式官方指南：https://commons.apache.org/proper/commons-ognl/language-guide.html

- 单独设置UserController的logger level

ognl --classLoaderClass org.springframework.boot.loader.LaunchedURLClassLoader '@com.example.demo.arthas.user.UserController@logger.setLevel(@ch.qos.logback.classic.Level@DEBUG)'

再次获取UserController@logger，可以发现已经是DEBUG了。

- 查询MathGame实例，调用函数

<span class="mark">查询class hash</span>

\[arthas@11612\]\$ classloader -t

+-BootstrapClassLoader

+-jdk.internal.loader.ClassLoaders\$PlatformClassLoader@6e3a9d87

+-com.taobao.arthas.agent.ArthasClassloader@53476cc5

+-jdk.internal.loader.ClassLoaders\$AppClassLoader@<span class="mark">18b4aac2 // 这个就是MathGame</span>

Affect(row-cnt:4) cost in 2 ms.

**<span class="mark">取MathGame实例，调用 instances\[0\].primeFactors(20)</span>**

\[arthas@11612\]\$ vmtool -c 18b4aac2 -a getInstances --className \*MathGame --express '#val=instances\[0\],#val.primeFactors(20)'

@ArrayList\[

@Integer\[2\],

@Integer\[2\],

@Integer\[5\],

\]

<span class="mark">或者直接调用不使用-c 参数</span>

\[arthas@11612\]\$ vmtool -a getInstances --className \*MathGame --express '#val=instances\[0\],#val.primeFactors(20)'

@ArrayList\[

@Integer\[2\],

@Integer\[2\],

@Integer\[5\],

\]

**JHSDB:基于服务性代理的调试工具**

**JConsole:Java监视与管理控制台**

**VisualVM:多合-故障处理工具**

结合 VisualGC 插件监控GC活动

**BTrace动态日志跟踪**

BTrace能够实现动态修改程序行为，是因为它是基于Java虚拟机的Instrument开发的。Instrument是Java虚拟机工具接口(JavaVirtualMachineToolInterface，JVMTI)的重要组件，提供了一套代理(Agent)机制，使得第三方工具程序可以以代理的方式访问和修改Java虚拟机内部的数据。阿里巴巴开源的诊断工具Arthas也通过Instrument实现了与BTrace类似的功能。

**Java Mission Control:可持续在线的监控工具**
