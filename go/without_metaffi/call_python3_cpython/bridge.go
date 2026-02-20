// Package call_python3_cpython provides a cgo bridge to the CPython C API
// for benchmarking Go -> Python3 calls without MetaFFI.
//
// Build requirements:
//   - CPython development headers (Python.h)
//   - pkg-config with python3-embed, OR set CGO_CFLAGS and CGO_LDFLAGS manually:
//       CGO_CFLAGS=-I<python-include-dir>
//       CGO_LDFLAGS=-L<python-libs-dir> -lpython3XX
//
// Auto-detect paths on any platform:
//
//	python -c "import sysconfig; print('-I' + sysconfig.get_path('include'))"
//	python -c "import sysconfig, os; print('-L' + os.path.join(sysconfig.get_config_var('prefix'), 'libs'))"
package call_python3_cpython

/*
#cgo windows CFLAGS: -IC:/Users/green/AppData/Local/Programs/Python/Python312/Include
#cgo windows LDFLAGS: -LC:/Users/green/AppData/Local/Programs/Python/Python312/libs -lpython312
#cgo !windows pkg-config: python3-embed
#include <Python.h>
#include <stdlib.h>
#include <string.h>

// ============================================================
// Initialization & teardown
// ============================================================

static int py_initialize(void) {
	Py_Initialize();
	return Py_IsInitialized() ? 0 : -1;
}

static int py_add_sys_path(const char* dir) {
	PyObject *sys_mod = PyImport_ImportModule("sys");
	if (!sys_mod) return -1;

	PyObject *sys_path = PyObject_GetAttrString(sys_mod, "path");
	if (!sys_path) { Py_DECREF(sys_mod); return -1; }

	PyObject *path_str = PyUnicode_FromString(dir);
	if (!path_str) { Py_DECREF(sys_path); Py_DECREF(sys_mod); return -1; }

	int ret = PyList_Append(sys_path, path_str);
	Py_DECREF(path_str);
	Py_DECREF(sys_path);
	Py_DECREF(sys_mod);
	return ret;
}

static void py_finalize(void) {
	if (Py_IsInitialized()) {
		Py_FinalizeEx();
	}
}

// ============================================================
// Error handling
// ============================================================

// Returns a malloc'd string or NULL. Caller must free().
static char* py_get_error(void) {
	if (!PyErr_Occurred()) return NULL;

	PyObject *type = NULL, *value = NULL, *tb = NULL;
	PyErr_Fetch(&type, &value, &tb);
	PyErr_NormalizeException(&type, &value, &tb);

	char *msg = NULL;
	if (value) {
		PyObject *str_obj = PyObject_Str(value);
		if (str_obj) {
			const char *utf8 = PyUnicode_AsUTF8(str_obj);
			if (utf8) {
				size_t len = strlen(utf8) + 1;
				msg = (char*)malloc(len);
				if (msg) memcpy(msg, utf8, len);
			}
			Py_DECREF(str_obj);
		}
	}

	Py_XDECREF(type);
	Py_XDECREF(value);
	Py_XDECREF(tb);

	if (!msg) {
		const char *fallback = "unknown Python error";
		size_t len = strlen(fallback) + 1;
		msg = (char*)malloc(len);
		if (msg) memcpy(msg, fallback, len);
	}
	return msg;
}

// ============================================================
// Module / attribute helpers
// ============================================================

static PyObject* py_import(const char* name) {
	return PyImport_ImportModule(name);
}

static PyObject* py_getattr(PyObject* obj, const char* name) {
	return PyObject_GetAttrString(obj, name);
}

static const char* py_version(void) {
	return Py_GetVersion();
}

// ============================================================
// Scenario 1: void call -- no_op()
// ============================================================

static int bench_void_call(PyObject* func) {
	PyObject *result = PyObject_CallObject(func, NULL);
	if (!result) return -1;
	Py_DECREF(result);
	return 0;
}

// ============================================================
// Scenario 2: primitive echo -- div_integers(10, 2) -> 5.0
// ============================================================

static int bench_primitive_echo(PyObject* func, double *out_val) {
	PyObject *a = PyLong_FromLong(10);
	PyObject *b = PyLong_FromLong(2);
	if (!a || !b) {
		Py_XDECREF(a);
		Py_XDECREF(b);
		return -1;
	}

	PyObject *args = PyTuple_Pack(2, a, b);
	Py_DECREF(a);
	Py_DECREF(b);
	if (!args) return -1;

	PyObject *result = PyObject_CallObject(func, args);
	Py_DECREF(args);

	if (!result) return -1;

	*out_val = PyFloat_AsDouble(result);
	Py_DECREF(result);

	if (PyErr_Occurred()) return -1;
	return 0;
}

// ============================================================
// Scenario 3: string echo -- join_strings(["hello","world"])
// ============================================================

static int bench_string_echo(PyObject* func, int *match) {
	PyObject *list = PyList_New(2);
	if (!list) return -1;

	// PyList_SetItem steals references
	PyList_SetItem(list, 0, PyUnicode_FromString("hello"));
	PyList_SetItem(list, 1, PyUnicode_FromString("world"));

	PyObject *args = PyTuple_Pack(1, list);
	Py_DECREF(list);
	if (!args) return -1;

	PyObject *result = PyObject_CallObject(func, args);
	Py_DECREF(args);

	if (!result) return -1;

	const char *s = PyUnicode_AsUTF8(result);
	*match = (s != NULL && strcmp(s, "hello,world") == 0) ? 1 : 0;
	Py_DECREF(result);
	return 0;
}

// ============================================================
// Scenario 4: array sum -- accepts_ragged_array([[1..N]])
// ============================================================

static int bench_array_sum(PyObject* func, int size, long expected_sum, int *match) {
	// Build inner list [1, 2, ..., size]
	PyObject *inner = PyList_New((Py_ssize_t)size);
	if (!inner) return -1;

	for (int i = 0; i < size; i++) {
		PyList_SetItem(inner, (Py_ssize_t)i, PyLong_FromLong((long)(i + 1)));
	}

	// Wrap in outer list [[...]]
	PyObject *outer = PyList_New(1);
	if (!outer) { Py_DECREF(inner); return -1; }
	PyList_SetItem(outer, 0, inner); // steals ref

	PyObject *args = PyTuple_Pack(1, outer);
	Py_DECREF(outer);
	if (!args) return -1;

	PyObject *result = PyObject_CallObject(func, args);
	Py_DECREF(args);

	if (!result) return -1;

	long val = PyLong_AsLong(result);
	*match = (val == expected_sum) ? 1 : 0;
	Py_DECREF(result);

	if (PyErr_Occurred()) return -1;
	return 0;
}

// ============================================================
// Scenario: dynamic any echo -- echo_any([1,"two",3.0,...])
// ============================================================

static int bench_any_echo(PyObject* func, int size, int *match) {
	PyObject *list = PyList_New((Py_ssize_t)size);
	if (!list) return -1;

	for (int i = 0; i < size; i++) {
		int mod = i % 3;
		if (mod == 0) {
			PyList_SetItem(list, i, PyLong_FromLong(1));
		} else if (mod == 1) {
			PyList_SetItem(list, i, PyUnicode_FromString("two"));
		} else {
			PyList_SetItem(list, i, PyFloat_FromDouble(3.0));
		}
	}

	PyObject *args = PyTuple_Pack(1, list);
	Py_DECREF(list);
	if (!args) return -1;

	PyObject *result = PyObject_CallObject(func, args);
	Py_DECREF(args);
	if (!result) return -1;

	*match = (PyList_Check(result) && PyList_Size(result) == size) ? 1 : 0;
	Py_DECREF(result);
	return 0;
}

// ============================================================
// Scenario 5: object method -- SomeClass("bench").print()
// ============================================================

static int bench_object_method(PyObject* cls, int *match) {
	// Create: SomeClass("bench")
	PyObject *name_arg = PyUnicode_FromString("bench");
	if (!name_arg) return -1;

	PyObject *ctor_args = PyTuple_Pack(1, name_arg);
	Py_DECREF(name_arg);
	if (!ctor_args) return -1;

	PyObject *instance = PyObject_CallObject(cls, ctor_args);
	Py_DECREF(ctor_args);
	if (!instance) return -1;

	// Get .print method and call it
	PyObject *print_method = PyObject_GetAttrString(instance, "print");
	if (!print_method) {
		Py_DECREF(instance);
		return -1;
	}

	PyObject *result = PyObject_CallObject(print_method, NULL);
	Py_DECREF(print_method);
	Py_DECREF(instance);

	if (!result) return -1;

	const char *s = PyUnicode_AsUTF8(result);
	*match = (s != NULL && strcmp(s, "Hello from SomeClass bench") == 0) ? 1 : 0;
	Py_DECREF(result);
	return 0;
}

// ============================================================
// Scenario 6: callback -- call_callback_add(adder)
// ============================================================

static PyObject* _c_adder(PyObject* self, PyObject* args) {
	long a, b;
	if (!PyArg_ParseTuple(args, "ll", &a, &b))
		return NULL;
	return PyLong_FromLong(a + b);
}

static PyMethodDef _adder_method_def = {
	"c_adder", _c_adder, METH_VARARGS, "Add two longs"
};

static int bench_callback(PyObject* func, int *match) {
	PyObject *adder = PyCFunction_New(&_adder_method_def, NULL);
	if (!adder) return -1;

	PyObject *args = PyTuple_Pack(1, adder);
	Py_DECREF(adder);
	if (!args) return -1;

	PyObject *result = PyObject_CallObject(func, args);
	Py_DECREF(args);

	if (!result) return -1;

	long val = PyLong_AsLong(result);
	*match = (val == 3) ? 1 : 0;
	Py_DECREF(result);

	if (PyErr_Occurred()) return -1;
	return 0;
}

// ============================================================
// Scenario 7: error propagation -- returns_an_error()
// ============================================================

// ---------------------------------------------------------------------------
// Thread / GIL management for subtests on different OS threads
// ---------------------------------------------------------------------------

// Release the GIL so other threads can acquire it.
// Call from the thread that currently holds the GIL (e.g. TestMain).
static void py_save_thread(void) {
	PyEval_SaveThread();
}

// Acquire the GIL for the current thread (creating a Python thread
// state if needed). Returns an opaque state for py_release_gil.
static int py_ensure_gil(void) {
	return (int)PyGILState_Ensure();
}

// Release the GIL for the current thread.
static void py_release_gil(int state) {
	PyGILState_Release((PyGILState_STATE)state);
}

// ============================================================
// Scenario 7: error propagation -- returns_an_error()
// ============================================================

static int bench_error_propagation(PyObject* func) {
	PyObject *result = PyObject_CallObject(func, NULL);
	if (result != NULL) {
		// Expected an error but call succeeded
		Py_DECREF(result);
		return -1;
	}
	// Error IS expected -- clear it
	PyErr_Clear();
	return 0;
}
*/
import "C"

import (
	"fmt"
	"strings"
	"unsafe"
)

// pyObj is a type alias to avoid exposing cgo types in test files.
type pyObj = *C.PyObject

// ---------------------------------------------------------------------------
// Go wrappers for CPython C API calls
// ---------------------------------------------------------------------------

// PyInitialize calls Py_Initialize and adds modulePath to sys.path.
func PyInitialize(modulePath string) error {
	if C.py_initialize() != 0 {
		return fmt.Errorf("Py_Initialize() failed: %s", GoGetPyError())
	}

	cpath := C.CString(modulePath)
	defer C.free(unsafe.Pointer(cpath))

	if C.py_add_sys_path(cpath) != 0 {
		return fmt.Errorf("failed to add %s to sys.path: %s", modulePath, GoGetPyError())
	}
	return nil
}

// PyFinalize calls Py_FinalizeEx.
func PyFinalize() {
	C.py_finalize()
}

// PySaveThread releases the GIL so other threads can acquire it.
// Must be called from the thread that currently holds the GIL.
func PySaveThread() {
	C.py_save_thread()
}

// PyEnsureGIL acquires the GIL for the current thread.
// Returns a state value that must be passed to PyReleaseGIL.
func PyEnsureGIL() int {
	return int(C.py_ensure_gil())
}

// PyReleaseGIL releases the GIL for the current thread.
func PyReleaseGIL(state int) {
	C.py_release_gil(C.int(state))
}

// PyImportModule imports a Python module by name.
func PyImportModule(name string) (pyObj, error) {
	cname := C.CString(name)
	defer C.free(unsafe.Pointer(cname))

	mod := C.py_import(cname)
	if mod == nil {
		return nil, fmt.Errorf("failed to import '%s': %s", name, GoGetPyError())
	}
	return mod, nil
}

// PyGetAttr gets an attribute from a Python object.
func PyGetAttr(obj pyObj, name string) (pyObj, error) {
	cname := C.CString(name)
	defer C.free(unsafe.Pointer(cname))

	attr := C.py_getattr(obj, cname)
	if attr == nil {
		return nil, fmt.Errorf("%s not found: %s", name, GoGetPyError())
	}
	return attr, nil
}

// PyVersion returns the Python version string (e.g. "3.12.0").
func PyVersion() string {
	pyVer := C.GoString(C.py_version())
	if idx := strings.IndexByte(pyVer, ' '); idx > 0 {
		pyVer = pyVer[:idx]
	}
	return pyVer
}

// GoGetPyError fetches the current Python exception as a Go string.
func GoGetPyError() string {
	cmsg := C.py_get_error()
	if cmsg == nil {
		return "unknown Python error"
	}
	defer C.free(unsafe.Pointer(cmsg))
	return C.GoString(cmsg)
}

// ---------------------------------------------------------------------------
// Benchmark scenario wrappers
// ---------------------------------------------------------------------------

// BenchVoidCall calls no_op().
func BenchVoidCall(fn pyObj) error {
	if C.bench_void_call(fn) != 0 {
		return fmt.Errorf("no_op() failed: %s", GoGetPyError())
	}
	return nil
}

// BenchPrimitiveEcho calls div_integers(10, 2) and validates the result.
func BenchPrimitiveEcho(fn pyObj) error {
	var val C.double
	if C.bench_primitive_echo(fn, &val) != 0 {
		return fmt.Errorf("div_integers(10,2) failed: %s", GoGetPyError())
	}
	if float64(val)-5.0 > 1e-10 || float64(val)-5.0 < -1e-10 {
		return fmt.Errorf("div_integers(10,2): got %v, want 5.0", float64(val))
	}
	return nil
}

// BenchStringEcho calls join_strings(["hello","world"]) and validates.
func BenchStringEcho(fn pyObj) error {
	var match C.int
	if C.bench_string_echo(fn, &match) != 0 {
		return fmt.Errorf("join_strings failed: %s", GoGetPyError())
	}
	if match == 0 {
		return fmt.Errorf("join_strings: result did not match \"hello,world\"")
	}
	return nil
}

// BenchArraySum calls accepts_ragged_array with a [1..size] array.
func BenchArraySum(fn pyObj, size int, expectedSum int64) error {
	var match C.int
	if C.bench_array_sum(fn, C.int(size), C.long(expectedSum), &match) != 0 {
		return fmt.Errorf("accepts_ragged_array(size=%d) failed: %s", size, GoGetPyError())
	}
	if match == 0 {
		return fmt.Errorf("accepts_ragged_array(size=%d): sum mismatch (want %d)", size, expectedSum)
	}
	return nil
}

// BenchAnyEcho calls echo_any([1,"two",3.0,...]) and validates result length.
func BenchAnyEcho(fn pyObj, size int) error {
	var match C.int
	if C.bench_any_echo(fn, C.int(size), &match) != 0 {
		return fmt.Errorf("echo_any(size=%d) failed: %s", size, GoGetPyError())
	}
	if match == 0 {
		return fmt.Errorf("echo_any(size=%d): result mismatch", size)
	}
	return nil
}

// BenchObjectMethod creates SomeClass("bench") and calls .print().
func BenchObjectMethod(cls pyObj) error {
	var match C.int
	if C.bench_object_method(cls, &match) != 0 {
		return fmt.Errorf("SomeClass.print() failed: %s", GoGetPyError())
	}
	if match == 0 {
		return fmt.Errorf("SomeClass.print(): result mismatch")
	}
	return nil
}

// BenchCallback passes a C adder function to call_callback_add.
func BenchCallback(fn pyObj) error {
	var match C.int
	if C.bench_callback(fn, &match) != 0 {
		return fmt.Errorf("call_callback_add failed: %s", GoGetPyError())
	}
	if match == 0 {
		return fmt.Errorf("call_callback_add: got wrong result, want 3")
	}
	return nil
}

// BenchErrorPropagation calls returns_an_error() and expects an exception.
func BenchErrorPropagation(fn pyObj) error {
	if C.bench_error_propagation(fn) != 0 {
		return fmt.Errorf("returns_an_error: expected error but call succeeded")
	}
	return nil
}
