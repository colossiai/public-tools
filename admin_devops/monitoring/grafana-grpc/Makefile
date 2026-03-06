.PHONY: services
services:
	grpcurl -plaintext localhost:50051 list


.PHONY: desc
desc:
	grpcurl -plaintext localhost:50051 describe demogrpc.Greeter

.PHONY: call-function
call-function:
	grpcurl -plaintext -d '{"name":"Alice"}' localhost:50051 demogrpc.Greeter.SayHello

.PHONY: prom-metrics
prom-metrics:
	curl http://localhost:9091/metrics


