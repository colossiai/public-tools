https://juejin.cn/post/6959333602748268575

**ThreadLocal的实现原理**

ThreadLocal变量只在单个线程内可见，那它是如何做到的呢？我们先从最基本的get()方法说起

public T get() {

//获得当前线程

Thread t = Thread.currentThread();

//每个线程 都有一个自己的ThreadLocalMap，

//ThreadLocalMap里就保存着所有的ThreadLocal变量

ThreadLocalMap map = getMap(t);

if (map != null) {

//ThreadLocalMap的key就是当前ThreadLocal对象实例，

//多个ThreadLocal变量都是放在这个map中的

ThreadLocalMap.Entry e = map.getEntry(this);

if (e != null) {

@SuppressWarnings("unchecked")

//从map里取出来的值就是我们需要的这个ThreadLocal变量

T result = (T)e.value;

return result;

}

}

// 如果map没有初始化，那么在这里初始化一下

return setInitialValue();

}

可以看到，所谓的ThreadLocal变量就是保存在每个线程的map中的。这个map就是Thread对象中的threadLocals字段。如下：

ThreadLocal.ThreadLocalMap threadLocals = null;

**一个良好的习惯依然是：当你不需要这个ThreadLocal变量时，主动调用remove()，这样对整个系统是有好处的。**

[<u>https://www.liaoxuefeng.com/wiki/1252599548343744/1306581251653666</u>](https://www.liaoxuefeng.com/wiki/1252599548343744/1306581251653666)

廖雪峰

/\*

为了保证能释放ThreadLocal关联的实例，我们可以通过AutoCloseable接口配合try (resource) {...}结构，

让编译器自动为我们关闭。例如，

一个保存了当前用户名的ThreadLocal可以封装为一个UserContext对象：

\*/

public class UserContext implements AutoCloseable {

static final ThreadLocal\<String\> ctx = new ThreadLocal\<\>();

public UserContext(String user) {

ctx.set(user);

}

public static String currentUser() {

return ctx.get();

}

@Override

public void close() {

ctx.remove();

}

}

// 使用的时候，我们借助try (resource) {...}结构，可以这么写：

try(var ctx = new UserContext("Bob")) {

// 可任意调用UserContext.currentUser():

String currentUser = UserContext.currentUser();

} // 在此自动调用UserContext.close()方法释放ThreadLocal关联对象

/\*

\* 这样就在UserContext中完全封装了ThreadLocal，外部代码在try (resource)

\* {...}内部可以随时调用UserContext.currentUser()获取当前线程绑定的用户名。

\*

\*/
