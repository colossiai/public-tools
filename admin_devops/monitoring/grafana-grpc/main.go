package main

import (
	"context"
	"log"
	"net"
	"net/http"

	"github.com/colossiai/grafanagrpc/pb"
	grpc_prometheus "github.com/grpc-ecosystem/go-grpc-prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

type greeterServer struct {
	pb.UnimplementedGreeterServer
}

func (s *greeterServer) SayHello(ctx context.Context, req *pb.HelloRequest) (*pb.HelloReply, error) {
	log.Printf("Received request from: %s", req.GetName())
	return &pb.HelloReply{Message: "Hello " + req.GetName()}, nil
}

func main() {
	listener, err := net.Listen("tcp", ":50051")
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	grpcServer := grpc.NewServer(
		// ==> (FOR Prometheus)  add Prometheus interceptors
		grpc.UnaryInterceptor(grpc_prometheus.UnaryServerInterceptor),
		grpc.StreamInterceptor(grpc_prometheus.StreamServerInterceptor),
	)
	// Register service
	pb.RegisterGreeterServer(grpcServer, &greeterServer{})

	// Enable gRPC reflection (for grpcurl)
	reflection.Register(grpcServer)

	// Enable Prometheus metrics
	// ==> (FOR Prometheus)
	// pClient := prometheusmetrics.NewPrometheusProvider(
	// 	metrics.DefaultRegistry,
	// 	"demo-grpc", "prom-metrics",
	// 	prometheus.DefaultRegisterer, time.Second)
	// go pClient.UpdatePrometheusMetrics() // not working
	// ==> (FOR Prometheus)
	grpc_prometheus.Register(grpcServer)

	http.Handle("/metrics", promhttp.Handler())
	go func() {
		// prometheus scrape port 9091
		if err := http.ListenAndServe(":9091", nil); err != nil {
			log.Fatalf("Failed to start metrics server: %v", err)
		}
	}()

	log.Println("Server is running on port 50051")
	if err := grpcServer.Serve(listener); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}
