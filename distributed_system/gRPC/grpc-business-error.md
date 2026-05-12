# #Recommend properly way to define grpc biz codes


If you are building a **pure gRPC service** (without grpc-gateway for now), the cleanest approach is:

* Use **gRPC status codes** for transport/system semantics
* Use **custom business codes** for stable domain contracts
* Put business codes into **structured protobuf error details**
* Avoid encoding everything into plain strings

This scales much better for:

* frontend/mobile apps
* microservices
* retries
* observability
* localization
* long-term API evolution

---

# Recommended Architecture

## 1. Keep gRPC status codes meaningful

Use standard gRPC codes for broad categories:

| Scenario           | gRPC code            |
| ------------------ | -------------------- |
| invalid request    | `InvalidArgument`    |
| not logged in      | `Unauthenticated`    |
| permission denied  | `PermissionDenied`   |
| resource missing   | `NotFound`           |
| duplicate resource | `AlreadyExists`      |
| insufficient state | `FailedPrecondition` |
| rate limited       | `ResourceExhausted`  |
| internal bug       | `Internal`           |
| dependency failure | `Unavailable`        |

These codes are important because:

* SDKs understand them
* load balancers understand them
* retry middleware understands them
* tracing/metrics systems understand them

---

# 2. Define your own business codes separately

Example:

```go id="7o8dbx"
const (
    BizOK = 0

    BizInsufficientBalance = 2000001
    BizCouponExpired       = 2000002
    BizInventoryNotEnough  = 3000001
)
```

Do NOT overload gRPC status codes with business meanings.

---

# 3. Define protobuf error detail message

This is the most important part.

Create a reusable protobuf:

```proto id="7t0m3r"
syntax = "proto3";

package errors;

message BizError {
  int32 code = 1;
  string message = 2;

  // optional machine-readable reason
  string reason = 3;

  // optional extra structured fields
  map<string, string> metadata = 4;
}
```

This becomes your canonical business error schema.

---

# 4. Attach BizError into gRPC status details

Recommended Go implementation:

```go id="8rx1mt"
import (
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/status"
)

func NewBizError(
    grpcCode codes.Code,
    bizCode int32,
    msg string,
) error {
    st := status.New(grpcCode, msg)

    detail := &errorspb.BizError{
        Code:    bizCode,
        Message: msg,
    }

    stWithDetail, err := st.WithDetails(detail)
    if err != nil {
        return st.Err()
    }

    return stWithDetail.Err()
}
```

Usage:

```go id="1wlx2f"
return nil, NewBizError(
    codes.FailedPrecondition,
    BizInsufficientBalance,
    "insufficient balance",
)
```

---

# 5. Client-side extraction

gRPC clients can properly parse structured details:

```go id="v8it1p"
st, ok := status.FromError(err)
if !ok {
    return
}

for _, d := range st.Details() {
    switch v := d.(type) {
    case *errorspb.BizError:
        fmt.Println(v.Code)
        fmt.Println(v.Message)
    }
}
```

This is type-safe and future-proof.

---

# 6. Why this is the best long-term design

Because it separates:

| Concern             | Ownership         |
| ------------------- | ----------------- |
| transport semantics | gRPC status code  |
| business semantics  | biz code          |
| human message       | localized text    |
| machine handling    | structured detail |

This avoids:

* string parsing
* giant switch on messages
* abusing `Internal`
* inventing fake HTTP semantics

---

# 7. Strong recommendation: use enums for reason

Instead of relying only on integers:

```proto id="pwt1c9"
enum BizReason {
  BIZ_REASON_UNSPECIFIED = 0;

  INSUFFICIENT_BALANCE = 1;
  COUPON_EXPIRED = 2;
}
```

Then:

```proto id="1xpgyl"
message BizError {
  int32 code = 1;
  string message = 2;
  BizReason reason = 3;
}
```

Reason enums are:

* easier for clients
* safer than string comparison
* easier for analytics

---

# 8. Avoid these anti-patterns

## BAD — encode everything into message

```go id="ckwo7t"
status.Error(codes.Internal, "ERR_1001")
```

Problem:

* brittle
* impossible to evolve
* ugly client parsing

---

## BAD — all business errors become Internal

```go id="x2tjj9"
status.Error(codes.Internal, "insufficient balance")
```

This destroys retry semantics and observability.

---

## BAD — custom giant error wrapper outside gRPC status

```proto id="q4p0n0"
message Response {
  int32 code = 1;
  string message = 2;
}
```

inside every RPC response.

Problem:

* duplicates gRPC error model
* breaks middleware ecosystem
* clients cannot use standard gRPC error handling

Use real gRPC errors instead.

---

# 9. Recommended mapping strategy

A good practical mapping:

| Business Problem     | gRPC Code            |
| -------------------- | -------------------- |
| validation failed    | `InvalidArgument`    |
| insufficient balance | `FailedPrecondition` |
| duplicate username   | `AlreadyExists`      |
| inventory empty      | `FailedPrecondition` |
| rate limit           | `ResourceExhausted`  |
| account banned       | `PermissionDenied`   |

Then attach precise biz code details.

---

# 10. What many large companies do

Large Go/gRPC systems commonly use:

* `status.Status`
* `errdetails`
* custom protobuf error details
* stable numeric biz codes
* enum reasons
* centralized error package

This is widely used in:

* fintech
* gaming
* ride-hailing
* e-commerce
* cloud infrastructure

because it preserves:

* protocol correctness
* business precision
* extensibility
* observability
* language interoperability
