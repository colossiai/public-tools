# Show Spring Boot + JUnit 5 patterns


Below are **real-world Spring Boot + JUnit 5 testing patterns**, from fastest → slowest, with **when to use each**, **common annotations**, and **example code**.
This is how most production Spring Boot teams structure tests.

---

# 1️⃣ Test Pyramid (Spring Boot Reality)

```
Controller (Web slice)     → fast, mocked
Service (unit)             → fastest
Repository (JPA slice)     → medium
Full context (@SpringBootTest) → slow, few
```

**Rule:**

> The more Spring you start, the fewer tests you should have.

---

# 2️⃣ Pure Unit Test (NO Spring)

✅ **Fastest, most important**

### When to use

* Business logic
* No Spring annotations
* Mock dependencies manually or with Mockito

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    OrderRepository repository;

    @InjectMocks
    OrderService service;

    @Test
    void createOrder_success() {
        when(repository.save(any())).thenReturn(new Order(1L));

        Order order = service.createOrder();

        assertNotNull(order.getId());
    }
}
```

### Why

* Runs in milliseconds
* No Spring context
* Best signal-to-noise ratio

---

# 3️⃣ Web Layer Test (Controller Slice)

✅ **Most common Spring test**

### When to use

* Controller request/response
* Validation
* HTTP status codes
* JSON shape

### Annotation

```java
@WebMvcTest(OrderController.class)
```

### Example

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Autowired
    MockMvc mockMvc;

    @MockBean
    OrderService orderService;

    @Test
    void createOrder_shouldReturn201() throws Exception {
        when(orderService.create()).thenReturn(new Order(1L));

        mockMvc.perform(post("/orders"))
               .andExpect(status().isCreated())
               .andExpect(jsonPath("$.id").value(1));
    }
}
```

### Key Points

* Loads **only MVC components**
* Uses `@MockBean` (Spring-managed mock)
* Very fast (~100ms)

---

# 4️⃣ JSON Serialization Test

### When to use

* Verify Jackson serialization/deserialization
* Prevent breaking API contracts

```java
@JsonTest
class OrderJsonTest {

    @Autowired
    JacksonTester<Order> json;

    @Test
    void serialize() throws Exception {
        Order order = new Order(1L);

        assertThat(json.write(order))
            .hasJsonPathNumberValue("$.id");
    }
}
```

💡 **Extremely useful for public APIs**

---

# 5️⃣ Service Layer Test (Spring Context, Limited)

### When to use

* Transaction behavior
* Spring annotations (`@Transactional`, `@Retryable`)

```java
@SpringBootTest
class OrderServiceIT {

    @Autowired
    OrderService service;

    @Test
    void createOrder_transactional() {
        service.createOrder();
    }
}
```

⚠️ Use sparingly — slower.

---

# 6️⃣ Repository Test (JPA Slice)

### When to use

* Custom queries
* Entity mapping
* Index & constraint verification

```java
@DataJpaTest
class OrderRepositoryTest {

    @Autowired
    OrderRepository repository;

    @Test
    void saveAndFind() {
        Order order = repository.save(new Order());

        assertTrue(repository.findById(order.getId()).isPresent());
    }
}
```

### Defaults

* In-memory DB (H2)
* Rollback after each test

To use real DB:

```java
@AutoConfigureTestDatabase(replace = NONE)
```

---

# 7️⃣ Full Integration Test (End-to-End)

🚨 **Slow, but necessary**

### When to use

* Security filters
* Full wiring
* Smoke tests

```java
@SpringBootTest
@AutoConfigureMockMvc
class ApplicationIT {

    @Autowired
    MockMvc mockMvc;

    @Test
    void healthCheck() throws Exception {
        mockMvc.perform(get("/actuator/health"))
               .andExpect(status().isOk());
    }
}
```

---

# 8️⃣ Testing REST with Random Port

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
class OrderApiIT {

    @Autowired
    TestRestTemplate restTemplate;

    @Test
    void getOrder() {
        ResponseEntity<Order> resp =
            restTemplate.getForEntity("/orders/1", Order.class);

        assertEquals(HttpStatus.OK, resp.getStatusCode());
    }
}
```

Use this only if:

* You need real HTTP stack
* WebSocket / filters / serialization edge cases

---

# 9️⃣ Test Configuration & Profiles

### application-test.yml

```yaml
spring:
  datasource:
    url: jdbc:h2:mem:test
```

### Activate profile

```java
@ActiveProfiles("test")
```

---

# 🔟 Common Anti-Patterns 🚫

❌ `@SpringBootTest` everywhere
❌ Testing logic in controllers
❌ Mocking repositories in integration tests
❌ Hitting real DB in unit tests

---

# 1️⃣1️⃣ Recommended Test Structure

```
src/test/java
├── unit
│   └── OrderServiceTest.java
├── web
│   └── OrderControllerTest.java
├── repository
│   └── OrderRepositoryTest.java
└── integration
    └── ApplicationIT.java
```

---

# 1️⃣2️⃣ Cheat Sheet

| Need             | Annotation                            |
| ---------------- | ------------------------------------- |
| Pure unit test   | `@ExtendWith(MockitoExtension.class)` |
| Controller test  | `@WebMvcTest`                         |
| JPA test         | `@DataJpaTest`                        |
| JSON test        | `@JsonTest`                           |
| Full context     | `@SpringBootTest`                     |
| HTTP client      | `TestRestTemplate`                    |
| Mock Spring bean | `@MockBean`                           |

---

If you want, next I can show:

* **Spring Security testing patterns**
* **Testcontainers + Spring Boot**
* **Fast CI test strategy**
* **Contract testing (OpenAPI / Pact)**

Just tell me which one 👌
