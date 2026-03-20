# #Show a minimal spring-cloud service discovery sample

Absolutely! Let’s do a **minimal Spring Cloud service discovery example** using **Eureka** (the most common Spring Cloud discovery server). I’ll show **Service Registry + two services** (Service A and Service B).

---

## **1️⃣ Set up Eureka Server**

**`pom.xml`** (Spring Boot + Eureka Server)

```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-netflix-eureka-server</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
</dependencies>
```

**`application.yml`**

```yaml
server:
  port: 8761

eureka:
  client:
    register-with-eureka: false
    fetch-registry: false
```

**`EurekaServerApplication.java`**

```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.netflix.eureka.server.EnableEurekaServer;

@SpringBootApplication
@EnableEurekaServer
public class EurekaServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(EurekaServerApplication.class, args);
    }
}
```

* Run this app → Eureka dashboard available at `http://localhost:8761`

---

## **2️⃣ Service B – the provider**

**`pom.xml`** (Spring Boot + Eureka Client)

```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
</dependencies>
```

**`application.yml`**

```yaml
spring:
  application:
    name: service-b
server:
  port: 8081

eureka:
  client:
    service-url:
      defaultZone: http://localhost:8761/eureka/
```

**`ServiceBController.java`**

```java
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ServiceBController {
    @GetMapping("/hello")
    public String hello() {
        return "Hello from Service B!";
    }
}
```

* Service B registers itself to Eureka automatically.
* Check Eureka dashboard → you should see **service-b**.

---

## **3️⃣ Service A – the consumer**

**`pom.xml`** (Spring Boot + Eureka Client + Ribbon for client-side load balancing)

```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
</dependencies>
```

**`application.yml`**

```yaml
spring:
  application:
    name: service-a
server:
  port: 8080

eureka:
  client:
    service-url:
      defaultZone: http://localhost:8761/eureka/
```

**`ServiceAController.java`**

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;
import java.util.List;

@RestController
public class ServiceAController {

    @Autowired
    private DiscoveryClient discoveryClient;

    private RestTemplate restTemplate = new RestTemplate();

    @GetMapping("/call-b")
    public String callServiceB() {
        // Discover instances of service-b
        List<org.springframework.cloud.client.ServiceInstance> instances =
                discoveryClient.getInstances("service-b");

        if (instances == null || instances.isEmpty()) {
            return "No instances of Service B found";
        }

        // Pick the first instance
        String url = instances.get(0).getUri() + "/hello";
        return restTemplate.getForObject(url, String.class);
    }
}
```

---

### **4️⃣ Run the demo**

1. Start **Eureka Server** (`port 8761`)
2. Start **Service B** (`port 8081`) → registers itself
3. Start **Service A** (`port 8080`)
4. Visit `http://localhost:8080/call-b`

Output:

```
Hello from Service B!
```

✅ **What this demonstrates:**

* Service B registers itself with Eureka → no hardcoding of IP/port needed.
* Service A discovers Service B dynamically via Eureka → handles scaling/moving instances.
* Minimal Spring Cloud service discovery setup.

---

If you want, I can also show a **version using Spring Cloud LoadBalancer** so that Service A **calls service-b automatically without manually picking instances** — this is closer to how real microservices talk in production.

Do you want me to show that version?
