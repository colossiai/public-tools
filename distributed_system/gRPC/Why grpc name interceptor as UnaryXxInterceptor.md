# #Why grpc name interceptor as UnaryXxInterceptor

In gRPC, `UnaryXxxInterceptor` means the interceptor is for a **unary RPC**.

A **unary RPC** is the normal request-response style call:

```text
client -> one request
server -> one response
```

Example:

```proto
rpc GetUser(GetUserRequest) returns (GetUserResponse);
```

So in Go you see names like:

```go id="x8ly2s"
grpc.UnaryServerInterceptor
grpc.UnaryClientInterceptor
```

because they intercept unary calls only.

gRPC has multiple RPC types:

| RPC Type                | Meaning                      |
| ----------------------- | ---------------------------- |
| Unary                   | 1 request → 1 response       |
| Server streaming        | 1 request → stream responses |
| Client streaming        | stream requests → 1 response |
| Bidirectional streaming | stream ↔ stream              |

Therefore gRPC separates interceptors into:

```go id="h7x41q"
grpc.UnaryServerInterceptor
grpc.StreamServerInterceptor
```

* `Unary...` → intercept normal RPC calls
* `Stream...` → intercept streaming RPC calls

Example unary interceptor:

```go id="ag20cu"
func LoggingInterceptor(
    ctx context.Context,
    req any,
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (resp any, err error) {

    log.Println(info.FullMethod)

    return handler(ctx, req)
}
```

This wraps a single request/response execution lifecycle.

For streaming RPCs, the API shape is different because the interceptor manages a stream object instead of one request and one response.


# #Difference between UnaryServerInterceptor and UnaryClientInterceptor

In gRPC Go, both `UnaryServerInterceptor` and `UnaryClientInterceptor` are middleware hooks for **unary RPCs** (single request → single response), but they run on different sides of the connection.

---

# UnaryServerInterceptor

Runs on the **server side**.

It intercepts incoming RPC requests before the actual handler executes.

## Signature

```go
type UnaryServerInterceptor func(
    ctx context.Context,
    req any,
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (resp any, err error)
```

## Flow

```text
Client
  ↓
Interceptor(s)
  ↓
Actual gRPC handler
  ↓
Response
```

## Common Uses

* Authentication / authorization
* Request logging
* Metrics
* Panic recovery
* Validation
* Rate limiting
* Tracing

## Example

```go
func LoggingInterceptor(
    ctx context.Context,
    req any,
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (any, error) {

    log.Println("before:", info.FullMethod)

    resp, err := handler(ctx, req)

    log.Println("after:", err)

    return resp, err
}
```

Register:

```go
grpc.NewServer(
    grpc.UnaryInterceptor(LoggingInterceptor),
)
```

---

# UnaryClientInterceptor

Runs on the **client side**.

It intercepts outgoing RPC calls before they are sent to the server.

## Signature

```go
type UnaryClientInterceptor func(
    ctx context.Context,
    method string,
    req, reply any,
    cc *grpc.ClientConn,
    invoker grpc.UnaryInvoker,
    opts ...grpc.CallOption,
) error
```

## Flow

```text
Client code
  ↓
Interceptor(s)
  ↓
Network call
  ↓
Server
```

## Common Uses

* Add auth tokens
* Retry logic
* Timeout injection
* Request logging
* Metrics
* Distributed tracing

## Example

```go
func AuthInterceptor(
    ctx context.Context,
    method string,
    req, reply any,
    cc *grpc.ClientConn,
    invoker grpc.UnaryInvoker,
    opts ...grpc.CallOption,
) error {

    ctx = metadata.AppendToOutgoingContext(
        ctx,
        "authorization",
        "Bearer token",
    )

    return invoker(ctx, method, req, reply, cc, opts...)
}
```

Register:

```go
conn, err := grpc.Dial(
    addr,
    grpc.WithUnaryInterceptor(AuthInterceptor),
)
```

---

# Core Concept Difference

| Aspect           | UnaryServerInterceptor | UnaryClientInterceptor        |
| ---------------- | ---------------------- | ----------------------------- |
| Runs on          | Server                 | Client                        |
| Intercepts       | Incoming requests      | Outgoing requests             |
| Main callback    | `handler`              | `invoker`                     |
| Purpose          | Protect/service logic  | Control outbound RPC behavior |
| Has method info  | `info.FullMethod`      | `method`                      |
| Usually used for | auth, validation       | retry, token injection        |

---

# `handler` vs `invoker`

This is the conceptual key.

## Server

```go
resp, err := handler(ctx, req)
```

`handler` means:

> “Continue executing the actual RPC implementation.”

Equivalent to:

```go
svc.MyRPC(ctx, req)
```

---

## Client

```go
err := invoker(ctx, method, req, reply, cc, opts...)
```

`invoker` means:

> “Actually send the RPC request to server.”

Equivalent to:

```go
client.MyRPC(ctx, req)
```

---

# Interceptor Chain

Both support chaining.

Example server chain:

```go
grpc.ChainUnaryInterceptor(
    RecoveryInterceptor,
    AuthInterceptor,
    LoggingInterceptor,
)
```

Execution order:

```text
Recovery
  → Auth
    → Logging
      → Handler
```

Then unwind back outward.

---

# Streaming Equivalent

Unary interceptors only work for unary RPCs.

Streaming versions:

| Unary                  | Streaming               |
| ---------------------- | ----------------------- |
| UnaryServerInterceptor | StreamServerInterceptor |
| UnaryClientInterceptor | StreamClientInterceptor |

Used for:

* server streaming
* client streaming
* bidirectional streaming

---

# Mental Model

Think of them like HTTP middleware:

| HTTP                     | gRPC                   |
| ------------------------ | ---------------------- |
| Gin middleware           | UnaryServerInterceptor |
| HTTP client RoundTripper | UnaryClientInterceptor |

That analogy is usually accurate enough for architecture discussions.
