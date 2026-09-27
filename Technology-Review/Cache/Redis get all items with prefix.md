# Q: Redis best way to collect data with key prefix

In Redis, collecting data with a specific key prefix is a common pattern. Redis doesn't natively support prefix-based operations, but there are efficient ways to collect data with a key prefix. Below are the best approaches depending on your use case:

### **1. Use the SCAN Command (Recommended for Large Datasets)**

The SCAN command is a cursor-based iterator that allows you to retrieve keys matching a pattern incrementally. It is more efficient than KEYS because it doesn’t block Redis and works well with large datasets.

#### **How to Use SCAN with a Key Prefix**

SCAN cursor MATCH prefix:\* COUNT 100

- **cursor**: Starts at 0 initially; Redis returns a new cursor for subsequent calls.

- **MATCH prefix:\***: Filters keys with the specified prefix.

- **COUNT 100**: Specifies how many keys to return in a single iteration (not guaranteed—used as a hint).

#### **Example in Python with redis-py:**

import redis

\# Connect to Redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

\# Initialize variables

prefix = "user:"

cursor = 0

keys = \[\]

\# SCAN loop

while True:

cursor, batch_keys = r.scan(cursor=cursor, match=f"{prefix}\*", count=100)

keys.extend(batch_keys)

if cursor == 0: \# Cursor 0 means the iteration is complete

break

print(f"Keys with prefix '{prefix}': {keys}")

#### **Advantages of SCAN:**

- Non-blocking and suitable for production environments.

- Allows retrieving keys in chunks to avoid memory issues.

### **2. Use the KEYS Command (For Small Datasets)**

The KEYS command can be used to get all keys matching a pattern. However, **it is not recommended for large datasets** because it blocks Redis and can degrade performance.

#### **How to Use KEYS with a Key Prefix**

KEYS prefix:\*

#### **Example in Python:**

keys = r.keys("user:\*")

print(keys)

#### **Limitations of KEYS:**

- Blocks Redis during execution (not ideal for production).

- May cause performance issues in large datasets.

### **3. Store Keys with Prefix in a Redis Set (Manual Indexing)**

A more proactive approach is to store all keys with a specific prefix in a Redis Set. This allows you to retrieve them without scanning the entire database.

#### **How It Works**

1.  Whenever you add a key with a prefix, also add its name to a set.

2.  Use the set to retrieve all keys with the prefix.

#### **Example:**

\# Add a key with a prefix

r.set("user:123", "John")

r.sadd("users", "user:123")

\# Get all keys with the prefix

keys = r.smembers("users")

print(keys)

#### **Advantages of Manual Indexing:**

- Extremely fast, as SMEMBERS is an O(N) operation within the set.

- Avoids scanning the entire keyspace.

#### **Limitations:**

- Requires additional maintenance (e.g., removing keys from the set when they are deleted).

### **4. Use Redis Streams or Hashes for Structured Data**

If you are frequently working with prefixed keys, consider using **Redis Streams** or **Hashes** as an alternative to plain keys.

#### **Redis Hash Example:**

\# Store data in a hash

r.hset("user:123", mapping={"name": "John", "age": 30})

\# Retrieve all fields

user_data = r.hgetall("user:123")

print(user_data)

#### **Redis Streams Example:**

\# Add an entry to a stream

r.xadd("user_stream", {"id": "123", "name": "John", "age": 30})

\# Read entries from the stream

entries = r.xrange("user_stream")

print(entries)

- **Hashes and Streams** allow you to group related data under a single key, potentially reducing the need for key prefixes.

### **Comparison Table**

| **Method** | **Use Case** | **Pros** | **Cons** |
|----|----|----|----|
| SCAN | Large datasets, non-blocking | Efficient and incremental | Slightly more complex to implement |
| KEYS | Small datasets only | Simple to use | Blocks Redis and affects performance on large datasets |
| <span class="mark">Manual Indexing</span> | <span class="mark">Frequent access to prefixed keys</span> | <span class="mark">Fast lookups, avoids full database scans</span> | <span class="mark">Requires extra maintenance logic</span> |
| Hashes or Streams | When working with structured or grouped data | Reduces key clutter, easier to manage | May require redesigning your application logic |

### **Recommendation**

- Use **SCAN** for general-purpose prefix-based collection.

- Use **manual indexing** if you frequently access keys with the same prefix.

- Consider **hashes or streams** for structured data to avoid the need for prefixes entirely.
