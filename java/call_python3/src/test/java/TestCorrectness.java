import api.MetaFFIModule;
import api.MetaFFIRuntime;
import metaffi.api.accessor.Caller;
import metaffi.api.accessor.MetaFFIHandle;
import metaffi.api.accessor.MetaFFITypeInfo;
import metaffi.api.accessor.MetaFFITypeInfo.MetaFFITypes;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import static org.junit.Assert.*;

/**
 * Correctness tests: Java host -> Python3 guest via MetaFFI.
 *
 * Tests ALL Python3 guest module entities accessible through MetaFFI.
 * Fail-fast: every assertion is exact (or epsilon-justified for floats).
 *
 * NOTE: No-params+return dispatch was fixed in SDK/JVM path.
 * Legacy xfail() wrappers are kept for minimal diff and now execute directly.
 */
public class TestCorrectness
{
	private static MetaFFIRuntime runtime;
	private static MetaFFIModule pyModuleDir;   // Python package: module/
	private static MetaFFIModule pyModuleFile;  // Single file: single_file_module.py

	private static final String NO_PARAMS_BUG = "legacy no-params+return regression guard";

	@BeforeClass
	public static void setUp()
	{
		String metaffiHome = System.getenv("METAFFI_HOME");
		assertNotNull("METAFFI_HOME must be set", metaffiHome);

		String sourceRoot = System.getenv("METAFFI_SOURCE_ROOT");
		assertNotNull("METAFFI_SOURCE_ROOT must be set", sourceRoot);

		runtime = new MetaFFIRuntime("python3");
		runtime.loadRuntimePlugin();

		// Load Python package (module/ directory)
		String moduleDirPath = sourceRoot.replace('\\', '/') +
			"/sdk/test_modules/guest_modules/python3/module";
		pyModuleDir = runtime.loadModule(moduleDirPath);
		assertNotNull("Failed to load Python3 module dir", pyModuleDir);

		// Load single-file module
		String moduleFilePath = sourceRoot.replace('\\', '/') +
			"/sdk/test_modules/guest_modules/python3/single_file_module.py";
		pyModuleFile = runtime.loadModule(moduleFilePath);
		assertNotNull("Failed to load Python3 single_file_module.py", pyModuleFile);
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
			pyModuleDir = null;
			pyModuleFile = null;
			runtime = null;
		}
	}

	// ---- Helper methods ----

	private static MetaFFITypeInfo t(MetaFFITypes type)
	{
		return new MetaFFITypeInfo(type);
	}

	private static MetaFFITypeInfo arr(MetaFFITypes type, int dims)
	{
		return new MetaFFITypeInfo(type, dims);
	}

	private Caller load(String entity, MetaFFITypeInfo[] params, MetaFFITypeInfo[] retvals)
	{
		return load(pyModuleDir, entity, params, retvals);
	}

	private Caller load(MetaFFIModule mod, String entity, MetaFFITypeInfo[] params, MetaFFITypeInfo[] retvals)
	{
		Caller c = mod.load(entity, params, retvals);
		assertNotNull("Failed to load entity: " + entity, c);
		return c;
	}

	/**
	 * Legacy wrapper kept to avoid large churn in test bodies.
	 * Known no-params+return issue is fixed, so execute the test directly.
	 */
	private void xfail(String reason, Runnable testCode)
	{
		assertNotNull("xfail reason must not be null", reason);
		testCode.run();
	}

	// ---- Python class creation helpers ----

	/**
	 * Creates a Python class instance: get class handle -> __new__ -> __init__
	 * Uses attribute getter (no params + return) as part of object construction.
	 */
	private MetaFFIHandle createPythonInstance(String className, Object... initArgs)
	{
		// Get class handle
		Caller getClass = load("attribute=" + className + ",getter", null,
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)});
		Object[] classResult = getClass.call();
		Object classHandle = classResult[0];

		// __new__ (has param: class handle)
		Caller newFn = load("callable=" + className + ".__new__",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)});
		Object[] instanceResult = newFn.call(classHandle);
		MetaFFIHandle instance = (MetaFFIHandle) instanceResult[0];

		// __init__ with the provided args
		if (initArgs.length == 0)
		{
			Caller initFn = load("callable=" + className + ".__init__,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)}, null);
			initFn.call(instance);
		}
		else
		{
			MetaFFITypeInfo[] initParams = new MetaFFITypeInfo[1 + initArgs.length];
			initParams[0] = t(MetaFFITypes.MetaFFIHandle);
			for (int i = 0; i < initArgs.length; i++)
			{
				initParams[i + 1] = inferType(initArgs[i]);
			}
			Caller initFn = load("callable=" + className + ".__init__,instance_required",
				initParams, null);

			Object[] allArgs = new Object[1 + initArgs.length];
			allArgs[0] = instance;
			System.arraycopy(initArgs, 0, allArgs, 1, initArgs.length);
			initFn.call(allArgs);
		}

		return instance;
	}

	private MetaFFITypeInfo inferType(Object arg)
	{
		if (arg instanceof Long) return t(MetaFFITypes.MetaFFIInt64);
		if (arg instanceof String) return t(MetaFFITypes.MetaFFIString8);
		if (arg instanceof Double) return t(MetaFFITypes.MetaFFIFloat64);
		if (arg instanceof Boolean) return t(MetaFFITypes.MetaFFIBool);
		return t(MetaFFITypes.MetaFFIAny);
	}

	// ========================================================================
	// core_functions.py -- WORKING (have input parameters)
	// ========================================================================

	@Test
	public void testDivIntegers()
	{
		Caller fn = load("callable=div_integers",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64), t(MetaFFITypes.MetaFFIInt64)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIFloat64)});
		Object[] result = fn.call(10L, 2L);
		assertNotNull(result);
		assertEquals(5.0, (Double) result[0], 1e-10);
	}

	@Test
	public void testDivIntegersFractional()
	{
		Caller fn = load("callable=div_integers",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64), t(MetaFFITypes.MetaFFIInt64)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIFloat64)});
		Object[] result = fn.call(7L, 3L);
		assertNotNull(result);
		assertEquals(7.0 / 3.0, (Double) result[0], 1e-10);
	}

	@Test
	public void testJoinStrings()
	{
		Caller fn = load("callable=join_strings",
			new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIString8Array, 1)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)});
		Object[] result = fn.call((Object) new String[]{"a", "b", "c"});
		assertNotNull(result);
		assertEquals("a,b,c", result[0]);
	}

	@Test
	public void testWaitABit()
	{
		Caller fn = load("callable=wait_a_bit",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)}, null);
		fn.call(0L);
	}

	@Test
	public void testReturnsAnError()
	{
		Caller fn = load("callable=returns_an_error", null, null);
		try
		{
			fn.call();
			fail("returns_an_error did not throw");
		}
		catch (Throwable e)
		{
			assertTrue("Expected error message containing 'Error', got: " + e.getMessage(),
				e.getMessage().toLowerCase().contains("error"));
		}
	}

	@Test
	public void testReturnAnyInt()
	{
		Caller fn = load("callable=return_any",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)});
		Object[] result = fn.call(0L);
		assertNotNull(result);
		assertEquals(1L, ((Number) result[0]).longValue());
	}

	@Test
	public void testReturnAnyString()
	{
		Caller fn = load("callable=return_any",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)});
		Object[] result = fn.call(1L);
		assertNotNull(result);
		assertEquals("string", result[0]);
	}

	@Test
	public void testReturnAnyFloat()
	{
		Caller fn = load("callable=return_any",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)});
		Object[] result = fn.call(2L);
		assertNotNull(result);
		assertEquals(3.0, ((Number) result[0]).doubleValue(), 1e-10);
	}

	@Test
	public void testReturnAnyNil()
	{
		Caller fn = load("callable=return_any",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)});
		Object[] result = fn.call(999L);
		assertNotNull(result);
		assertNull(result[0]);
	}

	@Test
	public void testAcceptsAnyInt()
	{
		Caller fn = load("callable=accepts_any",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64), t(MetaFFITypes.MetaFFIAny)}, null);
		fn.call(0L, 1L);
	}

	@Test
	public void testAcceptsAnyString()
	{
		Caller fn = load("callable=accepts_any",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64), t(MetaFFITypes.MetaFFIAny)}, null);
		fn.call(1L, "string");
	}

	@Test
	public void testAcceptsAnyFloat()
	{
		Caller fn = load("callable=accepts_any",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64), t(MetaFFITypes.MetaFFIAny)}, null);
		fn.call(2L, 3.0);
	}

	@Test
	public void testCallCallbackAdd()
	{
		Caller callCb = load("callable=call_callback_add",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFICallable)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});

		try
		{
			java.lang.reflect.Method addMethod = TestCorrectness.class.getMethod("javaAdd", long.class, long.class);
			Caller javaAdder = MetaFFIRuntime.makeMetaFFICallable(addMethod);
			Object[] result = callCb.call(javaAdder);
			assertNotNull(result);
			assertEquals(3L, result[0]);
		}
		catch (NoSuchMethodException e)
		{
			fail("Could not find javaAdd method: " + e.getMessage());
		}
	}

	/** Java callback: add(a, b) -> a + b */
	public static long javaAdd(long a, long b)
	{
		return a + b;
	}

	@Test
	public void testAccepts3DArray()
	{
		Caller fn = load("callable=accepts_3d_array",
			new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIInt64Array, 3)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});
		long[][][] arr3d = {{{1L}, {2L}}, {{3L}, {4L}}};
		Object[] result = fn.call((Object) arr3d);
		assertNotNull(result);
		assertEquals(10L, result[0]);
	}

	@Test
	public void testAcceptsRaggedArray()
	{
		Caller fn = load("callable=accepts_ragged_array",
			new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIInt64Array, 2)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});
		long[][] ragged = {{1L, 2L, 3L}, {4L}, {5L, 6L}};
		Object[] result = fn.call((Object) ragged);
		assertNotNull(result);
		assertEquals(21L, result[0]);
	}

	@Test
	public void testReturnsOptionalTrue()
	{
		Caller fn = load("callable=returns_optional",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIBool)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)});
		Object[] result = fn.call(true);
		assertNotNull(result);
		assertEquals(123L, ((Number) result[0]).longValue());
	}

	@Test
	public void testReturnsOptionalFalse()
	{
		Caller fn = load("callable=returns_optional",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIBool)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)});
		Object[] result = fn.call(false);
		assertNotNull(result);
		assertNull(result[0]);
	}

	// ========================================================================
	// callbacks_and_errors.py -- WORKING (have input parameters)
	// ========================================================================

	@Test
	public void testRaiseCustomError()
	{
		Caller fn = load("callable=raise_custom_error",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)}, null);
		try
		{
			fn.call("boom");
			fail("raise_custom_error did not throw");
		}
		catch (Throwable e)
		{
			assertTrue("Expected error containing 'boom', got: " + e.getMessage(),
				e.getMessage().toLowerCase().contains("boom"));
		}
	}

	@Test
	public void testReturnErrorTupleOk()
	{
		Caller fn = load("callable=return_error_tuple",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIBool)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIBool), t(MetaFFITypes.MetaFFIAny)});
		Object[] result = fn.call(true);
		assertNotNull(result);
		assertEquals(true, result[0]);
		assertNull(result[1]);
	}

	@Test
	public void testReturnErrorTupleFail()
	{
		Caller fn = load("callable=return_error_tuple",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIBool)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIBool), t(MetaFFITypes.MetaFFIAny)});
		Object[] result = fn.call(false);
		assertNotNull(result);
		assertEquals(false, result[0]);
		assertEquals("error", result[1]);
	}

	// ========================================================================
	// module_state.py -- WORKING (set/inc have input parameters)
	// ========================================================================

	@Test
	public void testModuleStateGlobalValue()
	{
		Caller setGlobal = load("callable=set_global_value",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8), t(MetaFFITypes.MetaFFIAny)}, null);
		Caller getGlobal = load("callable=get_global_value",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)});

		setGlobal.call("test_key", "test_value");
		Object[] result = getGlobal.call("test_key");
		assertEquals("test_value", result[0]);
	}

	// ========================================================================
	// args_and_signatures.py -- WORKING (have input parameters)
	// ========================================================================

	@Test
	public void testOverloadInt()
	{
		Caller fn = load("callable=overload",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)});
		Object[] result = fn.call(5L);
		assertNotNull(result);
		assertEquals(6L, ((Number) result[0]).longValue());
	}

	@Test
	public void testOverloadString()
	{
		Caller fn = load("callable=overload",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)});
		Object[] result = fn.call("hello");
		assertNotNull(result);
		assertEquals("HELLO", result[0]);
	}

	// ========================================================================
	// Legacy no-params+return coverage block (previously xfailed, now active)
	// ========================================================================

	@Test
	public void testHelloWorld()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=hello_world", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)});
			Object[] result = fn.call();
			assertNotNull(result);
			assertEquals("Hello World, from Python3", result[0]);
		});
	}

	@Test
	public void testReturnNull()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=return_null", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFINull)});
			Object[] result = fn.call();
			assertNotNull(result);
			assertNull(result[0]);
		});
	}

	@Test
	public void testReturnMultipleReturnValues()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=return_multiple_return_values", null,
				new MetaFFITypeInfo[]{
					t(MetaFFITypes.MetaFFIInt64), t(MetaFFITypes.MetaFFIString8),
					t(MetaFFITypes.MetaFFIFloat64), t(MetaFFITypes.MetaFFINull),
					arr(MetaFFITypes.MetaFFIUInt8Array, 1), t(MetaFFITypes.MetaFFIHandle),
				});
			Object[] result = fn.call();
			assertNotNull(result);
			assertEquals(6, result.length);
		});
	}

	@Test
	public void testReturnCallbackAdd()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=return_callback_add", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFICallable)});
			Object[] result = fn.call();
			assertNotNull(result);
			assertTrue("Expected Caller", result[0] instanceof Caller);
		});
	}

	@Test
	public void testGetThreeBuffers()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=get_three_buffers", null,
				new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIArray, 1)});
			Object[] result = fn.call();
			assertNotNull(result);
		});
	}

	@Test
	public void testGetSomeClasses()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=get_some_classes", null,
				new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIHandleArray, 1)});
			Object[] result = fn.call();
			assertNotNull(result);
		});
	}

	@Test
	public void testReturnsBytesBuffer()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=returns_bytes_buffer", null,
				new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIUInt8Array, 1)});
			Object[] result = fn.call();
			assertNotNull(result);
			assertArrayEquals(new byte[]{1, 2, 3}, (byte[]) result[0]);
		});
	}

	@Test
	public void testMake1DArray()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=make_1d_array", null,
				new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIInt64Array, 1)});
			Object[] result = fn.call();
			assertNotNull(result);
			assertArrayEquals(new long[]{1L, 2L, 3L}, (long[]) result[0]);
		});
	}

	@Test
	public void testMake2DArray()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=make_2d_array", null,
				new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIInt64Array, 2)});
			Object[] result = fn.call();
			assertNotNull(result);
		});
	}

	@Test
	public void testMake3DArray()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=make_3d_array", null,
				new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIInt64Array, 3)});
			Object[] result = fn.call();
			assertNotNull(result);
		});
	}

	@Test
	public void testMakeRaggedArray()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=make_ragged_array", null,
				new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIInt64Array, 2)});
			Object[] result = fn.call();
			assertNotNull(result);
		});
	}

	@Test
	public void testDefaultArgs()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=default_args", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny), t(MetaFFITypes.MetaFFIAny), t(MetaFFITypes.MetaFFIAny)});
			Object[] result = fn.call();
			assertNotNull(result);
			assertEquals(1L, ((Number) result[0]).longValue());
		});
	}

	@Test
	public void testBaseClassStaticValue()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("callable=BaseClass.static_value", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});
			Object[] result = fn.call();
			assertNotNull(result);
			assertEquals(42L, result[0]);
		});
	}

	@Test
	public void testModuleStateConstant()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load("attribute=CONSTANT_FIVE_SECONDS,getter", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});
			Object[] result = fn.call();
			assertNotNull(result);
			assertEquals(5L, result[0]);
		});
	}

	@Test
	public void testGetSetCounter()
	{
		xfail(NO_PARAMS_BUG + " (get_counter has no params)", () ->
		{
			Caller getCtr = load("callable=get_counter", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});
			Caller setCtr = load("callable=set_counter",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)}, null);
			setCtr.call(0L);
			Object[] getResult = getCtr.call();
			assertEquals(0L, getResult[0]);
		});
	}

	// ---- Python class tests (all xfail due to attribute getter using no params) ----

	@Test
	public void testSomeClassCreateAndPrint()
	{
		xfail(NO_PARAMS_BUG + " (attribute=SomeClass,getter)", () ->
		{
			MetaFFIHandle instance = createPythonInstance("SomeClass", "test_name");
			Caller printFn = load("callable=SomeClass.print,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)});
			Object[] result = printFn.call(instance);
			assertEquals("Hello from SomeClass test_name", result[0]);
		});
	}

	@Test
	public void testSomeClassStr()
	{
		xfail(NO_PARAMS_BUG + " (attribute=SomeClass,getter)", () ->
		{
			MetaFFIHandle instance = createPythonInstance("SomeClass", "abc");
			Caller strFn = load("callable=SomeClass.__str__,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)});
			Object[] result = strFn.call(instance);
			assertTrue(((String) result[0]).contains("SomeClass"));
		});
	}

	@Test
	public void testSomeClassEq()
	{
		xfail(NO_PARAMS_BUG + " (attribute=SomeClass,getter)", () ->
		{
			MetaFFIHandle instance1 = createPythonInstance("SomeClass", "same");
			MetaFFIHandle instance2 = createPythonInstance("SomeClass", "same");
			Caller eqFn = load("callable=SomeClass.__eq__,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle), t(MetaFFITypes.MetaFFIHandle)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIBool)});
			assertEquals(true, eqFn.call(instance1, instance2)[0]);
		});
	}

	@Test
	public void testTestMapSetGetContains()
	{
		xfail(NO_PARAMS_BUG + " (attribute=TestMap,getter)", () ->
		{
			MetaFFIHandle instance = createPythonInstance("TestMap");
			Caller setFn = load("callable=TestMap.set,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle), t(MetaFFITypes.MetaFFIString8), t(MetaFFITypes.MetaFFIAny)},
				null);
			setFn.call(instance, "k", 42L);

			Caller containsFn = load("callable=TestMap.contains,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle), t(MetaFFITypes.MetaFFIString8)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIBool)});
			assertEquals(true, containsFn.call(instance, "k")[0]);
		});
	}

	@Test
	public void testBaseClassCreateAndMethod()
	{
		xfail(NO_PARAMS_BUG + " (attribute=BaseClass,getter)", () ->
		{
			MetaFFIHandle instance = createPythonInstance("BaseClass", 10L);
			Caller baseMethod = load("callable=BaseClass.base_method,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});
			assertEquals(10L, baseMethod.call(instance)[0]);
		});
	}

	@Test
	public void testDerivedClassOverride()
	{
		xfail(NO_PARAMS_BUG + " (attribute=DerivedClass,getter)", () ->
		{
			MetaFFIHandle instance = createPythonInstance("DerivedClass", 10L, "extra_val");
			Caller baseMethod = load("callable=DerivedClass.base_method,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});
			assertEquals(20L, baseMethod.call(instance)[0]);
		});
	}

	// ---- Single-file module tests (all xfail due to no-param calls) ----

	@Test
	public void testSingleFileHelloWorld()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load(pyModuleFile, "callable=hello_world", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)});
			Object[] result = fn.call();
			assertTrue(((String) result[0]).contains("Hello World"));
		});
	}

	@Test
	public void testSingleFileReturnNull()
	{
		xfail(NO_PARAMS_BUG, () ->
		{
			Caller fn = load(pyModuleFile, "callable=return_null", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFINull)});
			Object[] result = fn.call();
			assertNull(result[0]);
		});
	}

	@Test
	public void testSingleFileSomeClass()
	{
		xfail(NO_PARAMS_BUG + " (attribute=SomeClass,getter on single_file)", () ->
		{
			Caller getClass = load(pyModuleFile, "attribute=SomeClass,getter", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)});
			Object classHandle = getClass.call()[0];

			Caller newFn = load(pyModuleFile, "callable=SomeClass.__new__",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)});
			MetaFFIHandle instance = (MetaFFIHandle) newFn.call(classHandle)[0];

			Caller initFn = load(pyModuleFile, "callable=SomeClass.__init__,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle), t(MetaFFITypes.MetaFFIString8)}, null);
			initFn.call(instance, "sf_test");

			Caller printFn = load(pyModuleFile, "callable=SomeClass.print,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)});
			assertEquals("Hello from SomeClass sf_test", printFn.call(instance)[0]);
		});
	}

	@Test
	public void testSingleFileTestMap()
	{
		xfail(NO_PARAMS_BUG + " (attribute=TestMap,getter on single_file)", () ->
		{
			Caller getClass = load(pyModuleFile, "attribute=TestMap,getter", null,
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)});
			Object classHandle = getClass.call()[0];

			Caller newFn = load(pyModuleFile, "callable=TestMap.__new__",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)});
			MetaFFIHandle instance = (MetaFFIHandle) newFn.call(classHandle)[0];

			Caller initFn = load(pyModuleFile, "callable=TestMap.__init__,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)}, null);
			initFn.call(instance);

			Caller setFn = load(pyModuleFile, "callable=TestMap.set,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle), t(MetaFFITypes.MetaFFIString8), t(MetaFFITypes.MetaFFIAny)},
				null);
			setFn.call(instance, "k", 99L);

			Caller containsFn = load(pyModuleFile, "callable=TestMap.contains,instance_required",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle), t(MetaFFITypes.MetaFFIString8)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIBool)});
			assertEquals(true, containsFn.call(instance, "k")[0]);
		});
	}
}
