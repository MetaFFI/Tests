package main

/*
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef int64_t (*AddCallbackFunc)(int64_t, int64_t);

// Helper to invoke C function pointer (needed by cgo)
static inline int64_t callAddCallback(AddCallbackFunc cb, int64_t a, int64_t b) {
	return cb(a, b);
}
*/
import "C"

import (
	"encoding/json"
	"sync"
	"unsafe"

	guest "metaffi_guest_go"
)

// ---------------------------------------------------------------------------
// Handle registry for opaque object passing
// ---------------------------------------------------------------------------

var (
	handleMu      sync.Mutex
	handleCounter uint64
	handles       = make(map[uint64]interface{})
)

func storeHandle(obj interface{}) uint64 {
	handleMu.Lock()
	defer handleMu.Unlock()
	handleCounter++
	handles[handleCounter] = obj
	return handleCounter
}

func loadHandle(h uint64) (interface{}, bool) {
	handleMu.Lock()
	defer handleMu.Unlock()
	obj, ok := handles[h]
	return obj, ok
}

func deleteHandle(h uint64) {
	handleMu.Lock()
	defer handleMu.Unlock()
	delete(handles, h)
}

// ---------------------------------------------------------------------------
// Scenario 1: Void call
// ---------------------------------------------------------------------------

//export GoWaitABit
func GoWaitABit(ms C.int64_t) C.int {
	guest.WaitABit(int64(ms))
	return 0
}

//export GoNoOp
func GoNoOp() {
	guest.NoOp()
}

// ---------------------------------------------------------------------------
// Scenario 2: Primitive echo (int64, int64) -> float64
// ---------------------------------------------------------------------------

//export GoDivIntegers
func GoDivIntegers(x C.int64_t, y C.int64_t, outResult *C.double) C.int {
	result := guest.DivIntegers(int64(x), int64(y))
	*outResult = C.double(result)
	return 0
}

// ---------------------------------------------------------------------------
// Scenario 3: String echo (string array -> joined string)
// ---------------------------------------------------------------------------

//export GoJoinStrings
func GoJoinStrings(arr **C.char, arrLen C.int, outResult **C.char) C.int {
	n := int(arrLen)
	goArr := make([]string, n)
	cPtrs := (*[1 << 20]*C.char)(unsafe.Pointer(arr))[:n:n]
	for i := 0; i < n; i++ {
		goArr[i] = C.GoString(cPtrs[i])
	}

	result := guest.JoinStrings(goArr)
	*outResult = C.CString(result)
	return 0
}

// ---------------------------------------------------------------------------
// Scenario 4: Array echo (uint8 round-trip)
// ---------------------------------------------------------------------------

//export GoEchoBytes
func GoEchoBytes(data unsafe.Pointer, dataLen C.int, outData *unsafe.Pointer, outLen *C.int) C.int {
	n := int(dataLen)
	goData := C.GoBytes(data, C.int(n))

	result := guest.EchoBytes(goData)

	resultLen := len(result)
	cBuf := C.malloc(C.size_t(resultLen))
	C.memcpy(cBuf, unsafe.Pointer(&result[0]), C.size_t(resultLen))

	*outData = cBuf
	*outLen = C.int(resultLen)
	return 0
}

// ---------------------------------------------------------------------------
// Scenario 5: Object create + method call
// ---------------------------------------------------------------------------

//export GoNewTestMap
func GoNewTestMap(outHandle *C.uint64_t) C.int {
	tm := guest.NewTestMap()
	h := storeHandle(tm)
	*outHandle = C.uint64_t(h)
	return 0
}

//export GoTestMapGetName
func GoTestMapGetName(handle C.uint64_t, outName **C.char) C.int {
	obj, ok := loadHandle(uint64(handle))
	if !ok {
		return -1
	}
	tm := obj.(*guest.TestMap)
	*outName = C.CString(tm.Name)
	return 0
}

//export GoFreeHandle
func GoFreeHandle(handle C.uint64_t) {
	deleteHandle(uint64(handle))
}

// ---------------------------------------------------------------------------
// Scenario 6: Callback
// ---------------------------------------------------------------------------

//export GoCallCallbackAdd
func GoCallCallbackAdd(cb C.AddCallbackFunc, outResult *C.int64_t) C.int {
	goCallback := func(a, b int64) int64 {
		return int64(C.callAddCallback(cb, C.int64_t(a), C.int64_t(b)))
	}

	result, err := guest.CallCallbackAdd(goCallback)
	if err != nil {
		return -1
	}

	*outResult = C.int64_t(result)
	return 0
}

// ---------------------------------------------------------------------------
// Scenario 7: Error propagation
// ---------------------------------------------------------------------------

//export GoReturnsAnError
func GoReturnsAnError(outErrMsg **C.char) C.int {
	err := guest.ReturnsAnError()
	if err != nil {
		*outErrMsg = C.CString(err.Error())
		return -1
	}
	*outErrMsg = nil
	return 0
}

// ---------------------------------------------------------------------------
// Scenario: dynamic any echo (JSON-encoded mixed array payload)
// ---------------------------------------------------------------------------

//export GoAnyEchoJSON
func GoAnyEchoJSON(inJSON *C.char, outJSON **C.char) C.int {
	if inJSON == nil {
		return -1
	}
	raw := C.GoString(inJSON)

	var arr []any
	if err := json.Unmarshal([]byte(raw), &arr); err != nil {
		return -1
	}
	if len(arr) == 0 {
		return -1
	}
	for i, v := range arr {
		switch i % 3 {
		case 0, 2:
			if _, ok := v.(float64); !ok {
				return -1
			}
		case 1:
			if _, ok := v.(string); !ok {
				return -1
			}
		}
	}

	*outJSON = C.CString(raw)
	return 0
}

// ---------------------------------------------------------------------------
// Memory management helpers
// ---------------------------------------------------------------------------

//export GoFreeString
func GoFreeString(str *C.char) {
	C.free(unsafe.Pointer(str))
}

//export GoFreeBytes
func GoFreeBytes(ptr unsafe.Pointer) {
	C.free(ptr)
}

func main() {}
