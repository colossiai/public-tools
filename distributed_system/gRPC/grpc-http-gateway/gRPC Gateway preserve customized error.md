# #grpc-http-gateway preserving customized error issue

```
I am building grpc-http-gateway API service, and I return customized error in gRPC handler
1) To preserve customized error, I need to go in-process mode e.g. call RegisterUserServiceHandlerServer
2) But use RegisterUserServiceHandlerServer will loss gRPC interceptors like (auth, recovery etc)

Am I correct?

```

---

Not exactly. There are two separate concerns here:

1. **How grpc-gateway talks to your gRPC service**
2. **Whether gRPC interceptors execute**

`RegisterUserServiceHandlerServer(...)` does **not** inherently disable interceptors.
But it does bypass the gRPC transport stack unless you manually re-enter it.

---

# 1. Two grpc-gateway modes

## A) Normal mode (network / loopback)

```go
pb.RegisterUserServiceHandlerFromEndpoint(...)
```

Flow:

```text
HTTP request
  -> grpc-gateway
    -> gRPC client
      -> gRPC server
        -> interceptors
          -> handler
```

This goes through a real gRPC server.

So:

* Unary interceptors run
* Stream interceptors run
* Auth middleware runs
* Recovery middleware runs
* Stats/tracing run
* Custom metadata works
* Standard gRPC status handling works

Even if it is localhost / same process.

---

## B) In-process direct mode

```go
pb.RegisterUserServiceHandlerServer(...)
```

Flow:

```text
HTTP request
  -> grpc-gateway
    -> handler directly
```

No gRPC client/server transport involved.

So:

* NO gRPC interceptors
* NO transport middleware
* NO grpc.StatsHandler
* NO peer info
* NO actual gRPC lifecycle

The gateway calls your handler implementation directly like normal Go method calls.

So your second statement is correct:

> use RegisterUserServiceHandlerServer will loss gRPC interceptors

Yes.

---

# 2. About customized errors

Your first statement is only partially correct.

You said:

> To preserve customized error, I need in-process mode

Not necessarily.

---

# 3. Why custom errors sometimes get lost

Problem usually comes from:

```text
custom Go error
   ↓
grpc status conversion
   ↓
grpc-gateway JSON conversion
```

If you return plain Go errors:

```go
return nil, myCustomError
```

grpc converts it into:

```go
codes.Unknown
```

and gateway loses your structure.

---

# 4. Correct way: return gRPC status errors

Instead of relying on in-process mode, use proper gRPC status errors.

Example:

```go
st := status.New(codes.InvalidArgument, "validation failed")

detail := &errdetails.BadRequest{
    FieldViolations: []*errdetails.BadRequest_FieldViolation{
        {
            Field: "email",
            Description: "invalid email",
        },
    },
}

st, _ = st.WithDetails(detail)

return nil, st.Err()
```

grpc-gateway can preserve this correctly.

---

# 5. grpc-gateway CAN preserve rich errors over network

grpc-gateway understands:

* `google.rpc.Status`
* error details
* grpc status codes

Even in normal network mode.

You do NOT need `RegisterHandlerServer()` for that.

---

# 6. Recommended production architecture

Usually:

```text
HTTP client
  -> grpc-gateway
      -> localhost gRPC server
          -> interceptors
              -> handlers
```

using:

```go
RegisterUserServiceHandlerFromEndpoint(...)
```

This is the standard production setup.

Benefits:

* interceptors work
* auth centralized
* observability works
* retries possible
* consistent behavior for gRPC + HTTP
* easier future service split

---

# 7. When should RegisterHandlerServer be used?

Mostly for:

* tests
* demos
* very small internal apps
* avoiding loopback overhead
* extremely latency-sensitive setups

But you lose transport-layer behavior.

---

# 8. Important subtlety

With:

```go
RegisterUserServiceHandlerServer(...)
```

you can still manually call shared business logic.

Example:

```text
HTTP gateway
  -> direct handler call
      -> service layer
```

But interceptor logic must be duplicated elsewhere.

This often becomes messy.

---

# 9. Best practice

Use:

```go
RegisterUserServiceHandlerFromEndpoint(...)
```

and standardize your errors as:

```go
status.Status + errdetails
```

instead of custom Go error structs.

That gives you:

* preserved structured errors
* gRPC interceptors
* proper middleware
* production-grade behavior

without needing in-process mode.


# #How to use grpc status.Status + errdetails to respond customized error

```
I want standard http response like this

http stauts=200

{
  "code": 0,
  "message": "",
  "data": {}
}

for return my customized error "code" 

{
  "code": 1000001,
  "message": "insufficient balance",
  "data": {}
}

How grpc status.Status + errdetails can achieve this?

```

`status.Status + errdetails` itself does NOT automatically produce your desired JSON shape.

By default, grpc-gateway outputs something like:

```json
{
  "code": 3,
  "message": "insufficient balance",
  "details": [...]
}
```

where:

* `code` = gRPC code (`InvalidArgument`, etc)
* not your business code (`1000001`)

---

What you want is:

```json
{
  "code": 1000001,
  "message": "insufficient balance",
  "data": {}
}
```

This is a very common “business error envelope” pattern in Asian APIs.

The correct approach is:

# Architecture

Use:

```text
grpc status code
    =
transport/protocol error

business code
    =
application/domain error
```

Meaning:

| Layer            | Purpose             |
| ---------------- | ------------------- |
| gRPC status code | transport semantics |
| business code    | your app logic      |

Example:

| Scenario             | gRPC Code          | business code |
| -------------------- | ------------------ | ------------- |
| invalid argument     | InvalidArgument    | 1001001       |
| insufficient balance | FailedPrecondition | 1000001       |
| unauthenticated      | Unauthenticated    | 1002001       |

---

# Recommended solution

Use:

1. `status.Status`
2. custom protobuf error detail
3. custom grpc-gateway error handler

---

# Step 1 — Define business error proto

Example:

```proto
syntax = "proto3";

package errors;

message BusinessError {
  int32 code = 1;
  string message = 2;
}
```

---

# Step 2 — Attach detail into gRPC status

Example:

```go
st := status.New(
    codes.FailedPrecondition,
    "insufficient balance",
)

detail := &errors.BusinessError{
    Code: 1000001,
    Message: "insufficient balance",
}

st, err := st.WithDetails(detail)
if err != nil {
    return nil, st.Err()
}

return nil, st.Err()
```

Now:

* gRPC interceptors still work
* recovery still works
* auth still works
* metadata still works
* gateway still works

---

# Step 3 — Customize grpc-gateway error response

This is the key part.

grpc-gateway lets you override the default error JSON.

Example:

```go
mux := runtime.NewServeMux(
    runtime.WithErrorHandler(CustomHTTPError),
)
```

---

# Step 4 — Implement custom error handler

Example:

```go
func CustomHTTPError(
    ctx context.Context,
    mux *runtime.ServeMux,
    marshaler runtime.Marshaler,
    w http.ResponseWriter,
    r *http.Request,
    err error,
) {
    st, ok := status.FromError(err)
    if !ok {
        w.WriteHeader(http.StatusInternalServerError)

        json.NewEncoder(w).Encode(map[string]interface{}{
            "code":    500,
            "message": err.Error(),
            "data":    map[string]interface{}{},
        })
        return
    }

    businessCode := int32(0)
    businessMessage := st.Message()

    for _, d := range st.Details() {
        switch v := d.(type) {
        case *errors.BusinessError:
            businessCode = v.Code
            businessMessage = v.Message
        }
    }

    // ALWAYS RETURN HTTP 200
    w.WriteHeader(http.StatusOK)

    json.NewEncoder(w).Encode(map[string]interface{}{
        "code":    businessCode,
        "message": businessMessage,
        "data":    map[string]interface{}{},
    })
}
```

---

# Result

Your handler:

```go
return nil, NewInsufficientBalanceError()
```

becomes:

```json
HTTP/1.1 200 OK

{
  "code": 1000001,
  "message": "insufficient balance",
  "data": {}
}
```

while preserving:

* gRPC interceptors
* tracing
* auth
* recovery
* middleware
* proper gRPC semantics internally

---

# Important production advice

Returning ALL errors as HTTP 200 is controversial.

Many public APIs in China/Asia do this:

```json
{
  "code": xxx
}
```

But Western REST conventions prefer:

| HTTP | Meaning      |
| ---- | ------------ |
| 400  | client error |
| 401  | auth         |
| 403  | forbidden    |
| 500  | server error |

Still, if your frontend/mobile ecosystem expects:

```json
code != 0
```

then your approach is perfectly reasonable.

---

# Best hybrid approach

Internally:

```text
gRPC status code = real transport semantics
```

Externally HTTP JSON:

```json
{
  "code": business_code
}
```

This gives you:

* proper gRPC behavior
* proper observability
* rich interceptors
* standardized frontend response envelope

without needing in-process gateway mode.
