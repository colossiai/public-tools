**\## O(1) orderbook, Use big array instead of hash-table to represent bid/ask ladder**

J: Quick question: does anyone here know of a complete O(1) orderbook for all core operations. i.e., placement, insertion, cancelation and modification?

**=====**

J, \[Mar 23, 2024 at 11:48:44\]:

It is being built now. I invented a new data management trie which allows

For highly bounded search spaces for insertions using mappings on the EVM. I was curious if it was a first or not.

O(1) worst-case algorithmic performance at the validator layer, but actually 1/log(n) gas complexity. Weird yes, but: cold to warm to memory storage accesses as n increases.

**===**

Vachagan Balayan, \[Mar 23, 2024 at 18:34:31\]:

O(1) yes possible but with conditions

you cant allow arbitrary random precision for prices

just like bitmex

if you say force a rule that minimum price leg must differy by 1\$ for example

or 0.5\$

then you can use an array straight up

in the orderbooks instead of a tree

allocate a large array for "hot" part of the orderbook and use tree for cold orderbook (e.g. orders that are placed super far like buy btc at 1\$ or sell btc at 1b\$)...

there is no perfect solution, there are just

traeoffs

**======**

Hello, can anyone help with this issue?

Vachagan Balayan, \[Mar 25, 2024 at 18:35:10\]:

if this issue boils down to a memory leak then its going to be easy to fix

make some memory dumps, replay all those prod events to the point where you are about to run out of memory

you ahve flags for that in jvm which will automatically dump heap before getting killed

once you have the heap dump use your favourite memory analyser to see what is holding those referencees

chances are you did something wrong, but if its in the library you can fix and contribute back to open source

i can recommend this little tool jxray

it will most likely report exactly what you need without much noise

but \#1 thing you should do is enable heap dump on out of memory

aquire the heap dump and maybe even we can help in the group, otherwise its a guess work

i never saw memory leaks when i worked with exchangecore...

normally the memory should grow to some point and then stop, or grow very slowly... in my case when we deployed we allocated huge rum so that we dont even get GC for a week

during weekend we redeployed anyway so that jvm was never actually doing any gc at all.

**\## fixed point arithmetic**

JH, \[Apr 26, 2024 at 16:24:35 (Apr 26, 2024 at 16:24:39)\]:

So they just scale up the decimal to interger?

Like solidity?

Vachagan Balayan, \[Apr 26, 2024 at 16:25:21\]:

there are many ways to do it

i dont know what solidity does

but you should search fixed point arithmetic

and look the classes in the project that test it

JH, \[Apr 26, 2024 at 16:32:15\]:

Big decimal in java should be not preferred ?

Due to performance

Vachagan Balayan, \[Apr 26, 2024 at 16:33:06\]:

no

1\. its an extra allocation

2\. its immutable (which means a lot more of allocations)

3\. its not using a single field, so it wont fit in a cache line

in exchange operations that you do 99% of the time are

addition, subtraction

(mul/div are only needed for inaccurate things outside of core, like moving averages, different indicators etc)

those operations for int and long are faster than float and double

you straight up cant use floating points because of their inaccuracy

so what you can do is be smart

\`use one byte to storing where the decimal point is for the number\`

\`and one long to store the full number itself\`

when you to arithmetic operations all you need is to make sure the decimal point byte is the same, or you adjust the number and make them the same

so you can be faster than primitive float and double

and you can have percision while doing so

assuming you only care about addition,subtraction, (even multiplication)

JH, \[Apr 26, 2024 at 16:53:21\]:

Let me check this

Thx for the info

**\## Use binary message format in websocket (SBE, Cap'n Proto, Flatbuffers)**

PK, \[Apr 26, 2024 at 17:26:25\]:

Anyone have good introduction resource on low latency websocket?

Rostyslav, \[Apr 26, 2024 at 19:59:11\]:

Websocket is protocol which is already low level. To build low latency with websocket the main idea is to not do add the overhead to the websocket. That's it

Vachagan Balayan, \[Apr 26, 2024 at 20:42:05 (Apr 26, 2024 at 20:43:02)\]:

use binary message formats that literally dont have serialization/deserialization phase

SBE, CapnPRoto, Flatbuffers or if you are insane implement yours )

# Summary

\# Summary

This document contains a chat discussion about building high-performance orderbooks and exchange systems. Key topics include:

\## O(1) Orderbook Operations

\- Achieving O(1) performance for placement, insertion, cancellation, and modification requires constraints

\- Using a \*\*large array instead of hash tables\*\* works well when prices have minimum increments (e.g., \$0.50 or \$1.00 steps)

\- Hybrid approach: allocate a large array for the "hot" (actively traded) part of the orderbook and use a tree for the "cold" part (extreme prices)

\- Trade-offs exist; there's no perfect solution

\## Memory Management

\- Memory leaks can be debugged by enabling heap dumps on out-of-memory errors

\- Tools like jxray help analyze heap dumps to identify problematic references

\- Proper memory allocation strategies can minimize garbage collection

\## Fixed-Point Arithmetic

\- Avoid using \`BigDecimal\` in Java due to performance concerns (extra allocations, immutability overhead, cache line misses)

\- For exchange operations (addition, subtraction), use fixed-point arithmetic instead

\- Store the decimal point position in one byte and the full number in a long

\- This approach is faster than floating-point while maintaining precision

\## Low-Latency Websocket Communication

\- Use binary message formats like \*\*SBE, Cap'n Proto, or Flatbuffers\*\* to eliminate serialization/deserialization overhead

\- Avoid adding unnecessary layers on top of the websocket protocol itself
