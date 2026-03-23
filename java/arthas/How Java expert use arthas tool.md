# #How Java expert use arthas tool


Arthas is one of the most powerful **production JVM debugging tools** used by senior Java engineers. It allows **live inspection of a running JVM without restarting the service**, which is critical in large distributed systems.

Java experts typically use it for **production debugging, performance diagnosis, and class tracing**.

Below is how experienced engineers actually use it.

---

# 1. Attach Arthas to a Running JVM

First step is attaching to a live Java process.

```bash
java -jar arthas-boot.jar
```

You will see something like:

```
* [1]: 12345 com.mycompany.OrderService
```

Select the process ID.

This attaches **without restarting the application**.

---

# 2. Inspect JVM & Threads (Production Incident)

When a system is slow, experts check threads first.

### Show top CPU threads

```
thread -n 5
```

Example output:

```
"Thread-12" cpu=82%
```

This tells you which thread is consuming CPU.

---

### Show thread stack

```
thread 12
```

Example:

```
at OrderService.matchOrder()
at OrderController.submit()
```

This immediately reveals the **hot code path**.

---

# 3. Trace Method Execution (The Most Powerful Feature)

Experts often use **trace** to find slow code.

```
trace com.exchange.matching.MatchEngine match
```

Output:

```
`---match()
    +---validateOrder() 2ms
    +---matchOrder() 45ms
    `---publishTrade() 1ms
```

Now you know **exactly which submethod is slow**.

---

# 4. Watch Method Parameters & Return Values

For debugging logic bugs:

```
watch com.service.OrderService createOrder "{params,returnObj}" -x 2
```

Output example:

```
params = [Order(symbol=BTC, qty=10)]
return = Order(id=12345)
```

This shows **method inputs and outputs in real time**.

---

# 5. Trace Exceptions in Production

To catch hidden exceptions:

```
watch com.service.OrderService createOrder "{throwExp}" -e
```

This prints exceptions when thrown.

---

# 6. Monitor Method Metrics

Experts often use `monitor` to watch method performance.

```
monitor com.service.OrderService createOrder
```

Output every few seconds:

```
total: 200
success: 198
fail: 2
avg-rt: 12ms
```

This is **live performance telemetry**.

---

# 7. Decompile Running Classes

Sometimes you want to verify the **actual code loaded in JVM**.

```
jad com.service.OrderService
```

This prints decompiled code.

This is extremely useful when:

* wrong version deployed
* hotfix applied
* jar mismatch

---

# 8. Check Loaded Classes

```
sc -d com.service.OrderService
```

Shows:

```
classloader
class location
fields
methods
```

This helps detect **classloader conflicts**.

---

# 9. View Method Call Path

To see who calls a method:

```
stack com.service.OrderService createOrder
```

Output:

```
OrderController.submit()
 -> OrderService.createOrder()
```

---

# 10. Inspect Objects Inside JVM

Example:

```
ognl '@java.lang.System@getProperty("java.version")'
```

or inspect Spring beans.

---

# 11. Real Production Example (Trading System)

When order matching becomes slow:

```
thread -n 3
```

Find hot thread.

Then:

```
trace com.exchange.matching.MatchEngine match
```

Output:

```
match()
 + validate() 1ms
 + findLiquidity() 80ms
 + publishTrade() 1ms
```

You immediately know **findLiquidity() is the bottleneck**.

---

# 12. Advanced Feature: Time Tunnel (Record Method Calls)

```
tt -t com.service.OrderService createOrder
```

Then view history:

```
tt -l
```

Replay a call:

```
tt -i 1000
```

This lets you **replay production method calls**.

Very powerful.

---

# Why Java Experts Love Arthas

Because it allows:

• debugging **without restart**
• tracing **real production traffic**
• inspecting **live JVM state**

Compared to traditional debugging:

| Tool         | Production Safe | Live Traffic |
| ------------ | --------------- | ------------ |
| IDE debugger | ❌               | ❌            |
| Logs         | limited         | partial      |
| Arthas       | ✅               | ✅            |

---

# Real Commands Senior Engineers Memorize

```
dashboard
thread -n 5
trace Class method
watch Class method "{params,returnObj}"
monitor Class method
jad Class
sc -d Class
stack Class method
tt -t Class method
```

---

If you want, I can also show:

**How engineers at companies like Alibaba and Ant Group use Arthas to debug massive production systems (10k+ JVMs) with real workflows.**

That workflow is extremely interesting and very different from typical debugging.
