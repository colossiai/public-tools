# What is HTTP OPTIONS request?

An **HTTP OPTIONS request** is a method used to ask a server **what communication options are available** for a given URL or resource.

Think of it as:

> “Hey server, what am I allowed to do here?”

---

## What OPTIONS is used for

### 1. Discover allowed HTTP methods

The server responds with which methods are supported (GET, POST, PUT, etc.).

Example response header:

```http
Allow: GET, POST, PUT, DELETE, OPTIONS
```

---

### 2. CORS preflight requests (most common in practice)

Browsers automatically send an **OPTIONS request before certain cross-origin requests** to check if they are allowed.

This happens when:

* Method is not GET/POST
* Custom headers are used
* `Content-Type` is not simple (e.g. `application/json`)
* Credentials are included

Example preflight request:

```http
OPTIONS /api/user HTTP/1.1
Origin: https://example.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Authorization
```

Expected server response:

```http
Access-Control-Allow-Origin: https://example.com
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
Access-Control-Allow-Headers: Authorization
Access-Control-Allow-Credentials: true
```

If this **fails**, the browser blocks the real request.

---

### 3. No request body, no business logic

* OPTIONS **should not modify server state**
* Usually returns **200** or **204**
* Often handled entirely by middleware

---

## Why it matters (especially for APIs)

* Required for **browser-based clients**
* Essential for **CORS**
* Misconfigured OPTIONS handling = frontend requests fail even though backend works

This is why most frameworks (including **Gin**) recommend handling OPTIONS globally via middleware.

---

## OPTIONS in Gin (best practice)

Instead of registering many routes, you typically do:

```go
func CORSMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS")
		c.Header("Access-Control-Allow-Headers", "*")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	}
}
```

Then:

```go
r.Use(CORSMiddleware())
```

---

## Quick summary

| Aspect         | OPTIONS                      |
| -------------- | ---------------------------- |
| Purpose        | Discover server capabilities |
| Common use     | CORS preflight               |
| Has body?      | No                           |
| Changes data?  | No                           |
| Typical status | 200 / 204                    |
| Browser sent?  | Automatically                |

---
