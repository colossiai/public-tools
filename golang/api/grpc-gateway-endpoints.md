# Service expose gRPC + HTTP endpoints

A common, **production-grade way** to expose **both gRPC and HTTP endpoints from one server** is to use **gRPC + gRPC-Gateway**. This gives you:

* **gRPC** for internal / high-performance clients
* **HTTP/JSON** for browsers, curl, mobile apps
* **Single source of truth**: `.proto` file

Below are the **three main architectures**, then a **recommended Go setup**.

---

## Option 1 (Recommended): gRPC + gRPC-Gateway (Same Binary)

```
           ┌─────────────┐
HTTP/JSON ─▶ grpc-gateway│
           └─────▲───────┘
                 │ gRPC
           ┌─────┴───────┐
           │ gRPC Server │
           └─────────────┘
```

### Pros

* One `.proto` defines both APIs
* No duplicated handlers
* Strong typing + validation
* Industry standard (Google, Stripe, etc.)

### Cons

* Slightly more setup

---

## Option 2: gRPC + Manual HTTP Handlers

```
HTTP ──▶ net/http handlers
gRPC ──▶ grpc server
```

### Pros

* Simple
* No codegen

### Cons

* Logic duplication
* HTTP and gRPC may drift
* Harder to maintain long-term

---

## Option 3: gRPC Only + Envoy (Infra-heavy)

```
HTTP ─▶ Envoy ─▶ gRPC
```

### Pros

* Clean backend
* Powerful routing

### Cons

* Needs infra / ops support
* Overkill for most apps

---

# ✅ Recommended Go Implementation (gRPC + HTTP)

## 1️⃣ Define proto with HTTP annotations

```proto
syntax = "proto3";

package account.v1;

// if missing go_package: protoc-gen-go: unable to determine Go import path for "account.proto"

option go_package = "github.com/ericyeung/go-repo/grpc/gateway/pb;account";

import "google/api/annotations.proto";

service AccountService {
  rpc GetBalance(GetBalanceRequest) returns (GetBalanceResponse) {
    option (google.api.http) = {
      get: "/v1/accounts/{account_id}/balance"
    };
  }
}

message GetBalanceRequest {
  string account_id = 1;
}

message GetBalanceResponse {
  string cash_available = 1;
  string cash_secured = 2;
}
```

---

## 2️⃣ Generate code

```bash
// google/api (annotations.proto & http.proto) must be downloaded

protoc -I . \
  --go_out=. --go_opt=paths=source_relative \
  --go-grpc_out=. --go-grpc_opt=paths=source_relative \
  --grpc-gateway_out=. --grpc-gateway_opt=paths=source_relative \
  account.proto

```

---

## 3️⃣ Implement gRPC service

```go
type AccountServer struct {
  pb.UnimplementedAccountServiceServer
}

func (s *AccountServer) GetBalance(
  ctx context.Context,
  req *pb.GetBalanceRequest,
) (*pb.GetBalanceResponse, error) {
  return &pb.GetBalanceResponse{
    CashAvailable: "10000.00",
    CashSecured:   "5000.00",
  }, nil
}
```

---

## 4️⃣ Run gRPC + HTTP in one process

```go
func main() {
  ctx := context.Background()

  // gRPC server
  grpcLis, _ := net.Listen("tcp", ":9090")
  grpcServer := grpc.NewServer()
  pb.RegisterAccountServiceServer(grpcServer, &AccountServer{})

  go grpcServer.Serve(grpcLis)

  // HTTP Gateway
  mux := runtime.NewServeMux()
  conn, _ := grpc.DialContext(
    ctx,
    "localhost:9090",
    grpc.WithInsecure(),
  )

  pb.RegisterAccountServiceHandler(ctx, mux, conn)

  http.ListenAndServe(":8080", mux)
}
```

Now you get:

* **gRPC** → `:9090`
* **HTTP/JSON** → `GET /v1/accounts/123/balance`

---

## When This Is Especially Good (Your Case)

Given your previous questions about:

* **API error models**
* **Idempotency**
* **Low-latency Go services**
* **Financial / account systems**

This approach gives you:

* Strong API contracts
* Easy versioning (`/v1`)
* Shared validation
* RFC-7807 compatible error mapping

## curl test

```bash
curl -v http://localhost:8080/v1/accounts/12345/balance
```

---
