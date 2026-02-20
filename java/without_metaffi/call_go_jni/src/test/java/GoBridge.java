/**
 * JNI bridge to Go guest module via cgo-exported DLL.
 *
 * The native methods are implemented in go_bridge/jni_impl.c,
 * which delegates to Go-exported functions in go_bridge/bridge.go.
 */
public class GoBridge
{
	static
	{
		System.loadLibrary("go_jni_bridge");
	}

	// Scenario 1: void call
	public static native void waitABit(long ms);
	public static native void noOp();

	// Scenario 2: primitive echo
	public static native double divIntegers(long x, long y);

	// Scenario 3: string echo
	public static native String joinStrings(String[] arr);

	// Scenario 4: array echo
	public static native byte[] echoBytes(byte[] data);

	// Scenario 5: object create + method call
	public static native long newTestMap();
	public static native String testMapGetName(long handle);
	public static native void freeHandle(long handle);

	// Scenario 6: callback
	public static native long callCallbackAdd(AddCallback adder);

	// Scenario 7: error propagation (returns error message, null if no error)
	public static native String returnsAnError();

	// Scenario: dynamic any echo (JSON-encoded mixed array payload)
	public static native String anyEchoJson(String payloadJson);

	/** Callback interface for add(a, b) -> result */
	public interface AddCallback
	{
		long add(long a, long b);
	}
}
