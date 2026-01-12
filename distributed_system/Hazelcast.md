# How to use hazelcast 

Hazelcast is an **in-memory data platform** commonly used for **distributed caching, shared state, pub/sub, and simple distributed data structures**. I’ll explain it from **what it is → how it works → how to use it**, with **practical Java examples**, and briefly mention **Go usage** since you often work with Go.

---

## 1. What Hazelcast is (mental model)

Think of Hazelcast as:

* A **distributed in-memory key–value store**
* With **automatic clustering**
* Providing **data structures**, not just a cache

It’s often used for:

* Distributed cache (like Redis, but embedded)
* Session sharing
* Distributed locks
* Pub/Sub messaging
* Simple distributed coordination

---

## 2. Core concepts

### Hazelcast cluster

* A **cluster** = multiple Hazelcast members (nodes)
* Members **auto-discover** each other
* Data is **partitioned + replicated**

### Distributed data structures

Hazelcast exposes Java-like structures, but distributed:

| Hazelcast Type | Similar to        |
| -------------- | ----------------- |
| `IMap<K,V>`    | ConcurrentHashMap |
| `IQueue<T>`    | BlockingQueue     |
| `ITopic<T>`    | Pub/Sub           |
| `ISet<T>`      | Set               |
| `ILock`        | Distributed lock  |

---

## 3. Basic usage (Java, embedded mode)

### Add dependency (Maven)

```xml
<dependency>
  <groupId>com.hazelcast</groupId>
  <artifactId>hazelcast</artifactId>
  <version>5.4.0</version>
</dependency>
```

---

### Start a Hazelcast member

```java
import com.hazelcast.core.Hazelcast;
import com.hazelcast.core.HazelcastInstance;

public class Server {
    public static void main(String[] args) {
        HazelcastInstance hz = Hazelcast.newHazelcastInstance();
        System.out.println("Hazelcast started");
    }
}
```

Run this **on multiple machines or processes** → they form a cluster automatically.

---

### Use a distributed map (cache)

```java
import com.hazelcast.map.IMap;

HazelcastInstance hz = Hazelcast.newHazelcastInstance();
IMap<String, String> map = hz.getMap("my-cache");

map.put("user:1", "Eric");
String value = map.get("user:1");

System.out.println(value);
```

* Data is **shared across nodes**
* Thread-safe + distributed

---

## 4. Client–server mode (recommended for production)

Instead of embedding Hazelcast everywhere, you usually run:

* **Hazelcast members** (servers)
* **Hazelcast clients** (apps)

### Start a server

```bash
java -jar hazelcast-5.4.0.jar
```

---

### Java client

```java
import com.hazelcast.client.HazelcastClient;
import com.hazelcast.core.HazelcastInstance;

HazelcastInstance client = HazelcastClient.newHazelcastClient();
IMap<String, String> map = client.getMap("my-cache");
```

---

## 5. Common real-world patterns

### 5.1 Distributed cache with TTL

```java
map.put("token:abc", "user1", 5, TimeUnit.MINUTES);
```

Used for:

* Auth tokens
* Rate limiting
* Session data

---

### 5.2 Distributed lock

```java
ILock lock = hz.getLock("order-123");

lock.lock();
try {
    // critical section
} finally {
    lock.unlock();
}
```

Used for:

* Preventing double-processing
* Cross-node coordination

---

### 5.3 Pub/Sub (events)

```java
ITopic<String> topic = hz.getTopic("events");

topic.addMessageListener(msg ->
    System.out.println("Received: " + msg.getMessageObject())
);

topic.publish("order_created");
```

---

## 6. Configuration (important)

### Programmatic config

```java
Config config = new Config();
config.setClusterName("prod-cluster");

NetworkConfig net = config.getNetworkConfig();
net.getJoin().getMulticastConfig().setEnabled(false);
net.getJoin().getTcpIpConfig()
   .setEnabled(true)
   .addMember("10.0.0.1");

HazelcastInstance hz = Hazelcast.newHazelcastInstance(config);
```

Key points:

* **Disable multicast** in cloud/K8s
* Use **TCP/IP or Kubernetes discovery**

---

## 7. Hazelcast in Kubernetes

Hazelcast has native K8s discovery:

```yaml
hazelcast:
  network:
    join:
      kubernetes:
        enabled: true
        service-name: hazelcast
```

Works well for:

* Stateful services
* Distributed cache in microservices

---

## 8. Using Hazelcast from Go

Hazelcast **does NOT provide an official Go client**.

Your options:

1. **Use Hazelcast via REST** (Management Center / custom gateway)
2. **Use Redis instead** (more Go-native)
3. **Use Hazelcast only for Java services**, expose data via API

If you want a **distributed cache for Go**, better choices:

* Redis
* etcd
* DragonflyDB

---

## 9. When to use Hazelcast (vs Redis)

Use Hazelcast when:

* You are **Java-heavy**
* You want **in-process speed**
* You need **distributed locks & structures**
* You want **no external cache service**

Avoid Hazelcast when:

* Polyglot (Go, Rust, Python-heavy)
* Need persistence-first semantics
* Want simple ops (Redis easier)

---

## 10. Typical architecture

```
[ Java App ] --client--> [ Hazelcast Cluster ]
[ Java App ] --client--> [ Hazelcast Cluster ]
```

Used as:

* Cache
* Coordination layer
* Shared state

---

If you want, I can:

* Show **Hazelcast vs Redis** deep comparison
* Give a **production-ready config**
* Show **session sharing** or **rate limiting**
* Suggest a **Go-friendly alternative**

Just tell me your use case.
