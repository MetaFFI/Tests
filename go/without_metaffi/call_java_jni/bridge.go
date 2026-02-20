package call_java_jni

// Build requirements:
// Set JAVA_HOME to your JDK installation. No -ljvm linking needed;
// jvm.dll / libjvm.so is loaded dynamically at runtime using
// LoadLibraryExW (Windows) or dlopen (Linux/macOS).

/*
#cgo windows CFLAGS: -IC:/PROGRA~1/OpenJDK/JDK-22~1.2/include -IC:/PROGRA~1/OpenJDK/JDK-22~1.2/include/win32
#cgo !windows CFLAGS: -I${JAVA_HOME}/include -I${JAVA_HOME}/include/linux

#include <jni.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <dlfcn.h>
#endif

// ---------------------------------------------------------------------------
// JNI_CreateJavaVM function pointer (loaded dynamically)
// ---------------------------------------------------------------------------

typedef jint (JNICALL *JNI_CreateJavaVM_t)(JavaVM**, void**, void*);
static JNI_CreateJavaVM_t pfn_JNI_CreateJavaVM = NULL;

#ifdef _WIN32
static HMODULE g_jvm_dll = NULL;
#else
static void* g_jvm_dl = NULL;
#endif

// Dynamically load jvm.dll/libjvm.so and resolve JNI_CreateJavaVM.
// Returns a malloc'd error string on failure, or NULL on success.
static char* load_jvm_library(void) {
	if (pfn_JNI_CreateJavaVM != NULL) {
		return NULL; // Already loaded
	}

	const char* java_home = getenv("JAVA_HOME");
	if (!java_home || java_home[0] == '\0') {
		return strdup("JAVA_HOME environment variable not set");
	}

#ifdef _WIN32
	// Convert JAVA_HOME to wide string
	wchar_t java_home_w[MAX_PATH];
	int wlen = MultiByteToWideChar(CP_UTF8, 0, java_home, -1, java_home_w, MAX_PATH);
	if (wlen == 0) {
		return strdup("Failed to convert JAVA_HOME to wide string");
	}

	// Add search directories for jvm.dll and its dependencies.
	// On Windows JDKs, jvm.dll can be in bin/server/ or lib/server/.
	wchar_t dir_buf[MAX_PATH];

	SetDefaultDllDirectories(LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);

	swprintf(dir_buf, MAX_PATH, L"%s\\bin", java_home_w);
	AddDllDirectory(dir_buf);

	swprintf(dir_buf, MAX_PATH, L"%s\\bin\\server", java_home_w);
	AddDllDirectory(dir_buf);

	swprintf(dir_buf, MAX_PATH, L"%s\\lib", java_home_w);
	AddDllDirectory(dir_buf);

	swprintf(dir_buf, MAX_PATH, L"%s\\lib\\server", java_home_w);
	AddDllDirectory(dir_buf);

	g_jvm_dll = LoadLibraryExW(L"jvm.dll", NULL, LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
	if (!g_jvm_dll) {
		char buf[512];
		snprintf(buf, sizeof(buf),
			"LoadLibraryExW(jvm.dll) failed (error %lu). JAVA_HOME=%s",
			GetLastError(), java_home);
		return strdup(buf);
	}

	pfn_JNI_CreateJavaVM = (JNI_CreateJavaVM_t)GetProcAddress(g_jvm_dll, "JNI_CreateJavaVM");
	if (!pfn_JNI_CreateJavaVM) {
		char buf[256];
		snprintf(buf, sizeof(buf),
			"GetProcAddress(JNI_CreateJavaVM) failed (error %lu)", GetLastError());
		return strdup(buf);
	}
#else
	// Linux/macOS: build path to libjvm.so and dlopen it
	char libjvm_path[512];
	snprintf(libjvm_path, sizeof(libjvm_path), "%s/lib/server/libjvm.so", java_home);

	g_jvm_dl = dlopen(libjvm_path, RTLD_NOW | RTLD_GLOBAL);
	if (!g_jvm_dl) {
		char buf[1024];
		snprintf(buf, sizeof(buf), "dlopen(%s) failed: %s", libjvm_path, dlerror());
		return strdup(buf);
	}

	pfn_JNI_CreateJavaVM = (JNI_CreateJavaVM_t)dlsym(g_jvm_dl, "JNI_CreateJavaVM");
	if (!pfn_JNI_CreateJavaVM) {
		char buf[256];
		snprintf(buf, sizeof(buf), "dlsym(JNI_CreateJavaVM) failed: %s", dlerror());
		return strdup(buf);
	}
#endif

	return NULL;
}

// ---------------------------------------------------------------------------
// Global JVM state
// ---------------------------------------------------------------------------

static JavaVM* g_jvm = NULL;
static JNIEnv* g_env = NULL;

// Class and method references (cached after init)
static jclass g_core_cls = NULL;
static jclass g_someclass_cls = NULL;
static jclass g_arrayfunctions_cls = NULL;

// Cached class refs used by hot-path benchmark functions.
// In real-world JNI code, these would be resolved once at init, not per-call.
static jclass g_string_cls = NULL;       // java/lang/String
static jclass g_int_array_cls = NULL;    // [I
static jclass g_object_cls = NULL;       // java/lang/Object
static jclass g_integer_cls = NULL;      // java/lang/Integer
static jclass g_double_cls = NULL;       // java/lang/Double
static jclass g_object_array_cls = NULL; // [Ljava/lang/Object;
static jmethodID g_int_valueOf = NULL;   // Integer.valueOf(int)
static jmethodID g_dbl_valueOf = NULL;   // Double.valueOf(double)

static jmethodID g_waitABit = NULL;
static jmethodID g_noOp = NULL;
static jmethodID g_divIntegers = NULL;
static jmethodID g_joinStrings = NULL;
static jmethodID g_returnsAnError = NULL;
static jmethodID g_callCallbackAdd = NULL;
static jmethodID g_echoAny = NULL;
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

// Workaround for Go issues #47576 and #58542:
// Go's Vectored Exception Handler (VEH) intercepts the JVM's internal SEH
// exceptions during JNI_CreateJavaVM and terminates the process. Both issues
// are still open as of Go 1.24.
//
// Solution: Run JNI_CreateJavaVM on a pure Windows thread (CreateThread).
// Go's VEH checks getg() — on a non-Go thread it returns NULL, so the VEH
// returns EXCEPTION_CONTINUE_SEARCH, letting the JVM's SEH handle its own
// internal exceptions. After JVM creation, we AttachCurrentThread to get a
// valid JNIEnv* on the calling (Go) thread.

#ifdef _WIN32

typedef struct {
	const char* classpath;
	char* error;       // malloc'd error string, or NULL on success
} jvm_init_args_t;

static DWORD WINAPI jvm_create_thread_proc(LPVOID param) {
	jvm_init_args_t* args = (jvm_init_args_t*)param;

	JavaVMInitArgs vm_args;
	JavaVMOption options[1];

	// Build classpath option
	size_t cp_len = strlen("-Djava.class.path=") + strlen(args->classpath) + 1;
	char* cp_opt = (char*)malloc(cp_len);
	snprintf(cp_opt, cp_len, "-Djava.class.path=%s", args->classpath);

	options[0].optionString = cp_opt;
	vm_args.version = JNI_VERSION_1_8;
	vm_args.nOptions = 1;
	vm_args.options = options;
	vm_args.ignoreUnrecognized = JNI_FALSE;

	// JNIEnv* from this thread is thread-local; we only need g_jvm.
	JNIEnv* init_env = NULL;
	jint rc = pfn_JNI_CreateJavaVM(&g_jvm, (void**)&init_env, &vm_args);
	free(cp_opt);

	if (rc != JNI_OK) {
		char buf[64];
		snprintf(buf, sizeof(buf), "JNI_CreateJavaVM failed with code %d", (int)rc);
		args->error = strdup(buf);
	} else {
		args->error = NULL;
	}

	return 0;
}

#endif // _WIN32

// Initialize JVM with classpath. Returns error string or NULL.
static char* jvm_initialize(const char* classpath) {

	// Dynamically load jvm.dll / libjvm.so
	char* load_err = load_jvm_library();
	if (load_err) return load_err;

#ifdef _WIN32
	// Create JVM on a pure Windows thread to avoid Go VEH/SEH conflict
	jvm_init_args_t args;
	args.classpath = classpath;
	args.error = NULL;

	HANDLE thread = CreateThread(NULL, 0, jvm_create_thread_proc, &args, 0, NULL);
	if (!thread) {
		char buf[128];
		snprintf(buf, sizeof(buf), "CreateThread for JVM init failed (error %lu)", GetLastError());
		return strdup(buf);
	}

	WaitForSingleObject(thread, INFINITE);
	CloseHandle(thread);

	if (args.error) return args.error;

	// Attach the current (Go) thread to the JVM to obtain a valid JNIEnv*
	jint rc = (*g_jvm)->AttachCurrentThread(g_jvm, (void**)&g_env, NULL);
	if (rc != JNI_OK) {
		char buf[64];
		snprintf(buf, sizeof(buf), "AttachCurrentThread failed with code %d", (int)rc);
		return strdup(buf);
	}

#else
	// Non-Windows: call directly (no VEH/SEH conflict)
	JavaVMInitArgs vm_args;
	JavaVMOption options[1];

	size_t cp_len = strlen("-Djava.class.path=") + strlen(classpath) + 1;
	char* cp_opt = (char*)malloc(cp_len);
	snprintf(cp_opt, cp_len, "-Djava.class.path=%s", classpath);

	options[0].optionString = cp_opt;
	vm_args.version = JNI_VERSION_1_8;
	vm_args.nOptions = 1;
	vm_args.options = options;
	vm_args.ignoreUnrecognized = JNI_FALSE;

	jint rc = pfn_JNI_CreateJavaVM(&g_jvm, (void**)&g_env, &vm_args);
	free(cp_opt);

	if (rc != JNI_OK) {
		char buf[64];
		snprintf(buf, sizeof(buf), "JNI_CreateJavaVM failed with code %d", (int)rc);
		return strdup(buf);
	}
#endif

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

// Ensure the current OS thread is attached to the JVM.
// Updates g_env to the JNIEnv* for this thread.
// Must be called from any thread that will make JNI calls.
static char* ensure_jvm_thread(void) {
	if (!g_jvm) return strdup("JVM not initialized");

	JNIEnv* env = NULL;
	jint rc = (*g_jvm)->GetEnv(g_jvm, (void**)&env, JNI_VERSION_1_8);
	if (rc == JNI_OK) {
		g_env = env;
		return NULL;
	}

	if (rc == JNI_EDETACHED) {
		rc = (*g_jvm)->AttachCurrentThread(g_jvm, (void**)&g_env, NULL);
		if (rc != JNI_OK) {
			char buf[64];
			snprintf(buf, sizeof(buf), "AttachCurrentThread failed: %d", (int)rc);
			return strdup(buf);
		}
		return NULL;
	}

	char buf[64];
	snprintf(buf, sizeof(buf), "GetEnv returned unexpected code: %d", (int)rc);
	return strdup(buf);
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

	g_noOp = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "noOp", "()V");
	if (!g_noOp) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find noOp"); }

	g_divIntegers = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "divIntegers", "(JJ)D");
	if (!g_divIntegers) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find divIntegers"); }

	g_joinStrings = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "joinStrings", "([Ljava/lang/String;)Ljava/lang/String;");
	if (!g_joinStrings) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find joinStrings"); }

	g_returnsAnError = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "returnsAnError", "()V");
	if (!g_returnsAnError) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find returnsAnError"); }

	g_callCallbackAdd = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "callCallbackAdd", "(Ljava/util/function/IntBinaryOperator;)I");
	if (!g_callCallbackAdd) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find callCallbackAdd"); }

	g_echoAny = (*g_env)->GetStaticMethodID(g_env, g_core_cls, "echoAny", "(Ljava/lang/Object;)Ljava/lang/Object;");
	if (!g_echoAny) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find echoAny"); }

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

	// Cache common class refs used by hot-path benchmark functions.
	// In real-world JNI code, these are resolved once at startup.
	jclass lc;

	lc = (*g_env)->FindClass(g_env, "java/lang/String");
	if (!lc) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find java.lang.String"); }
	g_string_cls = (jclass)(*g_env)->NewGlobalRef(g_env, lc);
	(*g_env)->DeleteLocalRef(g_env, lc);

	lc = (*g_env)->FindClass(g_env, "[I");
	if (!lc) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find [I"); }
	g_int_array_cls = (jclass)(*g_env)->NewGlobalRef(g_env, lc);
	(*g_env)->DeleteLocalRef(g_env, lc);

	lc = (*g_env)->FindClass(g_env, "java/lang/Object");
	if (!lc) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find java.lang.Object"); }
	g_object_cls = (jclass)(*g_env)->NewGlobalRef(g_env, lc);
	(*g_env)->DeleteLocalRef(g_env, lc);

	lc = (*g_env)->FindClass(g_env, "java/lang/Integer");
	if (!lc) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find java.lang.Integer"); }
	g_integer_cls = (jclass)(*g_env)->NewGlobalRef(g_env, lc);
	(*g_env)->DeleteLocalRef(g_env, lc);

	lc = (*g_env)->FindClass(g_env, "java/lang/Double");
	if (!lc) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find java.lang.Double"); }
	g_double_cls = (jclass)(*g_env)->NewGlobalRef(g_env, lc);
	(*g_env)->DeleteLocalRef(g_env, lc);

	lc = (*g_env)->FindClass(g_env, "[Ljava/lang/Object;");
	if (!lc) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find [Ljava.lang.Object;"); }
	g_object_array_cls = (jclass)(*g_env)->NewGlobalRef(g_env, lc);
	(*g_env)->DeleteLocalRef(g_env, lc);

	g_int_valueOf = (*g_env)->GetStaticMethodID(g_env, g_integer_cls, "valueOf", "(I)Ljava/lang/Integer;");
	if (!g_int_valueOf) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find Integer.valueOf"); }

	g_dbl_valueOf = (*g_env)->GetStaticMethodID(g_env, g_double_cls, "valueOf", "(D)Ljava/lang/Double;");
	if (!g_dbl_valueOf) { (*g_env)->ExceptionClear(g_env); return strdup("Cannot find Double.valueOf"); }

	return NULL;
}

// ---------------------------------------------------------------------------
// Benchmark functions (7 scenarios)
// ---------------------------------------------------------------------------

// Scenario 1: void call
static char* bench_void_call(void) {
	(*g_env)->CallStaticVoidMethod(g_env, g_core_cls, g_noOp);
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
	// Build String[] {"hello", "world"} — uses cached g_string_cls
	jobjectArray arr = (*g_env)->NewObjectArray(g_env, 2, g_string_cls, NULL);
	jstring s1 = (*g_env)->NewStringUTF(g_env, "hello");
	jstring s2 = (*g_env)->NewStringUTF(g_env, "world");
	(*g_env)->SetObjectArrayElement(g_env, arr, 0, s1);
	(*g_env)->SetObjectArrayElement(g_env, arr, 1, s2);

	jstring result = (jstring)(*g_env)->CallStaticObjectMethod(g_env, g_core_cls, g_joinStrings, arr);
	char* err = jni_get_error();
	if (err) {
		(*g_env)->DeleteLocalRef(g_env, arr);
		(*g_env)->DeleteLocalRef(g_env, s1);
		(*g_env)->DeleteLocalRef(g_env, s2);
		return err;
	}

	const char* chars = (*g_env)->GetStringUTFChars(g_env, result, NULL);
	*out = strdup(chars);
	(*g_env)->ReleaseStringUTFChars(g_env, result, chars);

	(*g_env)->DeleteLocalRef(g_env, arr);
	(*g_env)->DeleteLocalRef(g_env, s1);
	(*g_env)->DeleteLocalRef(g_env, s2);
	(*g_env)->DeleteLocalRef(g_env, result);

	return NULL;
}

// Scenario 4: array sum (sumRaggedArray with single-row int[][])
static char* bench_array_sum(int size, int* out) {
	// Build int[][]{int[size]{1, 2, ..., size}} — uses cached g_int_array_cls
	jintArray innerArr = (*g_env)->NewIntArray(g_env, size);
	jint* elems = (*g_env)->GetIntArrayElements(g_env, innerArr, NULL);
	for (int i = 0; i < size; i++) {
		elems[i] = i + 1;
	}
	(*g_env)->ReleaseIntArrayElements(g_env, innerArr, elems, 0);

	jobjectArray outerArr = (*g_env)->NewObjectArray(g_env, 1, g_int_array_cls, NULL);
	(*g_env)->SetObjectArrayElement(g_env, outerArr, 0, innerArr);

	jint result = (*g_env)->CallStaticIntMethod(g_env, g_arrayfunctions_cls, g_sumRaggedArray, outerArr);
	char* err = jni_get_error();
	if (err) {
		(*g_env)->DeleteLocalRef(g_env, innerArr);
		(*g_env)->DeleteLocalRef(g_env, outerArr);
		return err;
	}
	*out = (int)result;

	(*g_env)->DeleteLocalRef(g_env, innerArr);
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

// Scenario: dynamic any echo (mixed array payload)
// Uses cached class refs and method IDs (g_object_cls, g_integer_cls, etc.)
static char* bench_any_echo(int size, int* out_len) {
	jobjectArray arr = (*g_env)->NewObjectArray(g_env, size, g_object_cls, NULL);
	if (!arr) {
		return strdup("Failed to allocate Object[] for any echo");
	}

	for (int i = 0; i < size; i++) {
		jobject elem = NULL;
		switch (i % 3) {
			case 0:
				elem = (*g_env)->CallStaticObjectMethod(g_env, g_integer_cls, g_int_valueOf, (jint)1);
				break;
			case 1:
				elem = (*g_env)->NewStringUTF(g_env, "two");
				break;
			default:
				elem = (*g_env)->CallStaticObjectMethod(g_env, g_double_cls, g_dbl_valueOf, (jdouble)3.0);
				break;
		}
		(*g_env)->SetObjectArrayElement(g_env, arr, i, elem);
		if (elem) {
			(*g_env)->DeleteLocalRef(g_env, elem);
		}
	}

	jobject result = (*g_env)->CallStaticObjectMethod(g_env, g_core_cls, g_echoAny, arr);
	char* err = jni_get_error();
	if (err) {
		(*g_env)->DeleteLocalRef(g_env, arr);
		return err;
	}

	if (!result || !(*g_env)->IsInstanceOf(g_env, result, g_object_array_cls)) {
		(*g_env)->DeleteLocalRef(g_env, arr);
		if (result) {
			(*g_env)->DeleteLocalRef(g_env, result);
		}
		return strdup("echoAny returned non-array value");
	}

	*out_len = (int)(*g_env)->GetArrayLength(g_env, (jarray)result);

	(*g_env)->DeleteLocalRef(g_env, arr);
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

static char* init_callback_helper(void) {
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

// EnsureJVMThread attaches the current OS thread to the JVM if needed.
// Must be called (with runtime.LockOSThread) from any goroutine that
// will make JNI calls on a different thread than JVMInitialize.
func EnsureJVMThread() error {
	cerr := C.ensure_jvm_thread()
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return fmt.Errorf("ensure JVM thread: %s", msg)
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

// BenchAnyEcho executes the dynamic any echo scenario and returns the echoed length.
func BenchAnyEcho(size int) (int, error) {
	var outLen C.int
	cerr := C.bench_any_echo(C.int(size), &outLen)
	if cerr != nil {
		msg := C.GoString(cerr)
		C.free(unsafe.Pointer(cerr))
		return 0, fmt.Errorf("%s", msg)
	}
	return int(outLen), nil
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
