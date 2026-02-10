package call_java_jni

// Build requirements:
// Set JAVA_HOME to your JDK installation, then:
//   CGO_CFLAGS="-I$JAVA_HOME/include -I$JAVA_HOME/include/<platform>"
//   CGO_LDFLAGS="-L$JAVA_HOME/lib/server -ljvm"
// where <platform> is "win32", "linux", or "darwin".
//
// Windows example (PowerShell):
//   $env:CGO_CFLAGS = "-I$env:JAVA_HOME\include -I$env:JAVA_HOME\include\win32"
//   $env:CGO_LDFLAGS = "-L$env:JAVA_HOME\lib -L$env:JAVA_HOME\lib\server -ljvm"

/*
#cgo windows CFLAGS: -IC:/PROGRA~1/OpenJDK/JDK-22~1.2/include -IC:/PROGRA~1/OpenJDK/JDK-22~1.2/include/win32
#cgo windows LDFLAGS: -LC:/PROGRA~1/OpenJDK/JDK-22~1.2/lib -LC:/PROGRA~1/OpenJDK/JDK-22~1.2/lib/server -ljvm
#cgo !windows CFLAGS: -I${JAVA_HOME}/include -I${JAVA_HOME}/include/linux
#cgo !windows LDFLAGS: -L${JAVA_HOME}/lib/server -ljvm

#include <jni.h>
#include <stdlib.h>
#include <string.h>

// ---------------------------------------------------------------------------
// Global JVM state
// ---------------------------------------------------------------------------

static JavaVM* g_jvm = NULL;
static JNIEnv* g_env = NULL;

// Class and method references (cached after init)
static jclass g_core_cls = NULL;
static jclass g_someclass_cls = NULL;
static jclass g_arrayfunctions_cls = NULL;

static jmethodID g_waitABit = NULL;
static jmethodID g_divIntegers = NULL;
static jmethodID g_joinStrings = NULL;
static jmethodID g_returnsAnError = NULL;
static jmethodID g_callCallbackAdd = NULL;
static jmethodID g_someclass_ctor = NULL;
static jmethodID g_someclass_print = NULL;
static jmethodID g_sumRaggedArray = NULL;

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

// Returns a malloc'd error string, or NULL on success.
// Caller must free the returned string.
static char* jni_get_error(void) {
	if (!g_env) return strdup("JNI env is NULL");
	if (!(*g_env)->ExceptionCheck(g_env)) return NULL;

	jthrowable exc = (*g_env)->ExceptionOccurred(g_env);
	(*g_env)->ExceptionClear(g_env);

	jclass cls = (*g_env)->GetObjectClass(g_env, exc);
	jmethodID getMessage = (*g_env)->GetMethodID(g_env, cls, "getMessage", "()Ljava/lang/String;");
	jstring msg = (jstring)(*g_env)->CallObjectMethod(g_env, exc, getMessage);

	const char* msgChars = (*g_env)->GetStringUTFChars(g_env, msg, NULL);
	char* result = strdup(msgChars);
	(*g_env)->ReleaseStringUTFChars(g_env, msg, msgChars);

	(*g_env)->DeleteLocalRef(g_env, exc);
	(*g_env)->DeleteLocalRef(g_env, cls);
	(*g_env)->DeleteLocalRef(g_env, msg);

	return result;
}

// ---------------------------------------------------------------------------
// JVM lifecycle
// ---------------------------------------------------------------------------

// Initialize JVM with classpath. Returns error string or NULL.
static char* jvm_initialize(const char* classpath) {
	JavaVMInitArgs vm_args;
	JavaVMOption options[1];

	// Build classpath option
	size_t cp_len = strlen("-Djava.class.path=") + strlen(classpath) + 1;
	char* cp_opt = (char*)malloc(cp_len);
	snprintf(cp_opt, cp_len, "-Djava.class.path=%s", classpath);

	options[0].optionString = cp_opt;
	vm_args.version = JNI_VERSION_1_8;
	vm_args.nOptions = 1;
	vm_args.options = options;
	vm_args.ignoreUnrecognized = JNI_FALSE;

	jint rc = JNI_CreateJavaVM(&g_jvm, (void**)&g_env, &vm_args);
	free(cp_opt);

	if (rc != JNI_OK) {
		char buf[64];
		snprintf(buf, sizeof(buf), "JNI_CreateJavaVM failed with code %d", (int)rc);
		return strdup(buf);
	}

	return NULL;
}

static void jvm_destroy(void) {
	if (g_jvm) {
		(*g_jvm)->DestroyJavaVM(g_jvm);
		g_jvm = NULL;
		g_env = NULL;
	}
}

// Returns JVM version string
static const char* jvm_version(void) {
	return "JNI";
}

// ---------------------------------------------------------------------------
// Load classes and cache method IDs
// ---------------------------------------------------------------------------

static char* jni_load_classes(void) {
	// CoreFunctions
	g_core_cls = (*g_env)->FindClass(g_env, "guest/CoreFunctions");
	if (!g_core_cls) {
		(*g_env)->ExceptionClear(g_env);
		return strdup("Cannot find class guest.CoreFunctions");
	}
	g_core_cls = (jclass)(*g_env)->NewGlobalRef(g_env, g_core_cls);

	g_waitABit = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "waitABit", "(J)V");
	if (!g_waitABit) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find waitABit"); }

	g_divIntegers = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "divIntegers", "(JJ)D");
	if (!g_divIntegers) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find divIntegers"); }

	g_joinStrings = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "joinStrings", "([Ljava/lang/String;)Ljava/lang/String;");
	if (!g_joinStrings) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find joinStrings"); }

	g_returnsAnError = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "returnsAnError", "()V");
	if (!g_returnsAnError) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find returnsAnError"); }

	g_callCallbackAdd = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "callCallbackAdd", "(Ljava/util/function/IntBinaryOperator;)I");
	if (!g_callCallbackAdd) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find callCallbackAdd"); }

	// SomeClass
	g_someclass_cls = (*g_env)->FindClass(g_env, "guest/SomeClass");
	if (!g_someclass_cls) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find guest.SomeClass"); }
	g_someclass_cls = (jclass)(*g_env)->NewGlobalRef(g_env, g_someclass_cls);

	g_someclass_ctor = (*g_env)->GetMethodID(g_env, g_someclass_cls, "<init>", "(Ljava/lang/String;)V");
	if (!g_someclass_ctor) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find SomeClass(String)"); }

	g_someclass_print = (*g_env)->GetMethodID(g_env, g_someclass_cls, "print", "()Ljava/lang/String;");
	if (!g_someclass_print) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find SomeClass.print"); }

	// ArrayFunctions
	g_arrayfunctions_cls = (*g_env)->FindClass(g_env, "guest/ArrayFunctions");
	if (!g_arrayfunctions_cls) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find guest.ArrayFunctions"); }
	g_arrayfunctions_cls = (jclass)(*g_env)->NewGlobalRef(g_env, g_arrayfunctions_cls);

	g_sumRaggedArray = (*g_env)->GetStaticMethodID(g_env, g_arrayfunctions_cls, "sumRaggedArray", "([[I)I");
	if (!g_sumRaggedArray) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find sumRaggedArray"); }

	return NULL;
}

// ---------------------------------------------------------------------------
// Benchmark functions (7 scenarios)
// ---------------------------------------------------------------------------

// Scenario 1: void call
static char* bench_void_call(void) {
	(*g_env)->CallStaticVoidMethod(g_env, g_core_cls, g_waitABit, (jlong)0);
	return jni_get_error();
}

// Scenario 2: primitive echo (divIntegers)
// Writes result to *out.
static char* bench_primitive_echo(double* out) {
	jdouble result = (*g_env)->CallStaticDoubleMethod(g_env, g_core_cls, g_divIntegers, (jlong)10, (jlong)2);
	char* err = jni_get_error();
	if (err) return err;
	*out = (double)result;
	return NULL;
}

// Scenario 3: string echo (joinStrings)
// Writes result to *out (caller must free).
static char* bench_string_echo(char** out) {
	// Build String[] {"hello", "world"}
	jclass strCls = (*g_env)->FindClass(g_env, "java/lang/String");
	jobjectArray arr = (*g_env)->NewObjectArray(g_env, 2, strCls, NULL);
	jstring s1 = (*g_env)->NewStringUTF(g_env, "hello");
	jstring s2 = (*g_env)->NewStringUTF(g_env, "world");
	(*g_env)->SetObjectArrayElement(g_env, arr, 0, s1);
	(*g_env)->SetObjectArrayElement(g_env, arr, 1, s2);

	jstring result = (jstring)(*g_env)->CallStaticObjectMethod(g_env, g_core_cls, g_joinStrings, arr);
	char* err = jni_get_error();
	if (err) {
		(*g_env)->DeleteLocalRef(g_env, strCls);
		(*g_env)->DeleteLocalRef(g_env, arr);
		(*g_env)->DeleteLocalRef(g_env, s1);
		(*g_env)->DeleteLocalRef(g_env, s2);
		return err;
	}

	const char* chars = (*g_env)->GetStringUTFChars(g_env, result, NULL);
	*out = strdup(chars);
	(*g_env)->ReleaseStringUTFChars(g_env, result, chars);

	(*g_env)->DeleteLocalRef(g_env, strCls);
	(*g_env)->DeleteLocalRef(g_env, arr);
	(*g_env)->DeleteLocalRef(g_env, s1);
	(*g_env)->DeleteLocalRef(g_env, s2);
	(*g_env)->DeleteLocalRef(g_env, result);

	return NULL;
}

// Scenario 4: array sum (sumRaggedArray with single-row int[][])
static char* bench_array_sum(int size, int* out) {
	// Build int[][]{int[size]{1, 2, ..., size}}
	jintArray innerArr = (*g_env)->NewIntArray(g_env, size);
	jint* elems = (*g_env)->GetIntArrayElements(g_env, innerArr, NULL);
	for (int i = 0; i < size; i++) {
		elems[i] = i + 1;
	}
	(*g_env)->ReleaseIntArrayElements(g_env, innerArr, elems, 0);

	jclass intArrCls = (*g_env)->FindClass(g_env, "[I");
	jobjectArray outerArr = (*g_env)->NewObjectArray(g_env, 1, intArrCls, NULL);
	(*g_env)->SetObjectArrayElement(g_env, outerArr, 0, innerArr);

	jint result = (*g_env)->CallStaticIntMethod(g_env, g_arrayfunctions_cls, g_sumRaggedArray, outerArr);
	char* err = jni_get_error();
	if (err) {
		(*g_env)->DeleteLocalRef(g_env, innerArr);
		(*g_env)->DeleteLocalRef(g_env, intArrCls);
		(*g_env)->DeleteLocalRef(g_env, outerArr);
		return err;
	}
	*out = (int)result;

	(*g_env)->DeleteLocalRef(g_env, innerArr);
	(*g_env)->DeleteLocalRef(g_env, intArrCls);
	(*g_env)->DeleteLocalRef(g_env, outerArr);

	return NULL;
}

// Scenario 5: object create + method call
static char* bench_object_method(char** out) {
	jstring name = (*g_env)->NewStringUTF(g_env, "bench");
	jobject instance = (*g_env)->NewObject(g_env, g_someclass_cls, g_someclass_ctor, name);
	char* err = jni_get_error();
	if (err) {
		(*g_env)->DeleteLocalRef(g_env, name);
		return err;
	}

	jstring result = (jstring)(*g_env)->CallObjectMethod(g_env, instance, g_someclass_print);
	err = jni_get_error();
	if (err) {
		(*g_env)->DeleteLocalRef(g_env, name);
		(*g_env)->DeleteLocalRef(g_env, instance);
		return err;
	}

	const char* chars = (*g_env)->GetStringUTFChars(g_env, result, NULL);
	*out = strdup(chars);
	(*g_env)->ReleaseStringUTFChars(g_env, result, chars);

	(*g_env)->DeleteLocalRef(g_env, name);
	(*g_env)->DeleteLocalRef(g_env, instance);
	(*g_env)->DeleteLocalRef(g_env, result);

	return NULL;
}

// Scenario 6: callback
// NOTE: JNI callback for IntBinaryOperator requires registering a native method
// on a Java proxy class. For the JNI benchmark, we use a simpler approach:
// pre-create a Java lambda that adds two ints and pass it.
// This measures the JNI overhead of passing a Java object to a Java method.
static jclass g_adder_cls = NULL;
static jmethodID g_adder_ctor = NULL;
static jobject g_adder_instance = NULL;

// We'll define a small Java class at runtime... actually, for simplicity,
// we create the adder via MethodHandle or use the existing guest module.
// The cleanest approach: create a Java-side IntBinaryOperator lambda using
// a helper method, then pass it. But that requires another Java helper.
//
// Instead, for the JNI baseline, we measure calling callCallbackAdd with
// a pre-created Java IntBinaryOperator instance. The callback itself stays
// in Java (no cross-language callback). This is the fair JNI comparison.

static char* init_callback_helper(void) {
	// We'll use a dynamic proxy approach. Actually, the simplest:
	// Create a class that implements IntBinaryOperator via an anonymous inner class
	// compiled into the JAR. But our JAR doesn't have one.
	//
	// Alternative: Use returnCallbackAdd() which returns an IntBinaryOperator
	// that does (a,b)->a+b. Then pass that to callCallbackAdd.
	// This measures: JNI call -> Java static method -> callback (Java-to-Java) -> return.

	jmethodID returnCallbackAdd = (*g_env)->GetStaticMethodID(g_env, g_core_cls,
		"returnCallbackAdd", "()Ljava/util/function/IntBinaryOperator;");
	if (!returnCallbackAdd) {
		(*g_env)->ExceptionClear(g_env);
		return strdup("Cannot find returnCallbackAdd");
	}

	jobject adder = (*g_env)->CallStaticObjectMethod(g_env, g_core_cls, returnCallbackAdd);
	char* err = jni_get_error();
	if (err) return err;

	g_adder_instance = (*g_env)->NewGlobalRef(g_env, adder);
	(*g_env)->DeleteLocalRef(g_env, adder);

	return NULL;
}

static char* bench_callback(int* out) {
	jint result = (*g_env)->CallStaticIntMethod(g_env, g_core_cls, g_callCallbackAdd, g_adder_instance);
	char* err = jni_get_error();
	if (err) return err;
	*out = (int)result;
	return NULL;
}

// Scenario 7: error propagation
static char* bench_error_propagation(void) {
	(*g_env)->CallStaticVoidMethod(g_env, g_core_cls, g_returnsAnError);
	if ((*g_env)->ExceptionCheck(g_env)) {
		(*g_env)->ExceptionClear(g_env);
		return NULL; // Expected error occurred
	}
	return strdup("expected exception but none was thrown");
}
*/
import "C"

import (
	"fmt"
	"runtime"
	"unsafe"
)

// ---------------------------------------------------------------------------
// Go wrapper functions (exported to test code, no cgo types leak)
// ---------------------------------------------------------------------------

// JVMInitialize starts the JVM with the given classpath.
func JVMInitialize(classpath string) error {
	runtime.LockOSThread()
	cpath := C.CString(classpath)
	defer C.free(unsafe.Pointer(cpath))

	cerr := C.jvm_initialize(cpath)
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return fmt.Errorf("JVM init: %s", msg)
	}
	return nil
}

// JVMDestroy shuts down the JVM.
func JVMDestroy() {
	C.jvm_destroy()
}

// JVMVersion returns the JVM interface version string.
func JVMVersion() string {
	return C.GoString(C.jvm_version())
}

// JNILoadClasses resolves Java class/method references.
func JNILoadClasses() error {
	cerr := C.jni_load_classes()
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return fmt.Errorf("JNI load classes: %s", msg)
	}
	return nil
}

// InitCallbackHelper creates the Java-side callback for scenario 6.
func InitCallbackHelper() error {
	cerr := C.init_callback_helper()
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return fmt.Errorf("init callback helper: %s", msg)
	}
	return nil
}

// BenchVoidCall executes scenario 1.
func BenchVoidCall() error {
	cerr := C.bench_void_call()
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return fmt.Errorf("%s", msg)
	}
	return nil
}

// BenchPrimitiveEcho executes scenario 2 and returns the result.
func BenchPrimitiveEcho() (float64, error) {
	var result C.double
	cerr := C.bench_primitive_echo(&result)
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return 0, fmt.Errorf("%s", msg)
	}
	return float64(result), nil
}

// BenchStringEcho executes scenario 3 and returns the result.
func BenchStringEcho() (string, error) {
	var cstr *C.char
	cerr := C.bench_string_echo(&cstr)
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return "", fmt.Errorf("%s", msg)
	}
	result := C.GoString(cstr)
	C.free(unsafe.Pointer(cstr))
	return result, nil
}

// BenchArraySum executes scenario 4 and returns the sum.
func BenchArraySum(size int) (int, error) {
	var result C.int
	cerr := C.bench_array_sum(C.int(size), &result)
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return 0, fmt.Errorf("%s", msg)
	}
	return int(result), nil
}

// BenchObjectMethod executes scenario 5 and returns the print output.
func BenchObjectMethod() (string, error) {
	var cstr *C.char
	cerr := C.bench_object_method(&cstr)
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return "", fmt.Errorf("%s", msg)
	}
	result := C.GoString(cstr)
	C.free(unsafe.Pointer(cstr))
	return result, nil
}

// BenchCallback executes scenario 6.
func BenchCallback() (int, error) {
	var result C.int
	cerr := C.bench_callback(&result)
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return 0, fmt.Errorf("%s", msg)
	}
	return int(result), nil
}

// BenchErrorPropagation executes scenario 7.
func BenchErrorPropagation() error {
	cerr := C.bench_error_propagation()
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return fmt.Errorf("%s", msg)
	}
	return nil
}
