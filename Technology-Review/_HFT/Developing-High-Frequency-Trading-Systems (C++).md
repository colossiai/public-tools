**Use case - Building an FX high-frequency trading system**

A company needs an HFT system capable of sending an order within 20 microseconds. To do this, the company can follow this approach:

• Choose a <span class="mark">multi-process architecture</span> over a multi-core architecture.

• Ensure each process is <span class="mark">pinned to a specific core</span> to reduce context switches.

• Have processes communicating over a <span class="mark">circular buffer (lock-free data structure)</span> in shared memory.

• Design the network stack using <span class="mark">Solarflare OpenOnload</span> for network acceleration.

• <span class="mark">Increase the page size</span> to reduce the number of TLB cache misses.

• <span class="mark">Disable hyperthreading</span> to get more control over the concurrency execution of the processes.

• <span class="mark">Use the CRTP</span> to reduce the number of virtual functions.

• Remove runtime decisions by using <span class="mark">templated data structures</span>.

• <span class="mark">Pre-allocate</span> data structures to avoid any allocation on the critical path.

• Send fake orders to <span class="mark">keep caches hot</span> and allow an order to go out at the last moment.

Summary

In any trading system, the number of orders is way lower than the amount of market data received. The critical path from getting market data to sending an order is exercised very infrequently. The cache will be overtaken by non-critical path data and instructions. That's why it is very important to run a dummy path to send orders through the entire system

to keep the data cache and instruction cache primed. This will also keep the branch predictors hot.

The main idea of all these optimizations is to reduce the number of costly operations. Removing function calls, using lock-free data structures, and reducing the number of context switches are a part of this strategy.

Additionally, any decision taken at runtime is costly. That's why templated functions

and inlining will be part of the common code in any HFT system. The most costly operations are those involving networking communications. Using an end-to-end kernel bypass such as Solarflare optimizes the network latency within the trading system. By using these optimizations, this company could achieve 20 microseconds for the tick-to- trade. The latency distribution is very important to measure. We need to be sure that 20 microseconds is the latency upper bound. We should never consider the average values because it is difficult to assess high latency with this value.

In HFTs, some strategies are very profitable when a lot of trades occur. If most of the time a trading system works as expected, there is no guarantee that the system will always perform well. When a trading system receives a lot of data, if it is not built correctly, the maximum latency can be 10 times more than the average. We should keep in mind that any optimization is not guaranteed to be faster if we have not measured it ourselves in production.
