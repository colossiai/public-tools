Exchange 架构

Api -\> mq -\> Risk -\> mq -\> match

Api 无状态，很轻量，可水平扩展

risk按用户分片（包含用户所有account, position, open orders来做校验），也可水平扩展

match 按产品分片（order book 按产品聚合）

这样就有很强扩展能力

持久化

Mq 定期持久化 snapshot+offset (处理 crash recovery)

专门处理重启恢复，其他内存操作
