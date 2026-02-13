package call_java

import (
	"fmt"
	"math"
	"os"
	"path/filepath"
	"strings"
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
	jarPath   string
)

func reloadRuntimeModule() error {
	if metaffiRT != nil {
		_ = metaffiRT.ReleaseRuntimePlugin()
		metaffiRT = nil
		module = nil
	}

	metaffiRT = api.NewMetaFFIRuntime("jvm")
	if err := metaffiRT.LoadRuntimePlugin(); err != nil {
		return fmt.Errorf("failed to load jvm runtime plugin: %w", err)
	}

	mod, err := metaffiRT.LoadModule(jarPath)
	if err != nil {
		_ = metaffiRT.ReleaseRuntimePlugin()
		metaffiRT = nil
		return fmt.Errorf("failed to load module %s: %w", jarPath, err)
	}
	module = mod

	return nil
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

	// Path to guest_java.jar
	jarPath = filepath.Join(srcRoot, "sdk", "test_modules", "guest_modules", "java", "test_bin", "guest_java.jar")

	if err := reloadRuntimeModule(); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
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

// tiAlias creates a MetaFFITypeInfo with an alias (e.g., Java interface/class).
func tiAlias(t IDL.MetaFFIType, alias string) IDL.MetaFFITypeInfo {
	return IDL.MetaFFITypeInfo{StringType: t, Alias: alias}
}

// load loads an entity; fatals immediately on error (fail-fast).
func load(t *testing.T, entityPath string, params []IDL.MetaFFITypeInfo, retvals []IDL.MetaFFITypeInfo) func(...interface{}) ([]interface{}, error) {
	t.Helper()
	ff, err := module.LoadWithInfo(entityPath, params, retvals)
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
func assertFloat64(t *testing.T, name string, got, want, epsilon float64) {
	t.Helper()
	if math.Abs(got-want) > epsilon {
		t.Fatalf("%s: got %v, want %v (epsilon %v)", name, got, want, epsilon)
	}
}

// ==========================================================================
// CoreFunctions
// ==========================================================================

func TestCoreHelloWorld(t *testing.T) {
	ff := load(t, "class=guest.CoreFunctions,callable=helloWorld", nil, []IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	ret := call(t, "helloWorld", ff)
	if v, ok := ret[0].(string); !ok || v != "Hello World, from Java" {
		t.Fatalf("helloWorld: got %v (%T), want \"Hello World, from Java\"", ret[0], ret[0])
	}
}

func TestCoreDivIntegers(t *testing.T) {
	ff := load(t, "class=guest.CoreFunctions,callable=divIntegers",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64), ti(IDL.INT64)},
		[]IDL.MetaFFITypeInfo{ti(IDL.FLOAT64)})

	ret := call(t, "divIntegers(10,2)", ff, int64(10), int64(2))
	assertFloat64(t, "divIntegers(10,2)", ret[0].(float64), 5.0, 1e-10)
}

func TestCoreJoinStrings(t *testing.T) {
	ff := load(t, "class=guest.CoreFunctions,callable=joinStrings",
		[]IDL.MetaFFITypeInfo{tiArray(IDL.STRING8_ARRAY, 1)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})

	ret := call(t, "joinStrings", ff, []string{"a", "b", "c"})
	if v, ok := ret[0].(string); !ok || v != "a,b,c" {
		t.Fatalf("joinStrings: got %v (%T), want \"a,b,c\"", ret[0], ret[0])
	}
}

func TestCoreWaitABit(t *testing.T) {
	ff := load(t, "class=guest.CoreFunctions,callable=waitABit",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT64)}, nil)
	call(t, "waitABit", ff, int64(1))
}

func TestCoreReturnNull(t *testing.T) {
	ff := load(t, "class=guest.CoreFunctions,callable=returnNull", nil, []IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	ret := call(t, "returnNull", ff)
	if ret[0] != nil {
		t.Fatalf("returnNull: got %v (%T), want nil", ret[0], ret[0])
	}
}

func TestCoreReturnsAnError(t *testing.T) {
	ff := load(t, "class=guest.CoreFunctions,callable=returnsAnError", nil, nil)
	callExpectError(t, "returnsAnError", ff, "InvocationTargetException")
}

func TestCoreCallCallbackAdd(t *testing.T) {
	adapter := load(t, "class=metaffi.api.accessor.CallbackAdapters,callable=asInterface",
		[]IDL.MetaFFITypeInfo{ti(IDL.CALLABLE), ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})

	adder := func(a, b int32) int32 { return a + b }
	adapterRet := call(t, "CallbackAdapters.asInterface", adapter, adder, "java.util.function.IntBinaryOperator")
	if adapterRet[0] == nil {
		t.Fatal("CallbackAdapters.asInterface: got nil proxy")
	}
	proxy := adapterRet[0]

	ff := load(t, "class=guest.CoreFunctions,callable=callCallbackAdd",
		[]IDL.MetaFFITypeInfo{tiAlias(IDL.HANDLE, "java.util.function.IntBinaryOperator")},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})

	ret := call(t, "callCallbackAdd", ff, proxy)
	if v, ok := ret[0].(int32); !ok || v != 3 {
		t.Fatalf("callCallbackAdd: got %v (%T), want 3", ret[0], ret[0])
	}
}

func TestCoreReturnCallbackAdd(t *testing.T) {
	ff := load(t, "class=guest.CoreFunctions,callable=returnCallbackAdd", nil,
		[]IDL.MetaFFITypeInfo{tiAlias(IDL.HANDLE, "java.util.function.IntBinaryOperator")})

	ret := call(t, "returnCallbackAdd", ff)
	if ret[0] == nil {
		t.Fatal("returnCallbackAdd: got nil callable")
	}

	apply := load(t, "class=java.util.function.IntBinaryOperator,callable=applyAsInt,instance_required",
		[]IDL.MetaFFITypeInfo{
			tiAlias(IDL.HANDLE, "java.util.function.IntBinaryOperator"),
			ti(IDL.INT32),
			ti(IDL.INT32),
		},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})

	result := call(t, "IntBinaryOperator.applyAsInt", apply, ret[0], int32(3), int32(4))
	if v, ok := result[0].(int32); !ok || v != 7 {
		t.Fatalf("applyAsInt(3, 4): got %v (%T), want 7", result[0], result[0])
	}
}

func TestCoreReturnMultipleReturnValues(t *testing.T) {
	// Returns Object[]{1, "string", 3.0, null, byte[]{1,2,3}, SomeClass()}
	ff := load(t, "class=guest.CoreFunctions,callable=returnMultipleReturnValues", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.ANY_ARRAY, 1)})

	ret := call(t, "returnMultipleReturnValues", ff)
	if ret[0] == nil {
		t.Fatal("returnMultipleReturnValues: got nil")
	}
}

func TestCoreReturnAny(t *testing.T) {
	ff := load(t, "class=guest.CoreFunctions,callable=returnAny",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)},
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)})

	// which=0 -> Integer(1)
	ret := call(t, "returnAny(0)", ff, int32(0))
	if ret[0] == nil {
		t.Fatal("returnAny(0): got nil")
	}

	// which=1 -> "string"
	ret = call(t, "returnAny(1)", ff, int32(1))
	if v, ok := ret[0].(string); !ok || v != "string" {
		t.Fatalf("returnAny(1): got %v (%T), want \"string\"", ret[0], ret[0])
	}

	// which=999 -> null
	ret = call(t, "returnAny(999)", ff, int32(999))
	if ret[0] != nil {
		t.Fatalf("returnAny(999): got %v (%T), want nil", ret[0], ret[0])
	}
}

func TestCoreAcceptsAny(t *testing.T) {
	ff := load(t, "class=guest.CoreFunctions,callable=acceptsAny",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32), ti(IDL.ANY)}, nil)

	// which=1, val="string"
	call(t, "acceptsAny(1, string)", ff, int32(1), "string")

	// which=3, val=null
	call(t, "acceptsAny(3, null)", ff, int32(3), nil)
}

// ==========================================================================
// SomeClass
// ==========================================================================

func TestSomeClassCreateDefaultAndPrint(t *testing.T) {
	// Constructor with no args -> name = "some"
	newDefault := load(t, "class=guest.SomeClass,callable=<init>",
		nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "SomeClass()", newDefault)
	instance := instanceRet[0]

	// Call .print()
	printEntity := load(t, "class=guest.SomeClass,callable=print,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	printRet := call(t, "SomeClass.print", printEntity, instance)
	if v, ok := printRet[0].(string); !ok || v != "Hello from SomeClass some" {
		t.Fatalf("SomeClass.print: got %q, want \"Hello from SomeClass some\"", printRet[0])
	}
}

func TestSomeClassCreateWithNameAndPrint(t *testing.T) {
	// Constructor with name arg
	newWithName := load(t, "class=guest.SomeClass,callable=<init>",
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "SomeClass(name)", newWithName, "test_name")
	instance := instanceRet[0]

	// Call .print()
	printEntity := load(t, "class=guest.SomeClass,callable=print,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	printRet := call(t, "SomeClass.print", printEntity, instance)
	if v, ok := printRet[0].(string); !ok || v != "Hello from SomeClass test_name" {
		t.Fatalf("SomeClass.print: got %q, want \"Hello from SomeClass test_name\"", printRet[0])
	}
}

func TestSomeClassGetName(t *testing.T) {
	newWithName := load(t, "class=guest.SomeClass,callable=<init>",
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "SomeClass(name)", newWithName, "abc")
	instance := instanceRet[0]

	getName := load(t, "class=guest.SomeClass,callable=getName,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	ret := call(t, "SomeClass.getName", getName, instance)
	if v, ok := ret[0].(string); !ok || v != "abc" {
		t.Fatalf("SomeClass.getName: got %q, want \"abc\"", ret[0])
	}
}

// ==========================================================================
// TestMap
// ==========================================================================

func TestTestMapSetGetContains(t *testing.T) {
	// Create instance
	newMap := load(t, "class=guest.TestMap,callable=<init>",
		nil, []IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "TestMap()", newMap)
	instance := instanceRet[0]

	// Set
	setEntity := load(t, "class=guest.TestMap,callable=set,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8), ti(IDL.ANY)}, nil)
	call(t, "TestMap.set", setEntity, instance, "key1", int64(42))

	// Contains
	containsEntity := load(t, "class=guest.TestMap,callable=contains,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.BOOL)})
	containsRet := call(t, "TestMap.contains", containsEntity, instance, "key1")
	if v, ok := containsRet[0].(bool); !ok || !v {
		t.Fatalf("TestMap.contains(key1): got %v, want true", containsRet[0])
	}

	// Get
	getEntity := load(t, "class=guest.TestMap,callable=get,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)})
	getRet := call(t, "TestMap.get", getEntity, instance, "key1")
	if getRet[0] == nil {
		t.Fatal("TestMap.get(key1): got nil")
	}

	// Contains for non-existent key
	containsRet = call(t, "TestMap.contains(missing)", containsEntity, instance, "nonexistent")
	if v, ok := containsRet[0].(bool); !ok || v {
		t.Fatalf("TestMap.contains(nonexistent): got %v, want false", containsRet[0])
	}
}

func TestTestMapNameField(t *testing.T) {
	// Create instance
	newMap := load(t, "class=guest.TestMap,callable=<init>",
		nil, []IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "TestMap()", newMap)
	instance := instanceRet[0]

	// Get field "name"
	getNameField := load(t, "class=guest.TestMap,field=name,getter,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	ret := call(t, "TestMap.name getter", getNameField, instance)
	if v, ok := ret[0].(string); !ok || v != "name1" {
		t.Fatalf("TestMap.name: got %q, want \"name1\"", ret[0])
	}

	// Set field "name"
	setNameField := load(t, "class=guest.TestMap,field=name,setter,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)}, nil)
	call(t, "TestMap.name setter", setNameField, instance, "new_name")

	// Verify changed
	ret = call(t, "TestMap.name getter after set", getNameField, instance)
	if v, ok := ret[0].(string); !ok || v != "new_name" {
		t.Fatalf("TestMap.name after set: got %q, want \"new_name\"", ret[0])
	}
}

// ==========================================================================
// StaticState
// ==========================================================================

func TestStaticStateCounter(t *testing.T) {
	// Set counter to 0
	setCounter := load(t, "class=guest.StaticState,callable=setCounter",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)}, nil)
	call(t, "setCounter(0)", setCounter, int32(0))

	// Get counter -> 0
	getCounter := load(t, "class=guest.StaticState,callable=getCounter", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})
	ret := call(t, "getCounter", getCounter)
	if v, ok := ret[0].(int32); !ok || v != 0 {
		t.Fatalf("getCounter: got %v (%T), want 0", ret[0], ret[0])
	}

	// Increment by 5
	incCounter := load(t, "class=guest.StaticState,callable=incCounter",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})
	ret = call(t, "incCounter(5)", incCounter, int32(5))
	if v, ok := ret[0].(int32); !ok || v != 5 {
		t.Fatalf("incCounter(5): got %v (%T), want 5", ret[0], ret[0])
	}

	// Get counter -> 5
	ret = call(t, "getCounter after inc", getCounter)
	if v, ok := ret[0].(int32); !ok || v != 5 {
		t.Fatalf("getCounter after inc: got %v (%T), want 5", ret[0], ret[0])
	}

	// Reset
	call(t, "setCounter(0) restore", setCounter, int32(0))
}

func TestStaticStateConstant(t *testing.T) {
	// FIVE_SECONDS is a static final long = 5L
	ff := load(t, "class=guest.StaticState,field=FIVE_SECONDS,getter",
		nil, []IDL.MetaFFITypeInfo{ti(IDL.INT64)})
	ret := call(t, "FIVE_SECONDS", ff)
	if v, ok := ret[0].(int64); !ok || v != 5 {
		t.Fatalf("FIVE_SECONDS: got %v (%T), want 5", ret[0], ret[0])
	}
}

// ==========================================================================
// PrimitiveFunctions
// ==========================================================================

func TestPrimitivesAcceptsPrimitives(t *testing.T) {
	ff := load(t, "class=guest.PrimitiveFunctions,callable=acceptsPrimitives",
		[]IDL.MetaFFITypeInfo{
			ti(IDL.BOOL), ti(IDL.INT8), ti(IDL.INT16), ti(IDL.INT32),
			ti(IDL.INT64), ti(IDL.FLOAT32), ti(IDL.FLOAT64), ti(IDL.CHAR16),
		},
		[]IDL.MetaFFITypeInfo{tiArray(IDL.ANY_ARRAY, 1)})

	ret := call(t, "acceptsPrimitives", ff,
		true, int8(1), int16(2), int32(3), int64(4), float32(5.0), float64(6.0), 'a')
	if ret[0] == nil {
		t.Fatal("acceptsPrimitives: got nil")
	}
}

func TestPrimitivesEchoBytes(t *testing.T) {
	ff := load(t, "class=guest.PrimitiveFunctions,callable=echoBytes",
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT8_ARRAY, 1)},
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT8_ARRAY, 1)})

	input := []int8{1, 2, 3, 4, 5}
	ret := call(t, "echoBytes", ff, input)
	arr, ok := ret[0].([]int8)
	if !ok {
		t.Fatalf("echoBytes: unexpected type %T", ret[0])
	}
	if len(arr) != len(input) {
		t.Fatalf("echoBytes: len=%d, want %d", len(arr), len(input))
	}
	for i, v := range input {
		if arr[i] != v {
			t.Fatalf("echoBytes[%d]: got %d, want %d", i, arr[i], v)
		}
	}
}

func TestPrimitivesToUpper(t *testing.T) {
	ff := load(t, "class=guest.PrimitiveFunctions,callable=toUpper",
		[]IDL.MetaFFITypeInfo{ti(IDL.CHAR16)},
		[]IDL.MetaFFITypeInfo{ti(IDL.CHAR16)})

	ret := call(t, "toUpper('a')", ff, 'a')
	if ret[0] == nil {
		t.Fatal("toUpper: got nil")
	}
}

// ==========================================================================
// ArrayFunctions
// ==========================================================================

func TestArraysGetThreeBuffers(t *testing.T) {
	ff := load(t, "class=guest.ArrayFunctions,callable=getThreeBuffers", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT8_ARRAY, 2)})
	ret := call(t, "getThreeBuffers", ff)
	if ret[0] == nil {
		t.Fatal("getThreeBuffers: got nil")
	}
}

func TestArraysGetSomeClasses(t *testing.T) {
	ff := load(t, "class=guest.ArrayFunctions,callable=getSomeClasses", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.HANDLE_ARRAY, 1)})
	ret := call(t, "getSomeClasses", ff)
	if ret[0] == nil {
		t.Fatal("getSomeClasses: got nil")
	}
}

func TestArraysMake2d(t *testing.T) {
	ff := load(t, "class=guest.ArrayFunctions,callable=make2dArray", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT32_ARRAY, 2)})
	ret := call(t, "make2dArray", ff)
	arr, ok := ret[0].([][]int32)
	if !ok {
		t.Fatalf("make2dArray: unexpected type %T", ret[0])
	}
	if len(arr) != 2 || len(arr[0]) != 2 || len(arr[1]) != 2 {
		t.Fatalf("make2dArray: shape mismatch %v", arr)
	}
	if arr[0][0] != 1 || arr[0][1] != 2 || arr[1][0] != 3 || arr[1][1] != 4 {
		t.Fatalf("make2dArray: values mismatch %v", arr)
	}
}

func TestArraysMake3d(t *testing.T) {
	ff := load(t, "class=guest.ArrayFunctions,callable=make3dArray", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT32_ARRAY, 3)})
	ret := call(t, "make3dArray", ff)
	arr, ok := ret[0].([][][]int32)
	if !ok {
		t.Fatalf("make3dArray: unexpected type %T", ret[0])
	}
	if arr[0][0][0] != 1 || arr[0][1][0] != 2 || arr[1][0][0] != 3 || arr[1][1][0] != 4 {
		t.Fatalf("make3dArray: values mismatch %v", arr)
	}
}

func TestArraysMakeRagged(t *testing.T) {
	ff := load(t, "class=guest.ArrayFunctions,callable=makeRaggedArray", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT32_ARRAY, 2)})
	ret := call(t, "makeRaggedArray", ff)
	ragged, ok := ret[0].([][]int32)
	if !ok {
		t.Fatalf("makeRaggedArray: unexpected type %T", ret[0])
	}
	if len(ragged) != 3 {
		t.Fatalf("makeRaggedArray: len=%d, want 3", len(ragged))
	}
	if len(ragged[0]) != 3 || ragged[0][0] != 1 || ragged[0][1] != 2 || ragged[0][2] != 3 {
		t.Fatalf("makeRaggedArray[0]: %v", ragged[0])
	}
	if len(ragged[1]) != 1 || ragged[1][0] != 4 {
		t.Fatalf("makeRaggedArray[1]: %v", ragged[1])
	}
	if len(ragged[2]) != 2 || ragged[2][0] != 5 || ragged[2][1] != 6 {
		t.Fatalf("makeRaggedArray[2]: %v", ragged[2])
	}
}

func TestArraysSum3d(t *testing.T) {
	ff := load(t, "class=guest.ArrayFunctions,callable=sum3dArray",
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT32_ARRAY, 3)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})

	arr := [][][]int32{{{1}, {2}}, {{3}, {4}}}
	ret := call(t, "sum3dArray", ff, arr)
	if v, ok := ret[0].(int32); !ok || v != 10 {
		t.Fatalf("sum3dArray: got %v (%T), want 10", ret[0], ret[0])
	}
}

func TestArraysSum3dFromFactory(t *testing.T) {
	ff := load(t, "class=guest.ArrayFunctions,callable=sum3dArrayFromFactory", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})
	ret := call(t, "sum3dArrayFromFactory", ff)
	if v, ok := ret[0].(int32); !ok || v != 10 {
		t.Fatalf("sum3dArrayFromFactory: got %v (%T), want 10", ret[0], ret[0])
	}
}

func TestArraysSumRagged(t *testing.T) {
	ff := load(t, "class=guest.ArrayFunctions,callable=sumRaggedArray",
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT32_ARRAY, 2)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})

	arr := [][]int32{{1, 2, 3}, {4}, {5, 6}}
	ret := call(t, "sumRaggedArray", ff, arr)
	if v, ok := ret[0].(int32); !ok || v != 21 {
		t.Fatalf("sumRaggedArray: got %v (%T), want 21", ret[0], ret[0])
	}
}

func TestArraysExpectThreeBuffers(t *testing.T) {
	// First get the three buffers, then pass them back
	getBuffers := load(t, "class=guest.ArrayFunctions,callable=getThreeBuffers", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT8_ARRAY, 2)})
	ret := call(t, "getThreeBuffers", getBuffers)

	expectBuffers := load(t, "class=guest.ArrayFunctions,callable=expectThreeBuffers",
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT8_ARRAY, 2)}, nil)
	call(t, "expectThreeBuffers", expectBuffers, ret[0])
}

func TestArraysExpectThreeSomeClasses(t *testing.T) {
	getClasses := load(t, "class=guest.ArrayFunctions,callable=getSomeClasses", nil,
		[]IDL.MetaFFITypeInfo{tiArray(IDL.HANDLE_ARRAY, 1)})
	ret := call(t, "getSomeClasses", getClasses)

	expectClasses := load(t, "class=guest.ArrayFunctions,callable=expectThreeSomeClasses",
		[]IDL.MetaFFITypeInfo{tiArray(IDL.HANDLE_ARRAY, 1)}, nil)
	call(t, "expectThreeSomeClasses", expectClasses, ret[0])
}

// ==========================================================================
// EnumTypes
// ==========================================================================

func TestEnumGetColor(t *testing.T) {
	ff := load(t, "class=guest.EnumTypes,callable=getColor",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})

	ret := call(t, "getColor(0)", ff, int32(0))
	if ret[0] == nil {
		t.Fatal("getColor(0): got nil (expected RED handle)")
	}
}

func TestEnumColorName(t *testing.T) {
	getColor := load(t, "class=guest.EnumTypes,callable=getColor",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	greenHandle := call(t, "getColor(1)", getColor, int32(1))[0]

	colorName := load(t, "class=guest.EnumTypes,callable=colorName",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	ret := call(t, "colorName(GREEN)", colorName, greenHandle)
	if v, ok := ret[0].(string); !ok || v != "GREEN" {
		t.Fatalf("colorName(GREEN): got %q, want \"GREEN\"", ret[0])
	}
}

// ==========================================================================
// OverloadExamples
// ==========================================================================

func TestOverloadIntAdd(t *testing.T) {
	newOverload := load(t, "class=guest.OverloadExamples,callable=<init>",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	instanceRet := call(t, "OverloadExamples(2)", newOverload, int32(2))
	instance := instanceRet[0]

	// getValue
	getValue := load(t, "class=guest.OverloadExamples,callable=getValue,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})
	ret := call(t, "getValue", getValue, instance)
	if v, ok := ret[0].(int32); !ok || v != 2 {
		t.Fatalf("getValue: got %v (%T), want 2", ret[0], ret[0])
	}
}

// ==========================================================================
// NestedTypes
// ==========================================================================

func TestNestedMakeInner(t *testing.T) {
	makeInner := load(t, "class=guest.NestedTypes,callable=makeInner",
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	ret := call(t, "makeInner(5)", makeInner, int32(5))
	innerHandle := ret[0]
	if innerHandle == nil {
		t.Fatal("makeInner: got nil")
	}

	// Call getValue on the inner
	getValue := load(t, "class=guest.NestedTypes$Inner,callable=getValue,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})
	ret = call(t, "Inner.getValue", getValue, innerHandle)
	if v, ok := ret[0].(int32); !ok || v != 5 {
		t.Fatalf("Inner.getValue: got %v (%T), want 5", ret[0], ret[0])
	}
}

// ==========================================================================
// Interfaces
// ==========================================================================

func TestInterfacesCallGreeter(t *testing.T) {
	// Create a SimpleGreeter instance
	newGreeter := load(t, "class=guest.Interfaces$SimpleGreeter,callable=<init>",
		nil, []IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	greeterRet := call(t, "SimpleGreeter()", newGreeter)
	greeter := greeterRet[0]

	// Call callGreeter(greeter, "Bob")
	callGreeter := load(t, "class=guest.Interfaces,callable=callGreeter",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	ret := call(t, "callGreeter", callGreeter, greeter, "Bob")
	if v, ok := ret[0].(string); !ok || v != "Hello Bob" {
		t.Fatalf("callGreeter: got %q, want \"Hello Bob\"", ret[0])
	}
}

// ==========================================================================
// GenericBox
// ==========================================================================

func TestGenericBox(t *testing.T) {
	// Create GenericBox<String>("x")
	newBox := load(t, "class=guest.GenericBox,callable=<init>",
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	boxRet := call(t, "GenericBox(\"x\")", newBox, "x")
	box := boxRet[0]

	// Call .get()
	getVal := load(t, "class=guest.GenericBox,callable=get,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.ANY)})
	ret := call(t, "GenericBox.get", getVal, box)
	if v, ok := ret[0].(string); !ok || v != "x" {
		t.Fatalf("GenericBox.get: got %v (%T), want \"x\"", ret[0], ret[0])
	}

	// Call .set("y")
	setVal := load(t, "class=guest.GenericBox,callable=set,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE), ti(IDL.ANY)}, nil)
	call(t, "GenericBox.set(\"y\")", setVal, box, "y")

	// Verify changed
	ret = call(t, "GenericBox.get after set", getVal, box)
	if v, ok := ret[0].(string); !ok || v != "y" {
		t.Fatalf("GenericBox.get after set: got %v (%T), want \"y\"", ret[0], ret[0])
	}
}

// ==========================================================================
// VarargsExamples
// ==========================================================================

func TestVarargsSum(t *testing.T) {
	// varargs int... is passed as int[]
	ff := load(t, "class=guest.VarargsExamples,callable=sum",
		[]IDL.MetaFFITypeInfo{tiArray(IDL.INT32_ARRAY, 1)},
		[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})

	ret := call(t, "sum(1,2,3)", ff, []int32{1, 2, 3})
	if v, ok := ret[0].(int32); !ok || v != 6 {
		t.Fatalf("sum: got %v (%T), want 6", ret[0], ret[0])
	}
}

func TestVarargsJoin(t *testing.T) {
	ff := load(t, "class=guest.VarargsExamples,callable=join",
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8), tiArray(IDL.STRING8_ARRAY, 1)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})

	ret := call(t, "join(\"p\", \"a\", \"b\")", ff, "p", []string{"a", "b"})
	if v, ok := ret[0].(string); !ok || v != "p:a:b" {
		t.Fatalf("join: got %q, want \"p:a:b\"", ret[0])
	}
}

// ==========================================================================
// Errors
// ==========================================================================

func TestErrorsThrowRuntime(t *testing.T) {
	ff := load(t, "class=guest.Errors,callable=throwRuntime", nil, nil)
	callExpectError(t, "throwRuntime", ff, "Error")
}

func TestErrorsThrowChecked(t *testing.T) {
	ff := load(t, "class=guest.Errors,callable=throwChecked",
		[]IDL.MetaFFITypeInfo{ti(IDL.BOOL)}, nil)
	callExpectError(t, "throwChecked(true)", ff, "IO error", true)

	// doThrow=false -> no error
	call(t, "throwChecked(false)", ff, false)
}

func TestErrorsReturnErrorString(t *testing.T) {
	ff := load(t, "class=guest.Errors,callable=returnErrorString",
		[]IDL.MetaFFITypeInfo{ti(IDL.BOOL)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})

	ret := call(t, "returnErrorString(true)", ff, true)
	if v, ok := ret[0].(string); !ok || v != "ok" {
		t.Fatalf("returnErrorString(true): got %q, want \"ok\"", ret[0])
	}

	ret = call(t, "returnErrorString(false)", ff, false)
	if v, ok := ret[0].(string); !ok || v != "error" {
		t.Fatalf("returnErrorString(false): got %q, want \"error\"", ret[0])
	}
}

// ==========================================================================
// Callbacks
// ==========================================================================

func TestCallbacksCallTransformer(t *testing.T) {
	returnTransformer := load(t, "class=guest.Callbacks,callable=returnTransformer",
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{tiAlias(IDL.HANDLE, "guest.Callbacks.StringTransformer")})

	ff := load(t, "class=guest.Callbacks,callable=callTransformer",
		[]IDL.MetaFFITypeInfo{tiAlias(IDL.HANDLE, "guest.Callbacks.StringTransformer"), ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})

	transformerRet := call(t, "returnTransformer(\"_x\")", returnTransformer, "_x")
	if transformerRet[0] == nil {
		t.Fatal("returnTransformer(\"_x\"): got nil transformer")
	}

	ret := call(t, "callTransformer", ff, transformerRet[0], "a")
	if v, ok := ret[0].(string); !ok || v != "a_x" {
		t.Fatalf("callTransformer: got %q, want \"a_x\"", ret[0])
	}
}

func TestCallbacksReturnTransformer(t *testing.T) {
	ff := load(t, "class=guest.Callbacks,callable=returnTransformer",
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{tiAlias(IDL.HANDLE, "guest.Callbacks.StringTransformer")})

	ret := call(t, "returnTransformer(\"_y\")", ff, "_y")
	if ret[0] == nil {
		t.Fatal("returnTransformer: got nil callable")
	}

	transform := load(t, "class=guest.Callbacks.StringTransformer,callable=transform,instance_required",
		[]IDL.MetaFFITypeInfo{tiAlias(IDL.HANDLE, "guest.Callbacks.StringTransformer"), ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})

	result := call(t, "StringTransformer.transform", transform, ret[0], "b")
	if v, ok := result[0].(string); !ok || v != "b_y" {
		t.Fatalf("transform(\"b\"): got %v (%T), want \"b_y\"", result[0], result[0])
	}
}

// ==========================================================================
// CollectionFunctions (returned as handles)
// ==========================================================================

func TestCollectionsMakeStringList(t *testing.T) {
	ff := load(t, "class=guest.CollectionFunctions,callable=makeStringList", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	ret := call(t, "makeStringList", ff)
	if ret[0] == nil {
		t.Fatal("makeStringList: got nil")
	}
}

func TestCollectionsMakeStringIntMap(t *testing.T) {
	ff := load(t, "class=guest.CollectionFunctions,callable=makeStringIntMap", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	ret := call(t, "makeStringIntMap", ff)
	if ret[0] == nil {
		t.Fatal("makeStringIntMap: got nil")
	}
}

func TestCollectionsBigInteger(t *testing.T) {
	ff := load(t, "class=guest.CollectionFunctions,callable=bigIntegerValue", nil,
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	ret := call(t, "bigIntegerValue", ff)
	if ret[0] == nil {
		t.Fatal("bigIntegerValue: got nil")
	}
}

// ==========================================================================
// AutoCloseableResource
// ==========================================================================

func TestAutoCloseableResource(t *testing.T) {
	newRes := load(t, "class=guest.AutoCloseableResource,callable=<init>",
		nil, []IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})
	resRet := call(t, "AutoCloseableResource()", newRes)
	res := resRet[0]

	// isClosed -> false
	isClosed := load(t, "class=guest.AutoCloseableResource,callable=isClosed,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
		[]IDL.MetaFFITypeInfo{ti(IDL.BOOL)})
	ret := call(t, "isClosed before close", isClosed, res)
	if v, ok := ret[0].(bool); !ok || v {
		t.Fatalf("isClosed before close: got %v, want false", ret[0])
	}

	// close()
	closeEntity := load(t, "class=guest.AutoCloseableResource,callable=close,instance_required",
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)}, nil)
	call(t, "close", closeEntity, res)

	// isClosed -> true
	ret = call(t, "isClosed after close", isClosed, res)
	if v, ok := ret[0].(bool); !ok || !v {
		t.Fatalf("isClosed after close: got %v, want true", ret[0])
	}
}

// ==========================================================================
// SubModule
// ==========================================================================

func TestSubModuleEcho(t *testing.T) {
	ff := load(t, "class=guest.sub.SubModule,callable=echo",
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)},
		[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})
	ret := call(t, "SubModule.echo", ff, "hello")
	if v, ok := ret[0].(string); !ok || v != "hello" {
		t.Fatalf("SubModule.echo: got %q, want \"hello\"", ret[0])
	}
}

// ==========================================================================
// OptionalFunctions (returned as handle since Optional<T> is not a MetaFFI type)
// ==========================================================================

func TestOptionalMaybeString(t *testing.T) {
	ff := load(t, "class=guest.OptionalFunctions,callable=maybeString",
		[]IDL.MetaFFITypeInfo{ti(IDL.BOOL)},
		[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})

	// present=true -> Optional containing "value"
	ret := call(t, "maybeString(true)", ff, true)
	if ret[0] == nil {
		t.Fatal("maybeString(true): got nil handle")
	}

	// present=false -> Optional.empty()
	ret = call(t, "maybeString(false)", ff, false)
	// Empty Optional is still an object, not null
	if ret[0] == nil {
		t.Fatal("maybeString(false): got nil handle (expected empty Optional handle)")
	}
}
