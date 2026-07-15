`EAGAIN` 是 Linux/Unix 系统编程中最常见的错误码之一，也是理解**非阻塞 I/O**的关键。

很多初学者看到：

```c
read(fd, buf, sizeof(buf));
```

返回：

```c
-1
errno = EAGAIN
```

会以为出错了。

**其实不是。**

> **`EAGAIN` 的真正意思是："现在做不了，请稍后再试（Try Again Later）"。**

---

# 从名字开始

`EAGAIN`

就是：

```text
Error AGAIN
```

意思是：

> **现在没有条件完成这个操作，以后再试。**

有些系统上：

```text
EWOULDBLOCK
```

与 `EAGAIN` 是同一个值。

Linux 上：

```c
EAGAIN == EWOULDBLOCK
```

---

# 为什么会出现 EAGAIN？

来看一个 socket。

假设：

```text
TCP Buffer

---------------
ABCDEF
---------------
```

程序：

```c
read(fd, buf, 3);
```

读走：

```text
ABC
```

Buffer：

```text
DEF
```

继续：

```c
read(fd, buf, 3);
```

读走：

```text
DEF
```

Buffer：

```text
(empty)
```

再调用：

```c
read(fd, buf, 3);
```

这时候怎么办？

---

## 阻塞 socket

默认 socket 是阻塞的。

于是：

```text
没有数据

↓

read()

↓

一直等待...
```

程序停在那里。

直到：

```text
网络收到数据

↓

返回
```

例如：

```text
客户端：

HELLO
```

read 才返回。

---

## 非阻塞 socket

如果：

```c
fcntl(fd, F_SETFL, O_NONBLOCK);
```

变成：

**Non-blocking Socket**

那么：

```text
Buffer为空
```

read 不会等待。

而是立即返回：

```c
read()

↓

-1

errno = EAGAIN
```

意思：

> **目前没有数据可以读。**

不是错误。

只是：

```text
现在没有

以后再来
```

---

# 一个完整时间线

假设：

```
时间0：

Buffer:

(empty)
```

程序：

```c
read()
```

得到：

```text
EAGAIN
```

过了 100ms：

客户端发送：

```text
HELLO
```

Buffer：

```text
HELLO
```

再次：

```c
read()
```

返回：

```text
HELLO
```

继续：

```c
read()
```

Buffer 已空。

于是：

```text
EAGAIN
```

---

# ET 为什么一直读到 EAGAIN？

例如：

Buffer：

```text
ABCDEFGHIJK
```

ET 通知：

```text
epoll_wait()

↓

fd ready
```

程序：

```c
while (true) {
    n = read(...);

    if (n > 0)
        process();

    else if (errno == EAGAIN)
        break;
}
```

第一次：

```
ABCDEFGHIJK
```

↓

```
read

↓

ABCDEFG
```

剩：

```
HIJK
```

继续：

```
read
```

↓

```
HIJK
```

剩：

```
(empty)
```

继续：

```
read
```

返回：

```text
-1
errno = EAGAIN
```

说明：

> **缓冲区已经彻底读空。**

于是：

```text
退出while
```

等待下一次 epoll 通知。

---

# 为什么不是返回 0？

很多人容易混淆：

```text
EAGAIN
```

和：

```text
read == 0
```

它们完全不同。

## read == 0

表示：

> **对方关闭连接（EOF）。**

例如：

客户端：

```text
close(socket)
```

服务器：

```c
read()

↓

0
```

意味着：

```text
连接结束
```

以后不会再有数据。

---

## EAGAIN

表示：

> **连接还活着。**

只是：

```text
暂时没有数据
```

以后：

```text
客户端还能继续发送
```

所以：

```text
EAGAIN

≠ EOF
```

---

# write() 也会出现 EAGAIN

不仅：

```c
read()
```

会出现。

```c
write()
```

也一样。

例如：

TCP Send Buffer：

```text
##################
满了
##################
```

程序：

```c
write(...)
```

阻塞 socket：

```text
等待

直到发送缓冲区有空间
```

非阻塞 socket：

立即返回：

```text
-1

errno = EAGAIN
```

意思：

> **现在发送缓冲区没有空间，请稍后再写。**

等 `epoll` 通知这个 socket **可写（`EPOLLOUT`）** 后，再继续发送剩余数据。

---

# 一个形象的比喻

假设：

你去银行窗口办理业务。

### 阻塞模式

工作人员说：

> "请站着等。"

你一直等。

直到轮到你。

---

### 非阻塞模式

工作人员说：

> "现在没空。"

给你一张号码：

```text
EAGAIN
```

意思：

> "稍后再来。"

你不会一直站在那里浪费时间。

而是去办别的事情。

等系统通知：

```text
现在可以了
```

你再回来。

这正是**事件驱动（Event-driven）**编程的思想。

---

# 总结

| 返回值                      | 含义             | 是否错误     | 下一步          |
| ------------------------ | -------------- | -------- | ------------ |
| `n > 0`                  | 成功读取 `n` 字节    | 否        | 继续处理数据       |
| `0`                      | 对端关闭连接（EOF）    | 否        | 关闭本地连接       |
| `-1` + `errno == EAGAIN` | 暂时没有数据（或暂时不能写） | **不是错误** | 等待下一次可读/可写事件 |
| `-1` + 其他 `errno`        | 真正发生错误         | 是        | 根据错误处理或关闭连接  |

## 一句话记忆

* **`EAGAIN` = "现在不行，稍后再试。"**
* **`read() == 0` = "连接已经结束，不会再有数据了。"**
* **ET 模式下，`read()` 一直循环到 `EAGAIN`，才能确定内核接收缓冲区已经被读空。**
