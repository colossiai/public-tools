# #what will happen with the code?

```
func AuthHelper(c *gin.Context) {
	if invalid {
		c.AbortWithStatusJSON(401, gin.H{
			"error": "unauthorized",
		})

		// IMPORTANT
		return
	}
}

func Handler(c *gin.Context) {
	AuthHelper(c)

	// This still executes unless:
	// 1. AuthHelper returns and
	// 2. Handler checks/returns
	fmt.Println("still running")

	c.JSON(200, gin.H{
		"ok": true,
	})
}

it will send both 401 and 200 to clients?
```

---


No, the client will not receive two separate HTTP responses.

In Gin, HTTP headers/status can only be written once. What happens is:

1. `AbortWithStatusJSON(401, ...)`

   * immediately writes:

     * status = `401`
     * JSON body = `{"error":"unauthorized"}`
2. execution continues in `Handler`
3. `c.JSON(200, ...)` tries to write another response

At that point, Gin/Go will usually log something like:

```text
[GIN-debug] [WARNING] Headers were already written. Wanted to override status code 401 with 200
```

The client typically receives only the first response:

```http
HTTP/1.1 401 Unauthorized

{"error":"unauthorized"}
```

The later `c.JSON(200, ...)` is ignored or partially fails because the response has already started.

So this code is buggy:

```go id="bad-example"
func Handler(c *gin.Context) {
	AuthHelper(c)

	// still runs
	fmt.Println("still running")

	// tries to write second response
	c.JSON(200, gin.H{
		"ok": true,
	})
}
```

Correct pattern:

```go id="good-example"
func Handler(c *gin.Context) {
	AuthHelper(c)

	if c.IsAborted() {
		return
	}

	c.JSON(200, gin.H{
		"ok": true,
	})
}
```

Or better:

```go id="best-pattern"
func AuthHelper(c *gin.Context) bool {
	if invalid {
		c.AbortWithStatusJSON(401, gin.H{
			"error": "unauthorized",
		})
		return false
	}
	return true
}

func Handler(c *gin.Context) {
	if !AuthHelper(c) {
		return
	}

	c.JSON(200, gin.H{
		"ok": true,
	})
}
```

`c.IsAborted()` checks whether `Abort()` was called on the context.
