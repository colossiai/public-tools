# #Show Server streaming and Client streaming interceptor example


In gRPC, streaming interceptors use:

```go id="2vf6eu"
grpc.StreamServerInterceptor
grpc.StreamClientInterceptor
```

because streaming RPCs operate on a `ServerStream` / `ClientStream` instead of a single request/response.

---

# Server Streaming Example

Proto:

```proto id="ny0yqq"
service UserService {
  rpc ListUsers(ListUsersReq) returns (stream User);
}
```

Server interceptor:

```go id="y9l9cf"
func StreamLoggingInterceptor(
    srv any,
    ss grpc.ServerStream,
    info *grpc.StreamServerInfo,
    handler grpc.StreamHandler,
) error {

    log.Printf(
        "method=%s client_stream=%v server_stream=%v",
        info.FullMethod,
        info.IsClientStream,
        info.IsServerStream,
    )

    err := handler(srv, ss)

    if err != nil {
        log.Printf("stream error: %v", err)
    }

    return err
}
```

Register:

```go id="4r90t0"
grpc.NewServer(
    grpc.StreamInterceptor(StreamLoggingInterceptor),
)
```

Server implementation:

```go id="yz65m0"
func (s *Server) ListUsers(
    req *pb.ListUsersReq,
    stream pb.UserService_ListUsersServer,
) error {

    users := []string{"alice", "bob", "charlie"}

    for _, u := range users {
        if err := stream.Send(&pb.User{Name: u}); err != nil {
            return err
        }
    }

    return nil
}
```

Flow:

```text id="6sjh1e"
client ----1 request----> server
client <---many responses--- server
```

---

# Client Streaming Example

Proto:

```proto id="59z2ik"
service UploadService {
  rpc Upload(stream Chunk) returns (UploadResp);
}
```

Server interceptor is still `StreamServerInterceptor`
because from gRPC's perspective, all streaming RPCs use stream interceptors.

Implementation:

```go id="h5lpxy"
func (s *Server) Upload(
    stream pb.UploadService_UploadServer,
) error {

    var total int

    for {
        chunk, err := stream.Recv()

        if err == io.EOF {
            return stream.SendAndClose(
                &pb.UploadResp{Size: int64(total)},
            )
        }

        if err != nil {
            return err
        }

        total += len(chunk.Data)
    }
}
```

Flow:

```text id="7ph8s4"
client ----many chunks----> server
client <----1 response----- server
```

---

# Stream Client Interceptor Example

Client-side stream interceptor:

```go id="mz9x3h"
func ClientStreamInterceptor(
    ctx context.Context,
    desc *grpc.StreamDesc,
    cc *grpc.ClientConn,
    method string,
    streamer grpc.Streamer,
    opts ...grpc.CallOption,
) (grpc.ClientStream, error) {

    log.Printf("calling stream method=%s", method)

    stream, err := streamer(
        ctx,
        desc,
        cc,
        method,
        opts...,
    )

    if err != nil {
        log.Printf("stream error=%v", err)
        return nil, err
    }

    return stream, nil
}
```

Register:

```go id="sygqho"
conn, err := grpc.Dial(
    addr,
    grpc.WithStreamInterceptor(ClientStreamInterceptor),
)
```

---

# Key Difference vs Unary Interceptor

Unary interceptor:

```text id="a20rza"
req -> interceptor -> handler -> resp
```

Streaming interceptor:

```text id="x2mc9l"
stream object -> interceptor -> handler
```

The stream may stay alive for minutes or hours and can contain many messages, so gRPC exposes the stream abstraction instead of individual messages.
