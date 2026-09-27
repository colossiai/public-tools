### **Key Differences**

| **Aspect** | **Concurrent Execution** | **Parallel Execution** |
|----|----|----|
| **Execution Style** | Interleaved <span class="mark">(time-sliced</span>) tasks. | Simultaneous tasks. |
| **Hardware** | Can occur on a <span class="mark">single CPU</span>. | <span class="mark">Requires multiple CPUs/cores</span>. |
| **Goal** | Task management. | Task speed-up. |
| **Example** | Event-driven programming. | Matrix multiplication on a GPU. |

In summary,

**concurrency** is about dealing with multiple tasks <span class="mark">logically</span> at the same time, while

**parallelism** is about doing multiple tasks <span class="mark">physically</span> at the same time.
