# Real project optimization

- Cache:

> redis, local-memory-with-ttl, copy-on-write map
>
> Cache open order/position in gRPC service
>
> Keep statistics summary instead of raw data into atomic Map (boost read performance)

- Concurrent computing: grpc endpoint concurrent processing

- Batch:

> redis MGet,
>
> Mysql multi-insert

- Data compression: (no direct usage)

> ws message compression

- Lockless: atomic, CompareAndSwap

- Sharding

> Db sharding
>
> Memory sharding by user-id
>
> Minimize lock scope

- Reduce request

> Reduce IO if memory handling sufficient
>
> Reduce gRPC if memory handling sufficient

- Pooling:

> Mysql/Redis connection pooling
>
> Java Thread pooling

- Async processing

> Order event update (push)

- Database record-lock (SELECT FOR UPDATE)

> Mysql row-level lock

===========================

Key Takeaway of Refinement of amend-order api

Memory First: cache db account info, query on atomic map (update periodically and atomically)

Reduce IO: only query redis once, only call xopen grpc once

Sharding: memory synMap sharding; service instance sharding, storage sharding

===========================

- Index

> Mysql index optimization
>
> Memory index for large data structure

- Pre-fetch:

> Pre-fetch and keep config/master data in memory

- Rate-limiting

> Control request rate.

- Peak shaving and valley filling

> MQ/Kafka

- Stateless API service for vertical shading

> Order api

- Read/Write splitting

- Minimize IO

> Remove database reading, use gRPC

- 

# 

# 

# 储存

<span class="mark">异构查询db：比如设置不同索引的db给ims</span>

<span class="mark">异构查询db：ES</span>

# 

# API Log

Requirements

1 用户：Api交互中提供有效的信息

2 安全：不要泄漏系统安全信息 (内网ip，内部struct exception)

3 研发：提供context变量便于排除

内部实现：

需要区分error，哪些是io error， 哪些是sanity check(用户输入错误)

# API Error Code

建议

{

“success”: false,

“error_code”: “ERROR_INVALID_ARGUMENT”,

“details”: “field \[price\] is empty”

}

Error_code使用字符串code，是把integer code和msg的结合，且省去了查找code的含义

details是当时的环境参数，web/app可以不关注，api用户可以看到具体原因

# Golang structured error 设计

CustomError 实现 error { Error() string} 接口，那样

可以在返回error的地方，返回 CustomError

Api可以检查返回的 err 是否为 CustomError 再判断
