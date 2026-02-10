/**
 * JNI native method implementations for GoBridge.java.
 *
 * These functions are compiled into the same shared library as the Go bridge
 * (via cgo -buildmode=c-shared). They delegate to Go-exported functions
 * declared in bridge.go.
 *
 * Build: set CGO_CFLAGS to include JAVA_HOME/include paths, then:
 *   go build -buildmode=c-shared -o go_jni_bridge.dll .
 */

#include <jni.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* ---------------------------------------------------------------------------
 * Go-exported function declarations (from bridge.go //export directives).
 * Declared manually to avoid _cgo_export.h include-order issues.
 * ---------------------------------------------------------------------------*/

extern int GoWaitABit(int64_t ms);
extern int GoDivIntegers(int64_t x, int64_t y, double* outResult);
extern int GoJoinStrings(char** arr, int arrLen, char** outResult);
extern int GoEchoBytes(void* data, int dataLen, void** outData, int* outLen);
extern int GoNewTestMap(uint64_t* outHandle);
extern int GoTestMapGetName(uint64_t handle, char** outName);
extern void GoFreeHandle(uint64_t handle);
extern void GoFreeString(char* str);
extern void GoFreeBytes(void* ptr);
extern int GoReturnsAnError(char** outErrMsg);

typedef int64_t (*AddCallbackFunc)(int64_t, int64_t);
extern int GoCallCallbackAdd(AddCallbackFunc cb, int64_t* outResult);

/* ---------------------------------------------------------------------------
 * Scenario 1: void call
 * ---------------------------------------------------------------------------*/

JNIEXPORT void JNICALL Java_GoBridge_waitABit(JNIEnv* env, jclass cls, jlong ms)
{
    GoWaitABit((int64_t)ms);
}

/* ---------------------------------------------------------------------------
 * Scenario 2: primitive echo
 * ---------------------------------------------------------------------------*/

JNIEXPORT jdouble JNICALL Java_GoBridge_divIntegers(JNIEnv* env, jclass cls, jlong x, jlong y)
{
    double result;
    GoDivIntegers((int64_t)x, (int64_t)y, &result);
    return (jdouble)result;
}

/* ---------------------------------------------------------------------------
 * Scenario 3: string echo
 * ---------------------------------------------------------------------------*/

JNIEXPORT jstring JNICALL Java_GoBridge_joinStrings(JNIEnv* env, jclass cls, jobjectArray arr)
{
    int len = (*env)->GetArrayLength(env, arr);
    char** cStrings = (char**)malloc(sizeof(char*) * len);

    for (int i = 0; i < len; i++)
    {
        jstring jstr = (jstring)(*env)->GetObjectArrayElement(env, arr, i);
        const char* utfChars = (*env)->GetStringUTFChars(env, jstr, NULL);
        cStrings[i] = strdup(utfChars);
        (*env)->ReleaseStringUTFChars(env, jstr, utfChars);
    }

    char* result = NULL;
    GoJoinStrings(cStrings, len, &result);

    for (int i = 0; i < len; i++) free(cStrings[i]);
    free(cStrings);

    jstring jResult = (*env)->NewStringUTF(env, result);
    GoFreeString(result);
    return jResult;
}

/* ---------------------------------------------------------------------------
 * Scenario 4: array echo (byte[])
 * ---------------------------------------------------------------------------*/

JNIEXPORT jbyteArray JNICALL Java_GoBridge_echoBytes(JNIEnv* env, jclass cls, jbyteArray data)
{
    int dataLen = (*env)->GetArrayLength(env, data);
    jbyte* dataBytes = (*env)->GetByteArrayElements(env, data, NULL);

    void* outData = NULL;
    int outLen = 0;
    GoEchoBytes((void*)dataBytes, dataLen, &outData, &outLen);

    (*env)->ReleaseByteArrayElements(env, data, dataBytes, JNI_ABORT);

    jbyteArray result = (*env)->NewByteArray(env, outLen);
    (*env)->SetByteArrayRegion(env, result, 0, outLen, (jbyte*)outData);
    GoFreeBytes(outData);
    return result;
}

/* ---------------------------------------------------------------------------
 * Scenario 5: object create + method call
 * ---------------------------------------------------------------------------*/

JNIEXPORT jlong JNICALL Java_GoBridge_newTestMap(JNIEnv* env, jclass cls)
{
    uint64_t handle;
    GoNewTestMap(&handle);
    return (jlong)handle;
}

JNIEXPORT jstring JNICALL Java_GoBridge_testMapGetName(JNIEnv* env, jclass cls, jlong handle)
{
    char* name = NULL;
    GoTestMapGetName((uint64_t)handle, &name);
    jstring jResult = (*env)->NewStringUTF(env, name);
    GoFreeString(name);
    return jResult;
}

JNIEXPORT void JNICALL Java_GoBridge_freeHandle(JNIEnv* env, jclass cls, jlong handle)
{
    GoFreeHandle((uint64_t)handle);
}

/* ---------------------------------------------------------------------------
 * Scenario 6: callback
 * ---------------------------------------------------------------------------*/

/* Thread-local storage for the JNI callback context.
 * Safe because JNI native methods execute on the calling thread,
 * and cgo dispatches the callback on the same OS thread. */
static __thread JNIEnv* g_cb_env = NULL;
static __thread jobject g_cb_obj = NULL;
static __thread jmethodID g_cb_method = NULL;

static int64_t jni_add_callback(int64_t a, int64_t b)
{
    return (int64_t)(*g_cb_env)->CallLongMethod(g_cb_env, g_cb_obj, g_cb_method, (jlong)a, (jlong)b);
}

JNIEXPORT jlong JNICALL Java_GoBridge_callCallbackAdd(JNIEnv* env, jclass cls, jobject adder)
{
    jclass adderClass = (*env)->GetObjectClass(env, adder);
    jmethodID addMethod = (*env)->GetMethodID(env, adderClass, "add", "(JJ)J");

    /* Store in thread-local for the callback */
    g_cb_env = env;
    g_cb_obj = adder;
    g_cb_method = addMethod;

    int64_t result;
    int rc = GoCallCallbackAdd(&jni_add_callback, &result);

    g_cb_env = NULL;
    g_cb_obj = NULL;
    g_cb_method = NULL;

    if (rc != 0) return -1;
    return (jlong)result;
}

/* ---------------------------------------------------------------------------
 * Scenario 7: error propagation
 * ---------------------------------------------------------------------------*/

JNIEXPORT jstring JNICALL Java_GoBridge_returnsAnError(JNIEnv* env, jclass cls)
{
    char* errMsg = NULL;
    int rc = GoReturnsAnError(&errMsg);
    if (rc != 0 && errMsg != NULL)
    {
        jstring jErr = (*env)->NewStringUTF(env, errMsg);
        GoFreeString(errMsg);
        return jErr;
    }
    return NULL;
}
