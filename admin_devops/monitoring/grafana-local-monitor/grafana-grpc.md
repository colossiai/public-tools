To monitor gRPC metrics in a Go application with Grafana, you’ll typically use Prometheus as the metrics collection tool. Here's an example setup:

---

### **1. Install Dependencies**
Install the necessary Go libraries:
```bash
go get github.com/grpc-ecosystem/go-grpc-prometheus
go get github.com/prometheus/client_golang/prometheus
go get github.com/prometheus/client_golang/prometheus/promhttp
```

---

### **2. Instrument Your gRPC Server**

Below is an example of setting up a gRPC server and exposing metrics:

#### **server.go**
```go
package main

import (
	"context"
	"net"
	"net/http"

	"github.com/grpc-ecosystem/go-grpc-prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"google.golang.org/grpc"
	"log"
	pb "your_package/protos" // Replace with your gRPC generated proto package
)

// Your gRPC server implementation
type server struct {
	pb.UnimplementedYourServiceServer // Replace with your service's name
}

func (s *server) YourRPCMethod(ctx context.Context, req *pb.YourRequest) (*pb.YourResponse, error) {
	// Business logic
	return &pb.YourResponse{Message: "Hello, " + req.Name}, nil
}

func main() {
	// Create a gRPC server with Prometheus interceptors
	grpcServer := grpc.NewServer(
		grpc.UnaryInterceptor(grpc_prometheus.UnaryServerInterceptor),
		grpc.StreamInterceptor(grpc_prometheus.StreamServerInterceptor),
	)

	// Register your service
	pb.RegisterYourServiceServer(grpcServer, &server{})

	// Enable Prometheus metrics
	grpc_prometheus.Register(grpcServer)

	// Start a listener for gRPC
	listener, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}

	go func() {
		// HTTP server for Prometheus metrics
		http.Handle("/metrics", promhttp.Handler())
		log.Println("Serving Prometheus metrics at :8080/metrics")
		log.Fatal(http.ListenAndServe(":8080", nil))
	}()

	log.Println("Starting gRPC server on :50051")
	if err := grpcServer.Serve(listener); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
```

---

### **3. Create a Prometheus Configuration**
Create a `prometheus.yml` file to scrape metrics from your application.

#### **prometheus.yml**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "grpc_server"
    static_configs:
      - targets: ["localhost:8080"] # use "host.docker.internal:8080" if prometheus running inside docer
```

---

### **4. Run Prometheus**
Run Prometheus with the configuration file:
```bash
prometheus --config.file=prometheus.yml
```

---

### **5. Set Up Grafana**
1. Install Grafana if you haven’t already.
2. Add Prometheus as a data source:
   - Go to **Settings > Data Sources > Add Data Source**.
   - Select **Prometheus** and set the URL as `http://localhost:9090`.
3. Import a dashboard:
   - Search for or create a dashboard to visualize gRPC metrics (e.g., request rate, latency, etc.).

---

### **6. Visualize gRPC Metrics**
Key metrics to monitor:
- `grpc_server_handled_total`: Total number of RPCs completed.
- `grpc_server_handling_seconds_bucket`: Latency distribution.
- `grpc_server_handling_seconds_sum`: Total time spent handling RPCs.
- `grpc_server_handling_seconds_count`: Number of handled RPCs.

---

This example sets up a basic gRPC server and exposes its metrics to Prometheus, which Grafana can then use for visualization. You can customize the Grafana dashboard to meet your monitoring needs.


## Examine the metrics

* grpc_server_handled_total

```bash
$ make call-function
grpcurl -plaintext -d '{"name":"Alice"}' localhost:50051 demogrpc.Greeter.SayHello
{
  "message": "Hello Alice"
}

$ curl http://localhost:9091/metrics | grep SayHello | grep OK
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 16738    0 16738    0     0  13.8M      0 --:--:-- --:--:-- --:--:-- 15.9M
grpc_server_handled_total{grpc_code="OK",grpc_method="SayHello",grpc_service="demogrpc.Greeter",grpc_type="unary"} 1

```