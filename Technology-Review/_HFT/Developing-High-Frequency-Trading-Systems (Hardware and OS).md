Mentioned concepts:

\# efficient data structure to model the order book (Page33)

Constant look-up, fast quantity update:

Iteration in order of prices:

Retrieving best bid and ask in constant time:

Organize order identifiers to order information in a huge associative array (for C++,

it could be a std::unordered map or std::vector).

• The order metadata includes references to the order book and price-level it belongs to, therefore, after checking up the order, the order book and price-level data structures are only a single dereference away. When using an Order Execute or Order Reduce action, having a reference to the price allows for an O(1) decrease. You may preserve pointers to the next and previous orders in the queue if you wish to keep track of time priority as well.

• The Critical Components of a Trading System

Because the majority of changes occur near the inside of the book, employing a vector for each book's price levels will result in the quickest average price lookup. Because the desired price is usually just a few levels from the interior and a

linear search is simpler on the branch predictor, optimizer, and cache, searching linearly from the end of the vector is, on average, quicker than a binary search. Of course, pathological orders can exist outside of the book, and an attacker might, theoretically, transmit a large number of updates at the end of the book to slow down your implementation. In reality, however, this usually yields a cache-friendly, almost O(1) implementation for insert, lookup, update, and delete (with an O(N) memcpy in the worst-case scenario).

This has O(1) best-case behavior for insertion, lookup, deletion, and update, with extremely low constants. Unfortunately, because of the cache, TLB, and compiler- friendliness, you may achieve O(N) worst-case behavior with a low probability and still have extremely excellent constants. It's also very quick, almost ideally so, when it comes to Best Bid and Offer (BBO) updates, which is what you're normally after

\# non-uniform memory access (NUMA)

In NUMA architectures, there are memory controllers, with memory being physically connected to a particular socket. The main benefit of a NUMA architecture over UMA

is that a NUMA system can scale more quickly to a more significant number of CPUs, because interconnecting NUMA nodes is less complex than connecting several CPUs to a single pool of system memory.

\# translation lookaside buffer (TLB) (page 70)

A special- purpose high-speed cache in the CPU called the translation lookaside buffer (TLB) is used for any practical page tables.

Paging can hurt the performance of a process. When there is a cache miss in the TLB, the OS must load data from elsewhere in memory

\# System calls

Modern versions of Linux provide the virtual dynamic shared object (vDSO) exporting some special kernel space functions to user space, especially those related to retrieving current system time.

\# The role of compilers (Page 73)

Loop unrolling is an example of this tradeoff.

Function inlining can replace the function call by the assembly code

Table and calculation. The compilers can help create data structures to avoid recalculation

Linking: Typical HFT systems will use static linking where possible to avoid this overhead.

\# Multicast mode

This mode is a hybrid of the previous two in that the packet is transmitted to neither a single host nor all of the hosts on the segment.

Non-essential data, such as market data feeds, is often transmitted using UDP to reduce latency and overhead.

Critical data such as orders is carried out using the TCP/IP protocol.

Today, there is a trend to use UDP for Orders (UFO), which allows us to send orders faster.

\# FAST protocol (Fix FAST - UDP, compression)

The FAST protocol is the high-speed version of the FIX protocol. Market data is transmitted from exchanges or feed handlers to market participants via the FAST protocol, which operates on top of UDP.

FAST belongs to a family of protocols developed to improve the bandwidth and the speed of communication named Simple Binary Encoding (SBE). We will now talk about protocols that are way more efficient than string-based protocols for communication.

ITCH/OUCH protocol

ITCH and OUCH are considered binary protocols. OUCH is usually over TCP, and ITCH is multicast or TCP. ITCH is mainly for market data, while OUCH is made for the orders. Nasdaq created these protocols in 2000 after a patent infringement lawsuit impacted FAST.

CME market data protocol

CME also created its SBE protocol optimized for HFT.

\# Techniques to avoid or minimize context switches (Page 117)

\* Pinning threads to CPU cores

\* Avoiding system calls that lead to pre-emption

\# Types of synchronization mechanisms (Page 119)

\* Memory barriers

A memory barrier a.k.a. memory fence or fence is used to instruct the compiler and processors to not reorder the loads and stores.

\* test-and-set

\* fetch-and-add

\* Compare-and-swap

\# Spin Lock

With lock-free data structures, a thread makes progress each time it runs, and this is effectively implemented as a spin lock. A spin lock does not block but instead repeatedly keeps checking if the lock is available. This behavior is known as busy wait.

\# SPSC (Single producer sincle consumer) and MPMC

\# Avoid virtual functions (C++)

\# Pre-allocation-based alternatives to dynamic memory allocation

\* Limit memory to stack

\* Memory pools

\# Understanding why kernel bypass is the alternative

some examples are

\* Solarflare NICs and the OpenOnload/TCPDirect/ef_vi API to support kernel bypass,

\* Mellanox NICs and Mellanox Messaging Accelerator (VMA) APIs, and

\* Chelsio adapters and WireDirect/TCP Offload Engine (TOE) APIs.

The alternative to eliminate the latencies incurred in traditional socket programming, which make it a bad fit for HFT, has two aspects:

\* spinning on a CPU core in user space and

\* zero copy of incoming and outgoing data.

\# Presenting kernel bypass latencies

UDP read/write times without kernel bypass latencies range between 1.5 to 10 microseconds,

and with kernel bypass, latencies range between 0.5 to 2 microseconds.

\# Disadvantages of memory-mapped files

\* Page faults are the biggest concern with memory-mapped files

\# Evolution from cable fiber to hollow fiber to microwave

\# valgrind, cachegrind, and callgrind
