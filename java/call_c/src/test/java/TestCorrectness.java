import api.MetaFFIModule;
import api.MetaFFIRuntime;
import metaffi.api.accessor.Caller;
import metaffi.api.accessor.MetaFFITypeInfo;
import metaffi.api.accessor.MetaFFITypeInfo.MetaFFITypes;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import static org.junit.Assert.*;

/**
 * Correctness tests: Java host -> C guest via MetaFFI.
 *
 * Tests C guest module entities accessible through MetaFFI.
 * C guest uses the "cpp" runtime (xllr.cpp handles both C and C++).
 * Fail-fast: every assertion is exact (or epsilon-justified for floats).
 */
public class TestCorrectness
{
	private static MetaFFIRuntime runtime;
	private static MetaFFIModule cModule;

	@BeforeClass
	public static void setUp()
	{
		String metaffiHome = System.getenv("METAFFI_HOME");
		assertNotNull("METAFFI_HOME must be set", metaffiHome);

		String sourceRoot = System.getenv("METAFFI_SOURCE_ROOT");
		assertNotNull("METAFFI_SOURCE_ROOT must be set", sourceRoot);

		// C guest uses the "cpp" runtime
		runtime = new MetaFFIRuntime("cpp");
		runtime.loadRuntimePlugin();

		String modulePath = sourceRoot.replace('\\', '/') +
			"/sdk/test_modules/guest_modules/c/test_bin/" + getCGuestModuleFilename();
		cModule = runtime.loadModule(modulePath);
		assertNotNull("Failed to load C guest module", cModule);
	}

	private static String getCGuestModuleFilename()
	{
		String os = System.getProperty("os.name", "").toLowerCase();
		if (os.contains("win"))
		{
			return "c_guest_module.dll";
		}
		if (os.contains("mac"))
		{
			return "c_guest_module.dylib";
		}
		return "c_guest_module.so";
	}

	@AfterClass
	public static void tearDown()
	{
		try
		{
			if (runtime != null)
			{
				runtime.releaseRuntimePlugin();
			}
		}
		finally
		{
			cModule = null;
			runtime = null;
		}
	}

	// ---- Helper methods ----

	private static MetaFFITypeInfo t(MetaFFITypes type)
	{
		return new MetaFFITypeInfo(type);
	}

	private Caller load(String entity, MetaFFITypeInfo[] params, MetaFFITypeInfo[] retvals)
	{
		Caller c = cModule.load(entity, params, retvals);
		assertNotNull("Failed to load entity: " + entity, c);
		return c;
	}

	// ========================================================================
	// Core functions (C guest)
	// ========================================================================

	@Test
	public void testNoOp()
	{
		Caller fn = load("callable=xcall_c_no_op", null, null);
		fn.call();
	}

	@Test
	public void testHelloWorld()
	{
		Caller fn = load("callable=xcall_c_hello_world", null,
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)});
		Object[] result = fn.call();
		assertNotNull(result);
		assertEquals("Hello World from C", result[0]);
	}

	@Test
	public void testReturnsAnError()
	{
		// C guest returns int32 (-1) instead of throwing
		Caller fn = load("callable=xcall_c_returns_an_error", null,
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt32)});
		Object[] result = fn.call();
		assertNotNull(result);
		assertEquals(-1, ((Number) result[0]).intValue());
	}

	@Test
	public void testDivIntegers()
	{
		Caller fn = load("callable=xcall_c_div_integers",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64), t(MetaFFITypes.MetaFFIInt64)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIFloat64)});
		Object[] result = fn.call(10L, 2L);
		assertNotNull(result);
		assertEquals(5.0, (Double) result[0], 1e-10);
	}

	// ========================================================================
	// State: counter
	// ========================================================================

	@Test
	public void testCounter()
	{
		Caller getCtr = load("callable=xcall_c_get_counter", null,
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});
		Caller setCtr = load("callable=xcall_c_set_counter",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)}, null);
		Caller incCtr = load("callable=xcall_c_inc_counter",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});

		// Reset to known value
		setCtr.call(0L);
		Object[] getResult = getCtr.call();
		assertEquals(0L, getResult[0]);

		// Increment by 5
		Object[] incResult = incCtr.call(5L);
		assertEquals(5L, incResult[0]);

		// Verify
		getResult = getCtr.call();
		assertEquals(5L, getResult[0]);

		// Reset
		setCtr.call(0L);
	}
}
