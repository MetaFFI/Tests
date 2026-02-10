@echo off
REM Generate Go and Python gRPC stubs from benchmark.proto.
REM Prerequisites:
REM   - protoc (Protocol Buffers compiler)
REM   - protoc-gen-go, protoc-gen-go-grpc (Go plugins)
REM   - grpcio-tools (Python: pip install grpcio-tools)

set SCRIPT_DIR=%~dp0

echo Generating Go stubs...
if not exist "%SCRIPT_DIR%pb" mkdir "%SCRIPT_DIR%pb"
protoc ^
  --go_out="%SCRIPT_DIR%pb" --go_opt=paths=source_relative ^
  --go-grpc_out="%SCRIPT_DIR%pb" --go-grpc_opt=paths=source_relative ^
  -I "%SCRIPT_DIR%" ^
  "%SCRIPT_DIR%benchmark.proto"

echo Generating Python stubs...
python -m grpc_tools.protoc ^
  -I "%SCRIPT_DIR%" ^
  --python_out="%SCRIPT_DIR%server" ^
  --grpc_python_out="%SCRIPT_DIR%server" ^
  "%SCRIPT_DIR%benchmark.proto"

echo Done.
