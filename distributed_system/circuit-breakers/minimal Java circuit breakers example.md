Here is a **minimal Java circuit breaker implementation** (no frameworks, ~60 lines) so you can clearly see the core idea.

This example protects a call to a **remote service**.

---

# Minimal Java Circuit Breaker Example

```java
import java.util.concurrent.atomic.AtomicInteger;

public class CircuitBreaker {

    enum State {
        CLOSED, OPEN, HALF_OPEN
    }

    private State state = State.CLOSED;

    private final int failureThreshold = 3;
    private final long resetTimeoutMs = 5000;

    private AtomicInteger failureCount = new AtomicInteger(0);
    private long lastFailureTime = 0;

    public synchronized String call(RemoteService service) {

        // If OPEN, check if we should allow retry
        if (state == State.OPEN) {
            if (System.currentTimeMillis() - lastFailureTime > resetTimeoutMs) {
                state = State.HALF_OPEN;
            } else {
                throw new RuntimeException("Circuit OPEN — fast fail");
            }
        }

        try {
            String result = service.call();

            // success → reset breaker
            failureCount.set(0);
            state = State.CLOSED;

            return result;

        } catch (Exception e) {

            int failures = failureCount.incrementAndGet();
            lastFailureTime = System.currentTimeMillis();

            if (failures >= failureThreshold) {
                state = State.OPEN;
                System.out.println("Circuit breaker OPEN");
            }

            throw new RuntimeException("Service call failed");
        }
    }
}
```

---

# Example Remote Service

```java
import java.util.Random;

public class RemoteService {

    Random rand = new Random();

    public String call() {

        if (rand.nextInt(3) != 0) {
            throw new RuntimeException("Remote failure");
        }

        return "Success";
    }
}
```

---

# Example Usage

```java
public class App {

    public static void main(String[] args) throws Exception {

        CircuitBreaker cb = new CircuitBreaker();
        RemoteService service = new RemoteService();

        for (int i = 0; i < 20; i++) {

            try {
                String res = cb.call(service);
                System.out.println(res);

            } catch (Exception e) {
                System.out.println(e.getMessage());
            }

            Thread.sleep(1000);
        }
    }
}
```

---

# Runtime Behavior

Example output:

```
Service call failed
Service call failed
Circuit breaker OPEN
Circuit OPEN — fast fail
Circuit OPEN — fast fail
(wait 5s)
Success
Success
```

Flow:

```
CLOSED
  │
  │ failures >= threshold
  ▼
OPEN
  │
  │ after timeout
  ▼
HALF_OPEN
  │
  ├ success → CLOSED
  └ failure → OPEN
```

---

# What real production breakers add

Real systems (like in **microservices**) add more features:

* rolling failure window
* latency tracking
* concurrent request limits
* fallback responses
* metrics & monitoring

Popular libraries:

* Resilience4j
* Netflix Hystrix
* Spring Cloud Circuit Breaker

---

# What a real microservice call looks like

```java
CircuitBreaker breaker = registry.circuitBreaker("payment");

Supplier<String> supplier =
    CircuitBreaker.decorateSupplier(breaker, paymentService::charge);

String result = Try.ofSupplier(supplier)
                   .recover(e -> "fallback-payment")
                   .get();
```

---

✅ **Key insight**

Circuit breakers are **not about retrying** — they are about **protecting the system from overload when something downstream is broken.**

---

If you'd like, I can also show something **very interesting for senior engineers**:

**How circuit breakers are implemented inside high-performance systems (LMAX / trading systems) where latency is microseconds and you cannot afford locks or timeouts.**
The design is quite different and very elegant.
