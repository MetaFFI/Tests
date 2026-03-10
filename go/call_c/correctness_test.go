package call_c

import (
	"fmt"
	"math"
	"os"
	"path/filepath"
	"runtime"
	"testing"

	api "github.com/MetaFFI/sdk/api/go"
	"github.com/MetaFFI/sdk/idl_entities/go/IDL"
)

// ---------------------------------------------------------------------------
// Global test fixtures
// ---------------------------------------------------------------------------

var (
	metaffiRT *api.MetaFFIRuntime
	module    *api.MetaFFIModule
)

func guestModuleFilename() string {
	if runtime.GOOS == "windows" {
		return "c_guest_module.dll"
	}
	return "c_guest_module.so"
}

func TestMain(m *testing.M) {
	home := os.Getenv("METAFFI_HOME")
	if home == "" {
		fmt.Fprintln(os.Stderr, "FATAL: METAFFI_HOME must be set")
		os.Exit(1)
	}

	srcRoot := os.Getenv("METAFFI_SOURCE_ROOT")
	if srcRoot == "" {
		fmt.Fprintln(os.Stderr, "FATAL: METAFFI_SOURCE_ROOT must be set")
		os.Exit(1)
	}

	// Resolve C guest module path
	modulePath := filepath.Join(srcRoot, "sdk", "test_modules", "guest_modules", "c", "test_bin", guestModuleFilename())
	fmt.Fprintf(os.Stderr, "+++ go_call_c TestMain go=%s\n", runtime.Version())
	fmt.Fprintf(os.Stderr, "+++ go_call_c TestMain METAFFI_HOME=%s\n", home)
	fmt.Fprintf(os.Stderr, "+++ go_call_c TestMain module=%s\n", modulePath)

	// C guest uses the "cpp" runtime (xllr.cpp handles both)
	metaffiRT = api.NewMetaFFIRuntime("cpp")
	if err := metaffiRT.LoadRuntimePlugin(); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: Failed to load cpp runtime plugin: %v\n", err)
		os.Exit(1)
	}

	var err error
	module, err = metaffiRT.LoadModule(modulePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: Failed to load module %s: %v\n", modulePath, err)
		os.Exit(1)
	}

	code := m.Run()
	_ = metaffiRT.ReleaseRuntimePlugin()
	os.Exit(code)
}

// ---------------------------------------------------------------------------
// Helpers -- fail-fast, no fallbacks
// ---------------------------------------------------------------------------

func ti(t IDL.MetaFFIType) IDL.MetaFFITypeInfo {
	return IDL.MetaFFITypeInfo{StringType: t}
}

func load(t *testing.T, entityPath string, params []IDL.MetaFFITypeInfo, retvals []IDL.MetaFFITypeInfo) func(...interface{}) ([]interface{}, error) {
	t.Helper()
	raw, err := module.LoadWithInfo(entityPath, params, retvals)
	if err != nil {
		t.Fatalf("load %q: %v", entityPath, err)
	}
	if raw == nil {
		t.Fatalf("load %q: returned nil function", entityPath)
	}
	switch f := raw.(type) {
	case func() error:
		return func(_ ...interface{}) ([]interface{}, error) { return nil, f() }
	case func() ([]interface{}, error):
		return func(_ ...interface{}) ([]interface{}, error) { return f() }
	case func(...interface{}) error:
		return func(args ...interface{}) ([]interface{}, error) { return nil, f(args...) }
	case func(...interface{}) ([]interface{}, error):
		return f
	default:
		t.Fatalf("load %q: unexpected function type %T", entityPath, raw)
		return nil
	}
}

func call(t *testing.T, name string, ff func(...interface{}) ([]interface{}, error), args ...interface{}) []interface{} {
	t.Helper()
	ret, err := ff(args...)
	if err != nil {
		t.Fatalf("%s: unexpected error: %v", name, err)
	}
	return ret
}

func assertFloat64(t *testing.T, name string, got, want, epsilon float64) {
	t.Helper()
	if math.Abs(got-want) > epsilon {
		t.Fatalf("%s: got %v, want %v (epsilon %v)", name, got, want, epsilon)
	}
}

// ==========================================================================
// Core functions (C guest)
// ==========================================================================

func TestCNoOp(t *testing.T) {
	ff := load(t, "callable=xcall_c_no_op", nil, nil)
	call(t, "c_no_op", ff)
}

func TestCHelloWorld(t *testing.T) {
	ff := load(t, "callable=xcall_c_hello_world", nil, []IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	ret := call(t, "c_hello_world", ff)
	if v, ok := ret[0].(string); !ok || v != "Hello World from C" {
		t.Fatalf("c_hello_world: got %v (%T), want \"Hello World from C\"", ret[0], ret[0])
	}
}

func TestCReturnsAnError(t *testing.T) {
	// C guest returns int32 (-1) instead of throwing
	ff := load(t, "callable=xcall_c_returns_an_error", nil, []IDL.MetaFFITypeInfo{ti(IDL.INT32)})
	ret := call(t, "c_returns_an_error", ff)
	if v, ok := ret[0].(int32); !ok || v != -1 {
		t.Fatalf("c_returns_an_error: got %v (%T), want int32(-1)", ret[0], ret[0])
	}
}

func TestCDivIntegers(t *testing.T) {
	ff := load(t, "callable=xcall_c_div_integers",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64), ti(IDL.INT64)},
		[]IDL.MetaFFITypeInfo{ti(IDL.FLOAT64)})

	ret := call(t, "c_div_integers(10,2)", ff, int64(10), int64(2))
	assertFloat64(t, "c_div_integers(10,2)", ret[0].(float64), 5.0, 1e-10)
}

// ==========================================================================
// State: counter
// ==========================================================================

func TestCCounter(t *testing.T) {
	setCounter := load(t, "callable=xcall_c_set_counter",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)}, nil)
	getCounter := load(t, "callable=xcall_c_get_counter", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)})
	incCounter := load(t, "callable=xcall_c_inc_counter",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)})

	// Reset counter to 0
	call(t, "c_set_counter(0)", setCounter, int64(0))

	// Get counter -> 0
	ret := call(t, "c_get_counter", getCounter)
	if v, ok := ret[0].(int64); !ok || v != 0 {
		t.Fatalf("c_get_counter: got %v (%T), want 0", ret[0], ret[0])
	}

	// Increment by 5
	ret = call(t, "c_inc_counter(5)", incCounter, int64(5))
	if v, ok := ret[0].(int64); !ok || v != 5 {
		t.Fatalf("c_inc_counter(5): got %v (%T), want 5", ret[0], ret[0])
	}

	// Verify
	ret = call(t, "c_get_counter after inc", getCounter)
	if v, ok := ret[0].(int64); !ok || v != 5 {
		t.Fatalf("c_get_counter after inc: got %v (%T), want 5", ret[0], ret[0])
	}

	// Reset
	call(t, "c_set_counter(0) restore", setCounter, int64(0))
}
