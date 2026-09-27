АЛ Р, \[Jul 10, 2024 at 08:51:35\]:

I am new - joined to see if anybody got lmax exchange core to work in real project - and what exactly it took in terms of efforts?

Vachagan Balayan, \[Jul 10, 2024 at 11:37:52\]:

i used it twice for two different crypto exchanges

effort significantly depends on what kinda team you work with

if they know what this is, how to work with it you will get a working POC within 2 months

if they dont know much about why disruptor is designed the way its designed its going to be uncharted waters

i hired my team myself, so i didnt have that problem

Everest - Madrid / España, \[Jul 11, 2024 at 11:53:50\]:

We are testing a highly customized version of it for a few weeks

АЛ Р, \[Jul 11, 2024 at 13:02:47\]:

how long did it take your team to build up missing GUI etc ?

Shi fu, \[Jul 11, 2024 at 13:26:43\]:

We already had it

We developed some crypto exchanges before

АЛ Р, \[Jul 11, 2024 at 13:27:13\]:

Thanks

So - with LMAX — the orderbook is one thread , and bids and asks are size-of-order-based sorted lists. So 3 threads minimum in the core. Right ?

Vachagan Balayan, \[Jul 12, 2024 at 05:27:16\]:

yes but 3 is too few

if you are doing few orders per second its fine

first of all its not threads you should think of them as cores

if you are giving more than 1 worker to each core you are doing something wrong

if you get to have more TPS than single core instance can handle

you can scale orderbooks per pair

one pair is always one core

you can have more pairs per core but not vice versa

Everest - Madrid / España, \[Jul 12, 2024 at 16:47:03\]:

@AlexTender1 What are your requirements?

Frank, \[Jul 14, 2024 at 22:16:25\]:

Can anyone please advise how do I start working on low level programming...my background is on the enterprise applications using Java Python and AWS for now

Vachagan Balayan, \[Jul 15, 2024 at 00:15:12\]:

you are on the right path

Vachagan Balayan, \[Jul 15, 2024 at 00:31:53\]:

**<span class="mark">start with disruptor, how it works</span>**

**<span class="mark">why its so much faster than other queues</span>**

**<span class="mark">then i'd look into aeron media driver</span>**

**<span class="mark">and chronicle queue</span>**

**<span class="mark">just use them a bit to be familiar, understand how they work</span>**

**<span class="mark">and you are set</span>**

the rest is project specific knowledge

hardware low level fundamentals are universal, and apply to any lang

its just you're unlikely to see disruptor implemented in javascript

Rostyslav, \[Jul 15, 2024 at 00:39:16\]:

I would recommend chronicle stack first. Before Aeron

Chronicle has nice abstraction layer. When Aeron does not (Almost). But has more compoennts

Vachagan Balayan, \[Jul 15, 2024 at 00:41:09\]:

maybe it has a bit too much of an abstraction layers but thats not the point about learning how persistent queue works

why its very useful to make much simpler systems

often when you dont need to tryhard for maximum possible performance (to witch cq is very close) its much simpler to design systems where you can just think of each queue as

something that wont loose a message, cant run out of capacity (cos you are limited by storage not ring buffer size) so you can have multiple true microservices which use queues

and if one of them goes down the others just keep pumping messges until it comes up and catches up, no messages lost, simpler design often

knowing when to use which imo is important

i seen many abused cases of disruptor (treating it like a regular queue)

**<span class="mark">i'd say last point if you really want to dive into low level is serialization/rpc options</span>**

**<span class="mark">i like formats that avoid coversion between bytes to objects entirely</span>**

**<span class="mark">things like SBE, capnp, faltc</span>**

over things like protobuf

but for 99% of systems where you do not care about performance/zerogc (like things that can scale forever horizontally) protobuf/grpc is amazing

АЛ Р:

First of all learn the math of lock-free algorithms and structures. They have implementations in java libs

Next understand why disruptor is important.

Then learn how the real big data is operating. And don't just use BS standard code. Instead learn why concurrent store of data in memory mapped files will save and preserve real form. losses. Learn why memory pool is efficient in java using out of heap memory.

All those things should be described in some books like optimized or efficient java , if you find one.

Also why and how at least 2 instances of backend should run in different datacenters in high availability mode. So when the power of one dayacenter goes down the second instance takes over without loss of data and transactions

Rostyslav:

Also memory layout, cache line, alignment & paddings

Everest:

With skilled engineers working full-time, it will take approximately six months to develop a fully functional MVP (Minimum Viable Product) for a crypto exchange. This timeline includes implementing KYC (Know Your Customer), AML (Anti-Money Laundering), and compliance with regulatory requirements. It's important to note that opening a commercial bank account for a crypto exchange can be challenging. Therefore, it is advisable to begin legal planning before starting development

Vachagan Balayan:

arb is dead

Muhammed:

No who said

Vachagan Balayan:

if you are competing on speed its too late

# Summary

\# Summary

This is a chat transcript discussing \*\*low-latency trading systems and crypto exchange development\*\* using technologies like LMAX Disruptor.

\## Key Points:

\*\*LMAX Exchange Core Implementation:\*\*

\- POC can be built in ~2 months with an experienced team familiar with Disruptor concepts

\- Requires at least 3 CPU cores minimum (one orderbook thread + bid/ask processing)

\- One trading pair per core; multiple pairs can share a core but not vice versa

\*\*Learning Path for Low-Level Programming:\*\*

1\. Understand lock-free algorithms and structures

2\. Study LMAX Disruptor and why it's performant

3\. Learn Chronicle Queue, Aeron Media Driver

4\. Study serialization formats (SBE, Cap'n Proto, Flatbuffers over Protobuf for performance)

5\. Understand memory layout, cache lines, alignment, and padding

\*\*System Design Recommendations:\*\*

\- Use memory-mapped files for data persistence

\- Consider out-of-heap memory pools in Java

\- Implement high-availability across multiple datacenters

\- Avoid message loss through persistent queues

\*\*Crypto Exchange Development:\*\*

\- Full MVP takes ~6 months with skilled engineers

\- Must include KYC/AML compliance and regulatory requirements

\- Banking relationships are challenging to establish

\*\*Performance Note:\*\*

\- Speed-based arbitrage is increasingly difficult to compete on in modern markets
