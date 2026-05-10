# #What is grpc-gateway's in-process call mode.

In gRPC-Gateway, **in-process call mode** means:

> The HTTP gateway and the gRPC server run inside the **same Go process**, and the gateway forwards requests to the gRPC server locally.

Instead of:

```text
Browser -> HTTP Gateway Process -> network -> gRPC Server Process
```

you get:

```text
Browser -> HTTP Gateway -> local gRPC server
                 (same process)
```

---

# The Normal grpc-gateway Architecture

Normally, grpc-gateway works like this:

```text
Client
  |
HTTP/JSON
  |
grpc-gateway
  |
gRPC over HTTP/2
  |
gRPC Server
```

The gateway translates:

* HTTP + JSON
  → into
* gRPC + Protobuf

Usually the gateway connects to the gRPC server through TCP:

```go
grpc.Dial("localhost:9090")
```

Even if both are on the same machine.

---

# What “In-Process” Means

In-process means:

* same executable
* same memory space
* same OS process

Example:

```go
go run main.go
```

Inside this one process:

* HTTP server
* grpc-gateway
* gRPC server

all run together.

---

# Typical Setup

A common production setup:

```text
+----------------------------------+
|          Single Process          |
|                                  |
|  HTTP Server (:8080)             |
|      |                           |
|      v                           |
|  grpc-gateway                    |
|      |                           |
|      v                           |
|  gRPC Server (:9090)             |
|                                  |
+----------------------------------+
```

The gateway still speaks gRPC internally.

---

# Why People Use In-Process Mode

## 1. Simpler Deployment

Only one binary:

```bash
./api-server
```

instead of:

```bash
./grpc-server
./http-gateway
```

---

## 2. Lower Latency

No external network hop.

The request stays inside the machine.

---

## 3. Easier DevOps

Only one:

* container
* process
* deployment
* monitoring target

---

## 4. Shared Infrastructure

Both can share:

* logging
* tracing
* metrics
* configs
* DB pools

---

# Important Detail:

## It STILL Uses gRPC Internally

Even in-process, grpc-gateway usually still dials the gRPC server:

```go
pb.RegisterMyServiceHandlerFromEndpoint(...)
```

with:

```go
grpc.WithTransportCredentials(insecure.NewCredentials())
```

because traffic never leaves the machine.

This is why comments often say:

> “TLS boundary is the public HTTP listener.”

Meaning:

* external HTTPS is protected
* internal localhost gRPC does not need TLS

---

# Example

```go
grpcServer := grpc.NewServer()

pb.RegisterUserServiceServer(grpcServer, &UserService{})

lis, _ := net.Listen("tcp", ":9090")
go grpcServer.Serve(lis)

mux := runtime.NewServeMux()

pb.RegisterUserServiceHandlerFromEndpoint(
    context.Background(),
    mux,
    "localhost:9090",
    []grpc.DialOption{
        grpc.WithTransportCredentials(insecure.NewCredentials()),
    },
)

http.ListenAndServe(":8080", mux)
```

This is considered an “in-process” deployment because:

* both servers are in one Go process
* even though they communicate via localhost TCP

---

# True Zero-Network In-Process Mode

There is an even tighter integration using:

```go
RegisterUserServiceHandlerServer(...)
```

instead of:

```go
RegisterUserServiceHandlerFromEndpoint(...)
```

This bypasses TCP completely.

The gateway calls the service implementation directly.

---

## Comparison

| Mode          | Connection      |
| ------------- | --------------- |
| FromEndpoint  | localhost TCP   |
| HandlerServer | direct Go calls |

---

# HandlerServer Example

```go
pb.RegisterUserServiceHandlerServer(
    context.Background(),
    mux,
    &UserService{},
)
```

Now:

```text
HTTP -> gateway -> Go method call
```

No TCP.
No HTTP/2.
No grpc.Dial().

---

# Tradeoffs

## FromEndpoint Mode

Pros:

* more realistic
* exercises full gRPC stack
* interceptors work naturally
* same behavior as remote deployment

Cons:

* small localhost overhead

---

## HandlerServer Mode

Pros:

* fastest
* simplest

Cons:

* bypasses some gRPC networking behavior
* some interceptors/middleware may behave differently

---

# Simple Analogy

Think of grpc-gateway as a translator.

## Separate process

```text
Translator walks to another building to talk to worker.
```

## In-process

```text
Translator and worker sit in the same office.
```

## HandlerServer

```text
Translator directly taps worker on shoulder.
```


# #In grpc handler I will return my customized error, can this be preserved in http-gateway?

Yes. gRPC-Gateway can preserve your customized gRPC errors into HTTP responses — but **how much gets preserved depends on how you build the error**.

There are 3 common levels:

---

# 1. Standard gRPC Status Error (Best Practice)

If your handler returns:

```go
return nil, status.Error(codes.NotFound, "user not found")
```

grpc-gateway converts it automatically into HTTP JSON:

```json
{
  "code": 5,
  "message": "user not found",
  "details": []
}
```

with HTTP status:

```text
404 Not Found
```

This is fully preserved.

---

# Mapping Example

| gRPC Code              | HTTP Status |
| ---------------------- | ----------- |
| codes.InvalidArgument  | 400         |
| codes.Unauthenticated  | 401         |
| codes.PermissionDenied | 403         |
| codes.NotFound         | 404         |
| codes.AlreadyExists    | 409         |
| codes.Internal         | 500         |

---

# 2. Rich Structured Errors (Recommended)

gRPC supports structured error details using:

```go
status.New(...)
```

and:

```go
errdetails
```

Example:

```go
st := status.New(codes.InvalidArgument, "validation failed")

br := &errdetails.BadRequest{
    FieldViolations: []*errdetails.BadRequest_FieldViolation{
        {
            Field: "email",
            Description: "invalid email format",
        },
    },
}

st, _ = st.WithDetails(br)

return nil, st.Err()
```

grpc-gateway preserves this nicely.

HTTP response:

```json
{
  "code": 3,
  "message": "validation failed",
  "details": [
    {
      "@type": "type.googleapis.com/google.rpc.BadRequest",
      "fieldViolations": [
        {
          "field": "email",
          "description": "invalid email format"
        }
      ]
    }
  ]
}
```

This is the recommended production approach.

---

# 3. Returning Plain Go Errors

If you return:

```go
return nil, errors.New("database exploded")
```

grpc converts it into:

```go
codes.Unknown
```

gateway response:

```json
{
  "code": 2,
  "message": "database exploded"
}
```

You lose:

* proper status mapping
* structured metadata
* semantic meaning

So plain Go errors are not ideal.

---

# Can You Preserve FULL Custom JSON?

Not automatically.

grpc-gateway fundamentally understands:

* gRPC status codes
* protobuf error details

NOT arbitrary Go structs.

This will NOT work directly:

```go
type MyError struct {
    Code int
    Msg  string
}
```

unless you manually convert it.

---

# Production Pattern

Usually people do:

```text
domain error
    ↓
convert to grpc status
    ↓
grpc-gateway converts to HTTP JSON
```

Example:

```go
func ToGrpcError(err error) error {
    switch {
    case errors.Is(err, ErrUserNotFound):
        return status.Error(codes.NotFound, "user not found")

    case errors.Is(err, ErrInvalidEmail):
        return status.Error(codes.InvalidArgument, "invalid email")

    default:
        return status.Error(codes.Internal, "internal error")
    }
}
```

---

# Custom HTTP Error Shape

If you want:

```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "user not found"
  }
}
```

you can customize grpc-gateway using:

```go
runtime.WithErrorHandler(...)
```

Example:

```go
mux := runtime.NewServeMux(
    runtime.WithErrorHandler(customErrorHandler),
)
```

Then you fully control HTTP output.

---

# Example Custom Error Handler

```go
func customErrorHandler(
    ctx context.Context,
    mux *runtime.ServeMux,
    marshaler runtime.Marshaler,
    w http.ResponseWriter,
    r *http.Request,
    err error,
) {
    st, _ := status.FromError(err)

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(runtime.HTTPStatusFromCode(st.Code()))

    json.NewEncoder(w).Encode(map[string]interface{}{
        "success": false,
        "error": map[string]interface{}{
            "grpc_code": st.Code(),
            "message": st.Message(),
        },
    })
}
```

Now your HTTP API has completely customized error JSON.

---

# Important Architectural Insight

grpc-gateway is fundamentally:

```text
HTTP/JSON facade
        over
gRPC status system
```

So the cleanest design is:

```text
business error
    ↓
grpc status + details
    ↓
gateway converts to HTTP
```

instead of trying to push arbitrary HTTP error JSON backward into gRPC.

---

# Recommended Production Stack

## Use:

* `codes.*`
* `status.New`
* `errdetails`

## Avoid:

* random Go errors
* HTTP-specific error structs inside gRPC layer

This keeps:

* gRPC clients
* HTTP clients
* observability
* tracing
* retries

all consistent.


# #If grpc-http-gateway setup with RegisterUserServiceHandlerServer (zero-network), is there still grpc service that gRPC client can dial? or only HTTP service?

Yes — you can still have a real gRPC server that external gRPC clients can dial.

`RegisterUserServiceHandlerServer(...)` only changes **how the HTTP gateway talks to your service implementation internally**.

It does **NOT** remove the gRPC server unless you choose not to start one.

---

# Two Independent Things

You actually have two layers:

| Layer        | Purpose                  |
| ------------ | ------------------------ |
| gRPC Server  | serves gRPC clients      |
| grpc-gateway | serves HTTP/JSON clients |

The gateway is just another client of your service implementation.

---

# Normal FromEndpoint Architecture

With:

```go
RegisterUserServiceHandlerFromEndpoint(...)
```

architecture is:

```text
HTTP Client
    |
grpc-gateway
    |
grpc.Dial()
    |
gRPC Server
    |
UserService
```

Even inside same process.

---

# HandlerServer Architecture

With:

```go
RegisterUserServiceHandlerServer(...)
```

architecture becomes:

```text
HTTP Client
    |
grpc-gateway
    |
direct Go method call
    |
UserService
```

No internal gRPC connection.

BUT you can STILL separately run:

```text
External gRPC Client
        |
     gRPC Server
        |
    UserService
```

at the same time.

---

# Typical Real Setup

Very common production pattern:

```text
                +----------------+
HTTP JSON ----> | grpc-gateway   |
                +----------------+
                         |
                         | direct method call
                         v
                    UserService
                         ^
                         |
                +----------------+
gRPC Client --->| gRPC Server    |
                +----------------+
```

Both share the same service implementation.

---

# Example

```go
svc := &UserService{}
```

## Real gRPC server

```go
grpcServer := grpc.NewServer()

pb.RegisterUserServiceServer(grpcServer, svc)

lis, _ := net.Listen("tcp", ":9090")

go grpcServer.Serve(lis)
```

External gRPC clients can dial:

```text
localhost:9090
```

normally.

---

## HTTP Gateway

```go
mux := runtime.NewServeMux()

pb.RegisterUserServiceHandlerServer(
    context.Background(),
    mux,
    svc,
)
```

Gateway directly calls:

```text
svc.GetUser(...)
```

without gRPC networking.

---

# So What Gets Bypassed?

Only THIS internal path is removed:

```text
gateway -> grpc.Dial -> grpc server
```

The actual gRPC server can still exist.

---

# Important Caveat

With `HandlerServer`, the HTTP path bypasses some gRPC infrastructure:

| Feature                 | FromEndpoint        | HandlerServer  |
| ----------------------- | ------------------- | -------------- |
| HTTP/2 transport        | YES                 | NO             |
| gRPC codec              | YES                 | NO             |
| gRPC network layer      | YES                 | NO             |
| Unary interceptors      | PARTIAL / DIFFERENT | MAY BE SKIPPED |
| Stream behavior realism | FULL                | REDUCED        |

Because gateway directly invokes Go methods.

---

# Important Production Implication

If you rely heavily on:

* auth interceptors
* tracing interceptors
* metrics interceptors
* retry middleware
* gRPC metadata processing

then `HandlerServer` may behave differently from real gRPC traffic.

Many teams therefore prefer:

```go
RegisterUserServiceHandlerFromEndpoint(...)
```

even in same process,
because it exercises the full gRPC stack consistently.

---

# Simple Summary

## `HandlerFromEndpoint`

```text
HTTP -> gateway -> gRPC client -> gRPC server -> service
```

More realistic.

---

## `HandlerServer`

```text
HTTP -> gateway -> service
```

Faster/simpler.

---

## External gRPC clients?

Still fully supported IF you also start a real gRPC server.

`HandlerServer` does NOT disable gRPC serving.


