# Java volatile access ordering

```
Regarding Java Volatile Variable Rule: A write to a volatile variable Happens-before every subsequent read of that variable In a multi thread context, different threads read/write the volatile var, Seems there is not clear ordering sequence? how to define one "write" is before subsequent "read"?
```


## ANSWER

Great question — this is one of those Java Memory Model rules that sounds vague until you pin down *what “subsequent” actually means*.

Let’s unpack it carefully and kill the confusion. ☕️

---

## The key idea you’re missing

**“Subsequent” does NOT mean later in real time across all threads.**
It means **later in the *synchronization order*** defined by the Java Memory Model (JMM).

The JMM defines a **total order for all accesses to the *same volatile variable***.

That’s the missing ordering you’re looking for.

---

## Volatile variables have a *global order*

For **each volatile variable**, the JVM defines a **single, global, total order** of all reads and writes to that variable.

So even if:

* Thread A writes
* Thread B reads
* Thread C writes
* Thread D reads

…the JVM still linearizes those operations into **one well-defined sequence**.

Example (conceptual order chosen by the JVM):

```
W1 (Thread A)
R1 (Thread B)
W2 (Thread C)
R2 (Thread D)
```

This order:

* is **not necessarily wall-clock time**
* is **not chosen by you**
* **is guaranteed to exist**

---

## What the volatile rule *really* says

> **A write to a volatile variable happens-before every read of that same variable that comes later in the volatile’s synchronization order.**

So:

```
W(x)  →hb→  R(x)
```

**iff** `R(x)` is *after* `W(x)` in that volatile’s global order.

---

## Why this matters (visibility guarantee)

If:

```java
volatile boolean ready;
int data;

Thread A:
data = 42;
ready = true;   // volatile write

Thread B:
if (ready) {    // volatile read
    System.out.println(data);
}
```

Because of the volatile rule:

* `ready = true` happens-before `if (ready)`
* therefore **all writes before the volatile write** (`data = 42`)
  become visible to Thread B

So Thread B **must** see `data == 42`.

---

## What volatile does *not* guarantee

Volatile **does not** guarantee:

* fairness
* which thread “wins”
* real-time ordering
* atomicity of compound actions (`x++`)

Example that is still legal:

```
Thread A: write x = 1
Thread B: write x = 2
Thread C: read x → sees 1 OR 2
```

But:

* it **cannot** see a stale value (like 0)
* it **cannot** see a write that is *after* the read in synchronization order

---

## Mental model that actually works

Think of a volatile variable as having:

* a **single shared timeline**
* every read/write gets a **position on that timeline**
* happens-before is defined **along that line**

Not by clocks. Not by threads. By **JMM ordering**.

---

## One-sentence takeaway

> Even though threads run concurrently, **all accesses to a volatile variable are totally ordered**, and *“subsequent” means later in that JVM-defined order*, not wall-clock time.

If you want, I can also explain:

* how this differs from `synchronized`
* how CPUs enforce this with memory barriers
* or why `volatile` is weaker than `Atomic*` but stronger than plain fields

Just say the word 👀
