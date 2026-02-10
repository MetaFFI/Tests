@echo off
REM Generate Go gRPC stubs from benchmark.proto

if not exist "%~dp0pb" mkdir "%~dp0pb"

protoc ^
  --go_out="%~dp0pb" --go_opt=paths=source_relative ^
  --go-grpc_out="%~dp0pb" --go-grpc_opt=paths=source_relative ^
  -I "%~dp0" ^
  "%~dp0benchmark.proto"

echo Go stubs generated in %~dp0pb\
echo To build Java gRPC server: cd %~dp0server ^&^& gradle shadowJar
