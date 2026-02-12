package main

import (
	"fmt"
	"os"
	"path/filepath"

	jni "github.com/MetaFFI/tests/go/without_metaffi/call_java_jni"
)

func main() {
	srcRoot := os.Getenv("METAFFI_SOURCE_ROOT")
	if srcRoot == "" {
		fmt.Fprintln(os.Stderr, "FATAL: METAFFI_SOURCE_ROOT must be set")
		os.Exit(1)
	}

	jarPath := filepath.Join(srcRoot, "sdk", "test_modules", "guest_modules", "java", "test_bin", "guest_java.jar")

	fmt.Printf("Initializing JVM with classpath: %s\n", jarPath)
	err := jni.JVMInitialize(jarPath)
	if err != nil {
		fmt.Printf("FAILED: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("JVM initialized successfully")

	fmt.Println("Loading classes...")
	err = jni.JNILoadClasses()
	if err != nil {
		fmt.Printf("FAILED: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Classes loaded successfully")

	// Quick smoke test: void call
	fmt.Println("Testing void call...")
	err = jni.BenchVoidCall()
	if err != nil {
		fmt.Printf("FAILED: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Void call succeeded")

	// Quick smoke test: primitive echo
	fmt.Println("Testing primitive echo (10/2)...")
	val, err := jni.BenchPrimitiveEcho()
	if err != nil {
		fmt.Printf("FAILED: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("Result: %v (expected 5.0)\n", val)

	fmt.Println("\nAll smoke tests passed!")

	// Skip JVMDestroy — DestroyJavaVM hangs waiting for internal threads.
	// Process exit cleans up everything.
}
