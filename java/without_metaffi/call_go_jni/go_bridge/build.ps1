# Build the Go JNI bridge DLL.
# Requires: Go, GCC (MinGW), JAVA_HOME set to JDK installation.

$ErrorActionPreference = "Stop"

if (-not $env:JAVA_HOME) {
    Write-Error "JAVA_HOME must be set"
    exit 1
}

$env:CGO_ENABLED = "1"
$env:CGO_CFLAGS = "-I`"$env:JAVA_HOME\include`" -I`"$env:JAVA_HOME\include\win32`""

Write-Host "Building go_jni_bridge.dll..."
Write-Host "  JAVA_HOME=$env:JAVA_HOME"
Write-Host "  CGO_CFLAGS=$env:CGO_CFLAGS"

Push-Location $PSScriptRoot
try {
    go build -buildmode=c-shared -o go_jni_bridge.dll .
    if ($LASTEXITCODE -ne 0) { throw "go build failed" }
    Write-Host "Built: go_jni_bridge.dll"
} finally {
    Pop-Location
}
