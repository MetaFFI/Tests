#!/bin/bash
# Generate Go and Python gRPC stubs from benchmark.proto.
# Prerequisites:
#   - protoc (Protocol Buffers compiler)
#   - protoc-gen-go, protoc-gen-go-grpc (Go plugins)
#   - grpcio-tools (Python: pip install grpcio-tools)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Generating Go stubs..."
mkdir -p "$SCRIPT_DIR/pb"
protoc \
  --go_out="$SCRIPT_DIR/pb" --go_opt=paths=source_relative \
  --go-grpc_out="$SCRIPT_DIR/pb" --go-grpc_opt=paths=source_relative \
  -I "$SCRIPT_DIR" \
  "$SCRIPT_DIR/benchmark.proto"

echo "Generating Python stubs..."
python -m grpc_tools.protoc \
  -I "$SCRIPT_DIR" \
  --python_out="$SCRIPT_DIR/server" \
  --grpc_python_out="$SCRIPT_DIR/server" \
  "$SCRIPT_DIR/benchmark.proto"

echo "Done."
