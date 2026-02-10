package call_python3

import (
	"fmt"
	"math"
	"os"
	"path/filepath"
	"strings"
	"testing"

	api "github.com/MetaFFI/sdk/api/go"
	goruntime "github.com/MetaFFI/sdk/api/go/metaffi"
	"github.com/MetaFFI/sdk/idl_entities/go/IDL"
)

// ---------------------------------------------------------------------------
// Global test fixtures
// ---------------------------------------------------------------------------

var (
	metaffiRT    *api.MetaFFIRuntime
	moduleDir    *api.MetaFFIModule // Python package: module/
	moduleFile   *api.MetaFFIModule // Single file: single_file_module.py
)

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

	// Resolve guest module paths
	moduleDirPath := filepath.Join(srcRoot, "sdk", "test_modules", "guest_modules", "python3", "module")
	moduleFilePath := filepath.Join(srcRoot, "sdk", "test_modules", "guest_modules", "python3", "single_file_module.py")

	metaffiRT = api.NewMetaFFIRuntime("python3")
	if err := metaffiRT.LoadRuntimePlugin(); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: Failed to load python3 runtime plugin: %v\n", err)
		os.Exit(1)
	}

	var err error
	moduleDir, err = metaffiRT.LoadModule(moduleDirPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: Failed to load module dir %s: %v\n", moduleDirPath, err)
		os.Exit(1)
	}

	moduleFile, err = metaffiRT.LoadModule(moduleFilePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: Failed to load module file %s: %v\n", moduleFilePath, err)
		os.Exit(1)
	}

	code := m.Run()
	_ = metaffiRT.ReleaseRuntimePlugin()
	os.Exit(code)
}

// ---------------------------------------------------------------------------
// Helpers -- fail-fast, no fallbacks
// ---------------------------------------------------------------------------

// ti creates a MetaFFITypeInfo for a scalar type.
func ti(t IDL.MetaFFIType) IDL.MetaFFITypeInfo {
	return IDL.MetaFFITypeInfo{StringType: t}
}

// tiArray creates a MetaFFITypeInfo for an array type with given dimensions.
func tiArray(t IDL.MetaFFIType, dims int) IDL.MetaFFITypeInfo {
	return IDL.MetaFFITypeInfo{StringType: t, Dimensions: dims}
}

// load loads an entity; fatals immediately on error (fail-fast).
func load(t *testing.T, mod *api.MetaFFIModule, entityPath string, params []IDL.MetaFFITypeInfo, retvals []IDL.MetaFFITypeInfo) func(...interface{}) ([]interface{}, error) {
	t.Helper()
	ff, err := mod.LoadWithInfo(entityPath, params, retvals)
	if err != nil {
		t.Fatalf("load %q: %v", entityPath, err)
	}
	if ff == nil {
		t.Fatalf("load %q: returned nil function", entityPath)
	}
	return ff
}

// call invokes ff and fatals on error (fail-fast).
func call(t *testing.T, name string, ff func(...interface{}) ([]interface{}, error), args ...interface{}) []interface{} {
	t.Helper()
	ret, err := ff(args...)
	if err != nil {
		t.Fatalf("%s: unexpected error: %v", name, err)
	}
	return ret
}

// callExpectError invokes ff and expects an error containing substr.
func callExpectError(t *testing.T, name string, ff func(...interface{}) ([]interface{}, error), substr string, args ...interface{}) {
	t.Helper()
	_, err := ff(args...)
	if err == nil {
		t.Fatalf("%s: expected error containing %q but got nil", name, substr)
	}
	if !strings.Contains(strings.ToLower(err.Error()), strings.ToLower(substr)) {
		t.Fatalf("%s: error %q does not contain %q", name, err.Error(), substr)
	}
}

// assertFloat64 checks a float64 value with epsilon tolerance.
// Epsilon is explicitly justified: Python float division may produce IEEE 754 rounding.
func assertFloat64(t *testing.T, name string, got, want, epsilon float64) {
	t.Helper()
	if math.Abs(got-want) > epsilon {
		t.Fatalf("%s: got %v, want %v (epsilon %v)", name, got, want, epsilon)
	}
}

// ==========================================================================
// core_functions.py
// ==========================================================================

func TestCoreHelloWorld(t *testing.T) {
	ff := load(t, moduleDir, "callable=hello_world", nil, []IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	ret := call(t, "hello_world", ff)
	if v, ok := ret[0].(string); !ok || v != "Hello World, from Python3" {
		t.Fatalf("hello_world: got %v (%T), want \"Hello World, from Python3\"", ret[0], ret[0])
	}
}

func TestCoreDivIntegers(t *testing.T) {
	ff := load(t, moduleDir, "callable=div_integers",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64), ti(IDL.INT64)},
		[]IDL.MetaFFITypeInfo{ti(IDL.FLOAT64)})

	ret := call(t, "div_integers(10,2)", ff, int64(10), int64(2))
	assertFloat64(t, "div_integers(10,2)", ret[0].(float64), 5.0, 1e-10)
}

func TestCoreJoinStrings(t *testing.T) {
	ff := load(t, moduleDir, "callable=join_strings",
		[]IDL.MetaFFITypeInfo{tiArray(IDL.STRING8_ARRAY, 1)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})

	ret := call(t, "join_strings", ff, []string{"a", "b", "c"})
	if v, ok := ret[0].(string); !ok || v != "a,b,c" {
		t.Fatalf("join_strings: got %v (%T), want \"a,b,c\"", ret[0], ret[0])
	}
}

func TestCoreWaitABit(t *testing.T) {
	ff := load(t, moduleDir, "callable=wait_a_bit",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)}, nil)
	call(t, "wait_a_bit", ff, int64(1))
}

func TestCoreReturnNull(t *testing.T) {
	ff := load(t, moduleDir, "callable=return_null", nil, []IDL.MetaFFITypeInfo{ti(IDL.NULL)})
	ret := call(t, "return_null", ff)
	if ret[0] != nil {
		t.Fatalf("return_null: got %v (%T), want nil", ret[0], ret[0])
	}
}

func TestCoreReturnsAnError(t *testing.T) {
	ff := load(t, moduleDir, "callable=returns_an_error", nil, nil)
	callExpectError(t, "returns_an_error", ff, "Error")
}

func TestCoreCallCallbackAdd(t *testing.T) {
	ff := load(t, moduleDir, "callable=call_callback_add",
		[]IDL.MetaFFITypeInfo{ti(IDL.CALLABLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)})

	// Provide a Go function as callback: add(a, b) -> a + b
	adder := func(a, b int64) int64 { return a + b }

	ret := call(t, "call_callback_add", ff, adder)
	if v, ok := ret[0].(int64); !ok || v != 3 {
		t.Fatalf("call_callback_add: got %v (%T), want 3", ret[0], ret[0])
	}
}

func TestCoreReturnCallbackAdd(t *testing.T) {
	ff := load(t, moduleDir, "callable=return_callback_add", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.CALLABLE)})

	ret := call(t, "return_callback_add", ff)
	if ret[0] == nil {
		t.Fatal("return_callback_add: got nil callable")
	}

	callable, ok := ret[0].(*goruntime.MetaFFICallable)
	if !ok {
		t.Fatalf("return_callback_add: expected *MetaFFICallable, got %T", ret[0])
	}

	result, err := callable.Call(int64(3), int64(4))
	if err != nil {
		t.Fatalf("callable.Call(3, 4): %v", err)
	}
	if v, ok := result[0].(int64); !ok || v != 7 {
		t.Fatalf("callable.Call(3, 4): got %v (%T), want 7", result[0], result[0])
	}
}

func TestCoreReturnMultipleReturnValues(t *testing.T) {
	ff := load(t, moduleDir, "callable=return_multiple_return_values", nil,
		[]IDL.MetaFFITypeInfo{
			ti(IDL.INT64), ti(IDL.STRING8), ti(IDL.FLOAT64),
			ti(IDL.NULL), ti(IDL.UINT8_ARRAY), ti(IDL.HANDLE),
		})

	ret := call(t, "return_multiple_return_values", ff)
	if len(ret) != 6 {
		t.Fatalf("return_multiple_return_values: got %d returns, want 6", len(ret))
	}

	// ret[0] = 1 (int64)
	if v, ok := ret[0].(int64); !ok || v != 1 {
		t.Fatalf("ret[0]: got %v (%T), want int64(1)", ret[0], ret[0])
	}

	// ret[1] = "string"
	if v, ok := ret[1].(string); !ok || v != "string" {
		t.Fatalf("ret[1]: got %v (%T), want \"string\"", ret[1], ret[1])
	}

	// ret[2] = 3.0
	assertFloat64(t, "ret[2]", ret[2].(float64), 3.0, 1e-10)

	// ret[3] = nil (None)
	if ret[3] != nil {
		t.Fatalf("ret[3]: got %v (%T), want nil", ret[3], ret[3])
	}

	// ret[5] = handle (SomeClass instance) - just check it's not nil
	if ret[5] == nil {
		t.Fatal("ret[5] (SomeClass handle): got nil")
	}
}

func TestCoreReturnAny(t *testing.T) {
	ff := load(t, moduleDir, "callable=return_any",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)},
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)})

	// which=0 -> int(1)
	ret := call(t, "return_any(0)", ff, int64(0))
	if v, ok := ret[0].(int64); !ok || v != 1 {
		t.Fatalf("return_any(0): got %v (%T), want int64(1)", ret[0], ret[0])
	}

	// which=1 -> "string"
	ret = call(t, "return_any(1)", ff, int64(1))
	if v, ok := ret[0].(string); !ok || v != "string" {
		t.Fatalf("return_any(1): got %v (%T), want \"string\"", ret[0], ret[0])
	}

	// which=2 -> 3.0
	ret = call(t, "return_any(2)", ff, int64(2))
	assertFloat64(t, "return_any(2)", ret[0].(float64), 3.0, 1e-10)

	// which=999 -> None
	ret = call(t, "return_any(999)", ff, int64(999))
	if ret[0] != nil {
		t.Fatalf("return_any(999): got %v (%T), want nil", ret[0], ret[0])
	}
}

func TestCoreAcceptsAny(t *testing.T) {
	ff := load(t, moduleDir, "callable=accepts_any",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64), ti(IDL.ANY)}, nil)

	// which=0, val=int64(1)
	call(t, "accepts_any(0, int64)", ff, int64(0), int64(1))

	// which=1, val="string"
	call(t, "accepts_any(1, string)", ff, int64(1), "string")

	// which=2, val=3.0
	call(t, "accepts_any(2, float64)", ff, int64(2), float64(3.0))
}

func TestCoreGetThreeBuffers(t *testing.T) {
	ff := load(t, moduleDir, "callable=get_three_buffers", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.ARRAY, 1)})

	ret := call(t, "get_three_buffers", ff)
	if ret[0] == nil {
		t.Fatal("get_three_buffers: got nil")
	}
}

func TestCoreGetSomeClasses(t *testing.T) {
	ff := load(t, moduleDir, "callable=get_some_classes", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.HANDLE_ARRAY, 1)})

	ret := call(t, "get_some_classes", ff)
	if ret[0] == nil {
		t.Fatal("get_some_classes: got nil")
	}
}

// ==========================================================================
// objects_and_classes.py -- SomeClass
// ==========================================================================

func TestSomeClassCreateAndPrint(t *testing.T) {
	// Get the class itself
	getClass := load(t, moduleDir, "attribute=SomeClass,getter", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	classRet := call(t, "SomeClass class getter", getClass)
	classHandle := classRet[0]

	// Create new instance via __new__
	newEntity := load(t, moduleDir, "callable=SomeClass.__new__",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "SomeClass.__new__", newEntity, classHandle)
	instance := instanceRet[0]

	// Initialize via __init__
	initEntity := load(t, moduleDir, "callable=SomeClass.__init__,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)}, nil)
	call(t, "SomeClass.__init__", initEntity, instance, "test_name")

	// Call .print()
	printEntity := load(t, moduleDir, "callable=SomeClass.print,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	printRet := call(t, "SomeClass.print", printEntity, instance)
	if v, ok := printRet[0].(string); !ok || v != "Hello from SomeClass test_name" {
		t.Fatalf("SomeClass.print: got %q, want \"Hello from SomeClass test_name\"", printRet[0])
	}
}

func TestSomeClassStr(t *testing.T) {
	// Get class and create instance
	getClass := load(t, moduleDir, "attribute=SomeClass,getter", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	classRet := call(t, "SomeClass getter", getClass)

	newEntity := load(t, moduleDir, "callable=SomeClass.__new__",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "SomeClass.__new__", newEntity, classRet[0])
	instance := instanceRet[0]

	initEntity := load(t, moduleDir, "callable=SomeClass.__init__,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)}, nil)
	call(t, "SomeClass.__init__", initEntity, instance, "abc")

	// Call __str__
	strEntity := load(t, moduleDir, "callable=SomeClass.__str__,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	strRet := call(t, "SomeClass.__str__", strEntity, instance)
	if v, ok := strRet[0].(string); !ok || !strings.Contains(v, "SomeClass") {
		t.Fatalf("SomeClass.__str__: got %q, expected it to contain \"SomeClass\"", strRet[0])
	}
}

// ==========================================================================
// objects_and_classes.py -- TestMap
// ==========================================================================

func TestTestMapSetGetContains(t *testing.T) {
	// Get class
	getClass := load(t, moduleDir, "attribute=TestMap,getter", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	classRet := call(t, "TestMap getter", getClass)

	// Create instance
	newEntity := load(t, moduleDir, "callable=TestMap.__new__",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "TestMap.__new__", newEntity, classRet[0])
	instance := instanceRet[0]

	initEntity := load(t, moduleDir, "callable=TestMap.__init__,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)}, nil)
	call(t, "TestMap.__init__", initEntity, instance)

	// Set
	setEntity := load(t, moduleDir, "callable=TestMap.set,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8), ti(IDL.ANY)}, nil)
	call(t, "TestMap.set", setEntity, instance, "key1", int64(42))

	// Contains
	containsEntity := load(t, moduleDir, "callable=TestMap.contains,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.BOOL)})
	containsRet := call(t, "TestMap.contains", containsEntity, instance, "key1")
	if v, ok := containsRet[0].(bool); !ok || !v {
		t.Fatalf("TestMap.contains(key1): got %v, want true", containsRet[0])
	}

	// Get
	getEntity := load(t, moduleDir, "callable=TestMap.get,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)})
	getRet := call(t, "TestMap.get", getEntity, instance, "key1")
	if v, ok := getRet[0].(int64); !ok || v != 42 {
		t.Fatalf("TestMap.get(key1): got %v (%T), want 42", getRet[0], getRet[0])
	}

	// Contains for non-existent key
	containsRet = call(t, "TestMap.contains(missing)", containsEntity, instance, "nonexistent")
	if v, ok := containsRet[0].(bool); !ok || v {
		t.Fatalf("TestMap.contains(nonexistent): got %v, want false", containsRet[0])
	}
}

// ==========================================================================
// objects_and_classes.py -- BaseClass / DerivedClass
// ==========================================================================

func TestBaseClassStaticValue(t *testing.T) {
	ff := load(t, moduleDir, "callable=BaseClass.static_value", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)})
	ret := call(t, "BaseClass.static_value", ff)
	if v, ok := ret[0].(int64); !ok || v != 42 {
		t.Fatalf("BaseClass.static_value: got %v (%T), want 42", ret[0], ret[0])
	}
}

// ==========================================================================
// types_and_arrays.py
// ==========================================================================

func TestArraysMake1D(t *testing.T) {
	ff := load(t, moduleDir, "callable=make_1d_array", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT64_ARRAY, 1)})
	ret := call(t, "make_1d_array", ff)
	arr, ok := ret[0].([]int64)
	if !ok {
		t.Fatalf("make_1d_array: unexpected type %T", ret[0])
	}
	want := []int64{1, 2, 3}
	if len(arr) != len(want) {
		t.Fatalf("make_1d_array: len=%d, want %d", len(arr), len(want))
	}
	for i, v := range want {
		if arr[i] != v {
			t.Fatalf("make_1d_array[%d]: got %d, want %d", i, arr[i], v)
		}
	}
}

func TestArraysMake2D(t *testing.T) {
	ff := load(t, moduleDir, "callable=make_2d_array", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT64_ARRAY, 2)})
	ret := call(t, "make_2d_array", ff)
	arr, ok := ret[0].([][]int64)
	if !ok {
		t.Fatalf("make_2d_array: unexpected type %T", ret[0])
	}
	if len(arr) != 2 || len(arr[0]) != 2 || len(arr[1]) != 2 {
		t.Fatalf("make_2d_array: shape mismatch %v", arr)
	}
	if arr[0][0] != 1 || arr[0][1] != 2 || arr[1][0] != 3 || arr[1][1] != 4 {
		t.Fatalf("make_2d_array: values mismatch %v", arr)
	}
}

func TestArraysMake3D(t *testing.T) {
	ff := load(t, moduleDir, "callable=make_3d_array", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT64_ARRAY, 3)})
	ret := call(t, "make_3d_array", ff)
	arr, ok := ret[0].([][][]int64)
	if !ok {
		t.Fatalf("make_3d_array: unexpected type %T", ret[0])
	}
	if arr[0][0][0] != 1 || arr[0][1][0] != 2 || arr[1][0][0] != 3 || arr[1][1][0] != 4 {
		t.Fatalf("make_3d_array: values mismatch %v", arr)
	}
}

func TestArraysMakeRagged(t *testing.T) {
	ff := load(t, moduleDir, "callable=make_ragged_array", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT64_ARRAY, 2)})
	ret := call(t, "make_ragged_array", ff)
	ragged, ok := ret[0].([][]int64)
	if !ok {
		t.Fatalf("make_ragged_array: unexpected type %T", ret[0])
	}
	if len(ragged) != 3 {
		t.Fatalf("make_ragged_array: len=%d, want 3", len(ragged))
	}
	if len(ragged[0]) != 3 || ragged[0][0] != 1 || ragged[0][1] != 2 || ragged[0][2] != 3 {
		t.Fatalf("make_ragged_array[0]: %v", ragged[0])
	}
	if len(ragged[1]) != 1 || ragged[1][0] != 4 {
		t.Fatalf("make_ragged_array[1]: %v", ragged[1])
	}
	if len(ragged[2]) != 2 || ragged[2][0] != 5 || ragged[2][1] != 6 {
		t.Fatalf("make_ragged_array[2]: %v", ragged[2])
	}
}

func TestArraysAccepts3D(t *testing.T) {
	ff := load(t, moduleDir, "callable=accepts_3d_array",
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT64_ARRAY, 3)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)})

	arr := [][][]int64{{{1}, {2}}, {{3}, {4}}}
	ret := call(t, "accepts_3d_array", ff, arr)
	if v, ok := ret[0].(int64); !ok || v != 10 {
		t.Fatalf("accepts_3d_array: got %v (%T), want 10", ret[0], ret[0])
	}
}

func TestArraysAcceptsRagged(t *testing.T) {
	ff := load(t, moduleDir, "callable=accepts_ragged_array",
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT64_ARRAY, 2)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)})

	arr := [][]int64{{1, 2, 3}, {4}, {5, 6}}
	ret := call(t, "accepts_ragged_array", ff, arr)
	if v, ok := ret[0].(int64); !ok || v != 21 {
		t.Fatalf("accepts_ragged_array: got %v (%T), want 21", ret[0], ret[0])
	}
}

func TestReturnsBytes(t *testing.T) {
	ff := load(t, moduleDir, "callable=returns_bytes_buffer", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.UINT8_ARRAY, 1)})
	ret := call(t, "returns_bytes_buffer", ff)
	arr, ok := ret[0].([]uint8)
	if !ok {
		t.Fatalf("returns_bytes_buffer: unexpected type %T", ret[0])
	}
	want := []uint8{1, 2, 3}
	if len(arr) != len(want) {
		t.Fatalf("returns_bytes_buffer: len=%d, want %d", len(arr), len(want))
	}
	for i, v := range want {
		if arr[i] != v {
			t.Fatalf("returns_bytes_buffer[%d]: got %d, want %d", i, arr[i], v)
		}
	}
}

func TestReturnsOptional(t *testing.T) {
	ff := load(t, moduleDir, "callable=returns_optional",
		[]IDL.MetaFFITypeInfo{ti(IDL.BOOL)},
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)})

	// flag=true -> 123
	ret := call(t, "returns_optional(true)", ff, true)
	if v, ok := ret[0].(int64); !ok || v != 123 {
		t.Fatalf("returns_optional(true): got %v (%T), want 123", ret[0], ret[0])
	}

	// flag=false -> None
	ret = call(t, "returns_optional(false)", ff, false)
	if ret[0] != nil {
		t.Fatalf("returns_optional(false): got %v (%T), want nil", ret[0], ret[0])
	}
}

// ==========================================================================
// callbacks_and_errors.py
// ==========================================================================

func TestRaiseCustomError(t *testing.T) {
	ff := load(t, moduleDir, "callable=raise_custom_error",
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)}, nil)
	callExpectError(t, "raise_custom_error", ff, "boom", "boom")
}

func TestReturnErrorTuple(t *testing.T) {
	ff := load(t, moduleDir, "callable=return_error_tuple",
		[]IDL.MetaFFITypeInfo{ti(IDL.BOOL)},
		[]IDL.MetaFFITypeInfo{ti(IDL.BOOL), ti(IDL.ANY)})

	// ok=true -> (True, None)
	ret := call(t, "return_error_tuple(true)", ff, true)
	if v, ok := ret[0].(bool); !ok || !v {
		t.Fatalf("return_error_tuple(true)[0]: got %v, want true", ret[0])
	}
	if ret[1] != nil {
		t.Fatalf("return_error_tuple(true)[1]: got %v, want nil", ret[1])
	}

	// ok=false -> (False, "error")
	ret = call(t, "return_error_tuple(false)", ff, false)
	if v, ok := ret[0].(bool); !ok || v {
		t.Fatalf("return_error_tuple(false)[0]: got %v, want false", ret[0])
	}
	if v, ok := ret[1].(string); !ok || v != "error" {
		t.Fatalf("return_error_tuple(false)[1]: got %v (%T), want \"error\"", ret[1], ret[1])
	}
}

// ==========================================================================
// module_state.py
// ==========================================================================

func TestModuleStateCounter(t *testing.T) {
	// Set counter to 0
	setCounter := load(t, moduleDir, "callable=set_counter",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)}, nil)
	call(t, "set_counter(0)", setCounter, int64(0))

	// Get counter -> 0
	getCounter := load(t, moduleDir, "callable=get_counter", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)})
	ret := call(t, "get_counter", getCounter)
	if v, ok := ret[0].(int64); !ok || v != 0 {
		t.Fatalf("get_counter: got %v (%T), want 0", ret[0], ret[0])
	}

	// Increment by 5
	incCounter := load(t, moduleDir, "callable=inc_counter",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)})
	ret = call(t, "inc_counter(5)", incCounter, int64(5))
	if v, ok := ret[0].(int64); !ok || v != 5 {
		t.Fatalf("inc_counter(5): got %v (%T), want 5", ret[0], ret[0])
	}

	// Get counter -> 5
	ret = call(t, "get_counter after inc", getCounter)
	if v, ok := ret[0].(int64); !ok || v != 5 {
		t.Fatalf("get_counter after inc: got %v (%T), want 5", ret[0], ret[0])
	}

	// Reset
	call(t, "set_counter(0) restore", setCounter, int64(0))
}

func TestModuleStateGlobalValue(t *testing.T) {
	setGlobal := load(t, moduleDir, "callable=set_global_value",
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8), ti(IDL.ANY)}, nil)
	getGlobal := load(t, moduleDir, "callable=get_global_value",
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)})

	// Set and get
	call(t, "set_global_value", setGlobal, "test_key", "test_value")
	ret := call(t, "get_global_value", getGlobal, "test_key")
	if v, ok := ret[0].(string); !ok || v != "test_value" {
		t.Fatalf("get_global_value(test_key): got %v (%T), want \"test_value\"", ret[0], ret[0])
	}
}

func TestModuleStateConstant(t *testing.T) {
	ff := load(t, moduleDir, "attribute=CONSTANT_FIVE_SECONDS,getter", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)})
	ret := call(t, "CONSTANT_FIVE_SECONDS", ff)
	if v, ok := ret[0].(int64); !ok || v != 5 {
		t.Fatalf("CONSTANT_FIVE_SECONDS: got %v (%T), want 5", ret[0], ret[0])
	}
}

// ==========================================================================
// args_and_signatures.py
// ==========================================================================

func TestArgsDefaultArgs(t *testing.T) {
	// Call with no args, expect defaults (1, "x", None)
	ff := load(t, moduleDir, "callable=default_args", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY), ti(IDL.ANY), ti(IDL.ANY)})
	ret := call(t, "default_args()", ff)
	if v, ok := ret[0].(int64); !ok || v != 1 {
		t.Fatalf("default_args()[0]: got %v (%T), want 1", ret[0], ret[0])
	}
	if v, ok := ret[1].(string); !ok || v != "x" {
		t.Fatalf("default_args()[1]: got %v (%T), want \"x\"", ret[1], ret[1])
	}
	if ret[2] != nil {
		t.Fatalf("default_args()[2]: got %v (%T), want nil", ret[2], ret[2])
	}
}

func TestArgsOverload(t *testing.T) {
	ff := load(t, moduleDir, "callable=overload",
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)},
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)})

	// int -> value + 1
	ret := call(t, "overload(int)", ff, int64(5))
	if v, ok := ret[0].(int64); !ok || v != 6 {
		t.Fatalf("overload(5): got %v (%T), want 6", ret[0], ret[0])
	}

	// str -> upper
	ret = call(t, "overload(str)", ff, "hello")
	if v, ok := ret[0].(string); !ok || v != "HELLO" {
		t.Fatalf("overload(\"hello\"): got %v (%T), want \"HELLO\"", ret[0], ret[0])
	}
}

// ==========================================================================
// single_file_module.py
// ==========================================================================

func TestSingleFileHelloWorld(t *testing.T) {
	ff := load(t, moduleFile, "callable=hello_world", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	ret := call(t, "single_file hello_world", ff)
	if v, ok := ret[0].(string); !ok || !strings.Contains(v, "Hello World") {
		t.Fatalf("single_file hello_world: got %q, want string containing \"Hello World\"", ret[0])
	}
}

func TestSingleFileReturnNull(t *testing.T) {
	ff := load(t, moduleFile, "callable=return_null", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.NULL)})
	ret := call(t, "single_file return_null", ff)
	if ret[0] != nil {
		t.Fatalf("single_file return_null: got %v (%T), want nil", ret[0], ret[0])
	}
}

func TestSingleFileSomeClass(t *testing.T) {
	// Get class
	getClass := load(t, moduleFile, "attribute=SomeClass,getter", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	classRet := call(t, "single_file SomeClass getter", getClass)

	// Create instance
	newEntity := load(t, moduleFile, "callable=SomeClass.__new__",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "SomeClass.__new__", newEntity, classRet[0])
	instance := instanceRet[0]

	initEntity := load(t, moduleFile, "callable=SomeClass.__init__,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)}, nil)
	call(t, "SomeClass.__init__", initEntity, instance, "sf_test")

	// Call .print()
	printEntity := load(t, moduleFile, "callable=SomeClass.print,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	printRet := call(t, "SomeClass.print", printEntity, instance)
	if v, ok := printRet[0].(string); !ok || v != "Hello from SomeClass sf_test" {
		t.Fatalf("single_file SomeClass.print: got %q, want \"Hello from SomeClass sf_test\"", printRet[0])
	}
}

func TestSingleFileTestMap(t *testing.T) {
	// Get class
	getClass := load(t, moduleFile, "attribute=TestMap,getter", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	classRet := call(t, "single_file TestMap getter", getClass)

	// Create instance
	newEntity := load(t, moduleFile, "callable=TestMap.__new__",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "TestMap.__new__", newEntity, classRet[0])
	instance := instanceRet[0]

	initEntity := load(t, moduleFile, "callable=TestMap.__init__,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)}, nil)
	call(t, "TestMap.__init__", initEntity, instance)

	// Set/Get/Contains
	setEntity := load(t, moduleFile, "callable=TestMap.set,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8), ti(IDL.ANY)}, nil)
	call(t, "TestMap.set", setEntity, instance, "k", int64(99))

	containsEntity := load(t, moduleFile, "callable=TestMap.contains,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.BOOL)})
	ret := call(t, "TestMap.contains(k)", containsEntity, instance, "k")
	if v, ok := ret[0].(bool); !ok || !v {
		t.Fatalf("single_file TestMap.contains(k): got %v, want true", ret[0])
	}

	getEntity := load(t, moduleFile, "callable=TestMap.get,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)})
	ret = call(t, "TestMap.get(k)", getEntity, instance, "k")
	if v, ok := ret[0].(int64); !ok || v != 99 {
		t.Fatalf("single_file TestMap.get(k): got %v (%T), want 99", ret[0], ret[0])
	}
}
