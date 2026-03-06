#!/usr/bin/env bash
set -e

# Script that generates .pb.go files from the .proto files.
# Manually re-run this script after you edit any .proto file.

# 1. Install protoc
#
#   - Mac OS: `brew install protobuf`
#   - Linux: (TODO - add how to do it)
#
# 2. Install or update gRPC and the protoc plugin for Golang if you have not:
#
# $ go install \
#     github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-grpc-gateway \
#     github.com/grpc-ecosystem/grpc-gateway/v2/protoc-gen-openapiv2 \
#     google.golang.org/protobuf/cmd/protoc-gen-go \
#     google.golang.org/grpc/cmd/protoc-gen-go-grpc
#
# 3. Get the proto files of the API annotations.
#
# $ GO111MODULE=off go get gitlab.bit.com/nvwa/thirdparty

# Get the directory of this script file.
DIR=$(dirname "$0")

# Clean up the current generated .pb.go files
find "$DIR" -name \*.pb.go -delete
find "$DIR" -name \*.pb.gw.go -delete

GOSRC="$GOPATH"/src

protoc -I=. -I=$GOSRC \
   -I=../../.. \
   --go_out . --go_opt paths=source_relative \
   --go-grpc_out . --go-grpc_opt paths=source_relative \
   --grpc-gateway_out . --grpc-gateway_opt paths=source_relative \
   "$DIR"/*.proto
