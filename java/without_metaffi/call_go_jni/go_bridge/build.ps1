# Build the Go JNI bridge DLL.
# Requires: Go, GCC (MinGW), JAVA_HOME set to JDK installation.

$ErrorActionPreference = "Stop"

if (-not $env:JAVA_HOME) {
    Write-Error "JAVA_HOME must be set"
    exit 1
}

$env:CGO_ENABLED = "1"

# Mirror JDK headers into a local path without spaces (CGO/GCC on Windows is
# fragile with quoted include paths in CGO_CFLAGS).
$localJavaInclude = Join-Path $PSScriptRoot ".java_include"
if (Test-Path $localJavaInclude) {
    Remove-Item -Recurse -Force $localJavaInclude
}
New-Item -ItemType Directory -Path $localJavaInclude | Out-Null
Copy-Item -Recurse -Force (Join-Path $env:JAVA_HOME "include\\*") $localJavaInclude

$localJavaIncludePosix = ($localJavaInclude -replace "\\", "/")
$env:CGO_CFLAGS = "-I$localJavaIncludePosix -I$localJavaIncludePosix/win32"

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
