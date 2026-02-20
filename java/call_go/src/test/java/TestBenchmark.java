import api.MetaFFIModule;
import api.MetaFFIRuntime;
import metaffi.api.accessor.Caller;
import metaffi.api.accessor.MetaFFIHandle;
import metaffi.api.accessor.MetaFFITypeInfo;
import metaffi.api.accessor.MetaFFITypeInfo.MetaFFITypes;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.junit.Assert.*;

/**
 * Performance benchmarks: Java host -> Go guest via MetaFFI.
 *
 * 7 scenarios matching the plan specification, with statistical rigor.
 * Outputs results to tests/results/java_to_go_metaffi.json.
 */
public class TestBenchmark
{
	private static MetaFFIRuntime runtime;
	private static MetaFFIModule goModule;
	private static long loadRuntimePluginNs;
	private static long loadModuleNs;

	// Configuration from environment
	private static int WARMUP;
	private static int ITERATIONS;

	@BeforeClass
	public static void setUp()
	{
		String metaffiHome = System.getenv("METAFFI_HOME");
		assertNotNull("METAFFI_HOME must be set", metaffiHome);

		String sourceRoot = System.getenv("METAFFI_SOURCE_ROOT");
		assertNotNull("METAFFI_SOURCE_ROOT must be set", sourceRoot);

		WARMUP = parseIntEnv("METAFFI_TEST_WARMUP", 100);
		ITERATIONS = parseIntEnv("METAFFI_TEST_ITERATIONS", 10000);

		runtime = new MetaFFIRuntime("go");

		long start = System.nanoTime();
		runtime.loadRuntimePlugin();
		loadRuntimePluginNs = System.nanoTime() - start;

		String modulePath = sourceRoot.replace('\\', '/') +
			"/sdk/test_modules/guest_modules/go/test_bin/guest_MetaFFIGuest.dll";

		start = System.nanoTime();
		goModule = runtime.loadModule(modulePath);
		loadModuleNs = System.nanoTime() - start;

		assertNotNull("Failed to load Go guest module", goModule);
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
			goModule = null;
			runtime = null;
		}
	}

	private static int parseIntEnv(String name, int defaultValue)
	{
		String val = System.getenv(name);
		if (val == null || val.isEmpty()) return defaultValue;
		return Integer.parseInt(val);
	}

	private static Set<String> parseScenarioFilter()
	{
		String raw = System.getenv("METAFFI_TEST_SCENARIOS");
		if (raw == null || raw.trim().isEmpty())
		{
			return null;
		}

		Set<String> filter = new HashSet<>();
		for (String part : raw.split(","))
		{
			String k = part.trim();
			if (!k.isEmpty())
			{
				filter.add(k);
			}
		}
		return filter.isEmpty() ? null : filter;
	}

	private static String scenarioKey(String scenario, Integer dataSize)
	{
		return dataSize == null ? scenario : scenario + "_" + dataSize;
	}

	private static boolean shouldRunScenario(Set<String> filter, String scenario, Integer dataSize)
	{
		return filter == null || filter.contains(scenarioKey(scenario, dataSize));
	}

	// ---- Helper types and methods ----

	private static MetaFFITypeInfo t(MetaFFITypes type)
	{
		return new MetaFFITypeInfo(type);
	}

	private static MetaFFITypeInfo arr(MetaFFITypes type, int dims)
	{
		return new MetaFFITypeInfo(type, dims);
	}

	// ---- Statistical helpers ----

	private static double[] computeStats(long[] sortedNs)
	{
		int n = sortedNs.length;
		if (n == 0)
		{
			return new double[]{0, 0, 0, 0, 0, 0, 0};
		}

		double sum = 0;
		for (long v : sortedNs) sum += v;
		double mean = sum / n;

		double median;
		if (n % 2 == 1)
		{
			median = sortedNs[n / 2];
		}
		else
		{
			median = (sortedNs[n / 2 - 1] + sortedNs[n / 2]) / 2.0;
		}

		double p95 = sortedNs[(int) (n * 0.95)];
		double p99 = sortedNs[Math.min((int) (n * 0.99), n - 1)];

		double sqDiffSum = 0;
		for (long v : sortedNs) sqDiffSum += (v - mean) * (v - mean);
		double stddev = Math.sqrt(sqDiffSum / n);

		double se = stddev / Math.sqrt(n);
		double ci95Low = mean - 1.96 * se;
		double ci95High = mean + 1.96 * se;

		return new double[]{mean, median, p95, p99, stddev, ci95Low, ci95High};
	}

	private static long[] removeOutliersIQR(long[] sortedNs)
	{
		int n = sortedNs.length;
		if (n < 4) return sortedNs;

		double q1 = sortedNs[n / 4];
		double q3 = sortedNs[3 * n / 4];
		double iqr = q3 - q1;
		double lower = q1 - 1.5 * iqr;
		double upper = q3 + 1.5 * iqr;

		List<Long> cleaned = new ArrayList<>();
		for (long v : sortedNs)
		{
			if (v >= lower && v <= upper)
			{
				cleaned.add(v);
			}
		}

		long[] result = new long[cleaned.size()];
		for (int i = 0; i < cleaned.size(); i++) result[i] = cleaned.get(i);
		return result;
	}

	private static long measureTimerOverhead()
	{
		long[] samples = new long[10000];
		for (int i = 0; i < 10000; i++)
		{
			long start = System.nanoTime();
			samples[i] = System.nanoTime() - start;
		}
		Arrays.sort(samples);
		return samples[5000];
	}

	// ---- Benchmark runner ----

	@FunctionalInterface
	interface BenchFn
	{
		void run() throws Throwable;
	}

	private static String runBenchmark(String scenario, Integer dataSize, int warmup, int iterations, BenchFn fn) throws Throwable
	{
		String label = scenario + (dataSize != null ? "[" + dataSize + "]" : "");
		System.err.println("  Benchmark: " + label + " (" + warmup + " warmup + " + iterations + " iterations)...");
		System.err.flush();

		// Warmup phase
		for (int i = 0; i < warmup; i++)
		{
			try
			{
				fn.run();
			}
			catch (Throwable e)
			{
				throw new RuntimeException("Benchmark '" + scenario + "' warmup iteration " + i + ": " + e.getMessage(), e);
			}
		}

		// Measurement phase
		long[] rawNs = new long[iterations];
		for (int i = 0; i < iterations; i++)
		{
			long start = System.nanoTime();
			fn.run();
			rawNs[i] = System.nanoTime() - start;
		}

		// Sort for statistics
		long[] sortedNs = rawNs.clone();
		Arrays.sort(sortedNs);

		// Remove outliers and compute stats
		long[] cleaned = removeOutliersIQR(sortedNs);
		double[] stats = computeStats(cleaned);

		System.err.println("  Done: " + label + " (mean ~" + String.format("%.0f", stats[0]) + " ns)");

		// Build JSON fragment
		StringBuilder sb = new StringBuilder();
		sb.append("    {\n");
		sb.append("      \"scenario\": \"").append(scenario).append("\",\n");
		sb.append("      \"data_size\": ").append(dataSize == null ? "null" : dataSize).append(",\n");
		sb.append("      \"status\": \"PASS\",\n");

		// Raw iterations
		sb.append("      \"raw_iterations_ns\": [");
		for (int i = 0; i < rawNs.length; i++)
		{
			if (i > 0) sb.append(", ");
			sb.append(rawNs[i]);
		}
		sb.append("],\n");

		// Phases
		sb.append("      \"phases\": {\n");
		sb.append("        \"total\": {\n");
		sb.append("          \"mean_ns\": ").append(stats[0]).append(",\n");
		sb.append("          \"median_ns\": ").append(stats[1]).append(",\n");
		sb.append("          \"p95_ns\": ").append(stats[2]).append(",\n");
		sb.append("          \"p99_ns\": ").append(stats[3]).append(",\n");
		sb.append("          \"stddev_ns\": ").append(stats[4]).append(",\n");
		sb.append("          \"ci95_ns\": [").append(stats[5]).append(", ").append(stats[6]).append("]\n");
		sb.append("        }\n");
		sb.append("      }\n");
		sb.append("    }");
		return sb.toString();
	}

	private static String makeFailedResult(String scenario, Integer dataSize, String error)
	{
		StringBuilder sb = new StringBuilder();
		sb.append("    {\n");
		sb.append("      \"scenario\": \"").append(scenario).append("\",\n");
		sb.append("      \"data_size\": ").append(dataSize == null ? "null" : dataSize).append(",\n");
		sb.append("      \"status\": \"FAIL\",\n");
		sb.append("      \"error\": \"").append(error.replace("\"", "\\\"").replace("\n", "\\n")).append("\",\n");
		sb.append("      \"raw_iterations_ns\": [],\n");
		sb.append("      \"phases\": {}\n");
		sb.append("    }");
		return sb.toString();
	}

	/** Java callback for Go: add(a, b) -> a + b */
	public static long javaAdd(long a, long b)
	{
		return a + b;
	}

	/** Validate that an any_echo result has the expected collection length. */
	private static void validateAnyEchoResult(Object echoed, int expectedSize)
	{
		if (echoed instanceof Object[])
		{
			if (((Object[]) echoed).length != expectedSize)
			{
				throw new RuntimeException("any_echo: wrong Object[] length");
			}
		}
		else if (echoed instanceof java.util.List<?>)
		{
			if (((java.util.List<?>) echoed).size() != expectedSize)
			{
				throw new RuntimeException("any_echo: wrong List size");
			}
		}
		else
		{
			throw new RuntimeException("any_echo: unexpected return type " +
				(echoed == null ? "null" : echoed.getClass().getName()));
		}
	}

	// ---- Individual scenario benchmarks ----

	private void benchVoidCall(Set<String> filter, List<String> jsons, long timerOverhead) throws Throwable
	{
		if (!shouldRunScenario(filter, "void_call", null)) return;

		Caller noopFn = goModule.load("callable=NoOp", null, null);
		assertNotNull("Failed to load NoOp", noopFn);

		jsons.add(runBenchmark("void_call", null, WARMUP, ITERATIONS,
			() -> noopFn.call()));
		writeResults(jsons, timerOverhead);
		System.gc();
	}

	private void benchPrimitiveEcho(Set<String> filter, List<String> jsons, long timerOverhead) throws Throwable
	{
		if (!shouldRunScenario(filter, "primitive_echo", null)) return;

		Caller divFn = goModule.load("callable=DivIntegers",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64), t(MetaFFITypes.MetaFFIInt64)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIFloat64)});
		assertNotNull("Failed to load DivIntegers", divFn);

		jsons.add(runBenchmark("primitive_echo", null, WARMUP, ITERATIONS,
			() -> {
				Object[] result = divFn.call(10L, 2L);
				if (Math.abs((Double) result[0] - 5.0) > 1e-10)
				{
					throw new RuntimeException("DivIntegers: got " + result[0] + ", want 5.0");
				}
			}));
		writeResults(jsons, timerOverhead);
		System.gc();
	}

	private void benchStringEcho(Set<String> filter, List<String> jsons, long timerOverhead) throws Throwable
	{
		if (!shouldRunScenario(filter, "string_echo", null)) return;

		Caller joinFn = goModule.load("callable=JoinStrings",
			new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIString8Array, 1)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)});
		assertNotNull("Failed to load JoinStrings", joinFn);

		String[] joinArgs = new String[]{"hello", "world"};
		jsons.add(runBenchmark("string_echo", null, WARMUP, ITERATIONS,
			() -> {
				Object[] result = joinFn.call((Object) joinArgs);
				if (!"hello,world".equals(result[0]))
				{
					throw new RuntimeException("JoinStrings: got " + result[0]);
				}
			}));
		writeResults(jsons, timerOverhead);
		System.gc();
	}

	private void benchArrayEcho(Set<String> filter, List<String> jsons, long timerOverhead) throws Throwable
	{
		// Check if any array_echo size is requested
		boolean anyRequested = false;
		for (int s : new int[]{10, 100, 1000, 10000})
		{
			if (shouldRunScenario(filter, "array_echo", s)) anyRequested = true;
		}
		if (!anyRequested) return;

		Caller echoFn = goModule.load("callable=EchoBytes",
			new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIUInt8PackedArray, 1)},
			new MetaFFITypeInfo[]{arr(MetaFFITypes.MetaFFIUInt8PackedArray, 1)});
		assertNotNull("Failed to load EchoBytes", echoFn);

		for (int size : new int[]{10, 100, 1000, 10000})
		{
			if (!shouldRunScenario(filter, "array_echo", size)) continue;

			byte[] data = new byte[size];
			for (int i = 0; i < size; i++) data[i] = (byte) (i % 256);
			final byte[] finalData = data;
			final int finalSize = size;

			jsons.add(runBenchmark("array_echo", size, WARMUP, ITERATIONS,
				() -> {
					Object[] result = echoFn.call((Object) finalData);
					if (((byte[]) result[0]).length != finalSize)
					{
						throw new RuntimeException("EchoBytes: wrong length");
					}
				}));
			writeResults(jsons, timerOverhead);
			System.gc();
		}
	}

	private void benchObjectMethod(Set<String> filter, List<String> jsons, long timerOverhead) throws Throwable
	{
		if (!shouldRunScenario(filter, "object_method", null)) return;

		Caller newTestMap = goModule.load("callable=NewTestMap", null,
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)});
		Caller nameGetter = goModule.load("callable=TestMap.GetName",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIString8)});
		assertNotNull("Failed to load NewTestMap", newTestMap);
		assertNotNull("Failed to load TestMap.GetName", nameGetter);

		jsons.add(runBenchmark("object_method", null, WARMUP, ITERATIONS,
			() -> {
				Object[] mapResult = newTestMap.call();
				MetaFFIHandle handle = (MetaFFIHandle) mapResult[0];
				Object[] nameResult = nameGetter.call(handle);
				if (!"name1".equals(nameResult[0]))
				{
					throw new RuntimeException("TestMap.Name: got " + nameResult[0]);
				}
			}));
		writeResults(jsons, timerOverhead);
		System.gc();
	}

	private void benchErrorPropagation(Set<String> filter, List<String> jsons, long timerOverhead) throws Throwable
	{
		if (!shouldRunScenario(filter, "error_propagation", null)) return;

		Caller errFn = goModule.load("callable=ReturnsAnError", null, null);
		assertNotNull("Failed to load ReturnsAnError", errFn);

		jsons.add(runBenchmark("error_propagation", null, WARMUP, ITERATIONS,
			() -> {
				try
				{
					errFn.call();
					throw new RuntimeException("ReturnsAnError did not throw");
				}
				catch (RuntimeException re)
				{
					if (re.getMessage().equals("ReturnsAnError did not throw")) throw re;
					// Expected: Go error -> Java exception
				}
				catch (Throwable t)
				{
					// Expected: Go error -> Java throwable
				}
			}));
		writeResults(jsons, timerOverhead);
		System.gc();
	}

	private void benchCallback(Set<String> filter, List<String> jsons, long timerOverhead) throws Throwable
	{
		if (!shouldRunScenario(filter, "callback", null)) return;

		try
		{
			Caller callCb = goModule.load("callable=CallCallbackAdd",
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFICallable)},
				new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIInt64)});
			assertNotNull("Failed to load CallCallbackAdd", callCb);

			Method addMethod = TestBenchmark.class.getMethod("javaAdd", long.class, long.class);
			Caller javaAdder = MetaFFIRuntime.makeMetaFFICallable(addMethod);

			jsons.add(runBenchmark("callback", null, WARMUP, ITERATIONS,
				() -> {
					Object[] result = callCb.call(javaAdder);
					if ((Long) result[0] != 3L)
					{
						throw new RuntimeException("CallCallbackAdd: got " + result[0] + ", want 3");
					}
				}));
		}
		catch (Throwable e)
		{
			System.err.println("Callback scenario failed: " + e.getMessage());
			jsons.add(makeFailedResult("callback", null, e.getMessage()));
		}
		writeResults(jsons, timerOverhead);
		System.gc();
	}

	private void benchAnyEcho(Set<String> filter, List<String> jsons, long timerOverhead) throws Throwable
	{
		final int anyEchoSize = 100;
		if (!shouldRunScenario(filter, "any_echo", anyEchoSize)) return;

		Caller newTestMap = goModule.load("callable=NewTestMap", null,
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle)});
		Caller setFn = goModule.load("callable=TestMap.Set",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle), t(MetaFFITypes.MetaFFIString8), t(MetaFFITypes.MetaFFIAny)},
			null);
		Caller getFn = goModule.load("callable=TestMap.Get",
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIHandle), t(MetaFFITypes.MetaFFIString8)},
			new MetaFFITypeInfo[]{t(MetaFFITypes.MetaFFIAny)});
		assertNotNull("Failed to load NewTestMap", newTestMap);
		assertNotNull("Failed to load TestMap.Set", setFn);
		assertNotNull("Failed to load TestMap.Get", getFn);

		Object[] mapResult = newTestMap.call();
		MetaFFIHandle handle = (MetaFFIHandle) mapResult[0];
		final String key = "any_echo_payload";
		final Object[] pattern = new Object[]{1L, "two", 3.0};
		final Object[] payload = new Object[anyEchoSize];
		for (int i = 0; i < anyEchoSize; i++)
		{
			payload[i] = pattern[i % pattern.length];
		}

		jsons.add(runBenchmark("any_echo", anyEchoSize, WARMUP, ITERATIONS,
			() -> {
				setFn.call(handle, key, payload);
				Object[] out = getFn.call(handle, key);
				if (out == null || out.length == 0 || out[0] == null)
				{
					throw new RuntimeException("TestMap.Get(any_echo_payload): got null/empty return");
				}
				validateAnyEchoResult(out[0], anyEchoSize);
			}));
		writeResults(jsons, timerOverhead);
		System.gc();
	}

	// ---- Main benchmark test ----

	@Test
	public void testAllBenchmarks() throws Throwable
	{
		String mode = System.getenv().getOrDefault("METAFFI_TEST_MODE", "");
		if ("correctness".equals(mode))
		{
			System.err.println("Skipping benchmarks: METAFFI_TEST_MODE=correctness");
			return;
		}

		long timerOverhead = measureTimerOverhead();
		System.err.println("Timer overhead: " + timerOverhead + " ns");
		Set<String> scenarioFilter = parseScenarioFilter();
		if (scenarioFilter != null)
		{
			System.err.println("Scenario filter enabled: " + String.join(",", scenarioFilter));
		}

		List<String> benchmarkJsons = new ArrayList<>();

		// Run each scenario (each method handles its own filter check)
		benchVoidCall(scenarioFilter, benchmarkJsons, timerOverhead);
		benchPrimitiveEcho(scenarioFilter, benchmarkJsons, timerOverhead);
		benchStringEcho(scenarioFilter, benchmarkJsons, timerOverhead);
		benchArrayEcho(scenarioFilter, benchmarkJsons, timerOverhead);
		benchObjectMethod(scenarioFilter, benchmarkJsons, timerOverhead);
		benchErrorPropagation(scenarioFilter, benchmarkJsons, timerOverhead);
		benchCallback(scenarioFilter, benchmarkJsons, timerOverhead);
		benchAnyEcho(scenarioFilter, benchmarkJsons, timerOverhead);

		if (benchmarkJsons.isEmpty())
		{
			fail("METAFFI_TEST_SCENARIOS selected no benchmark scenarios: " + System.getenv("METAFFI_TEST_SCENARIOS"));
		}

		// Final write (in case no scenario triggered an intermediate save)
		writeResults(benchmarkJsons, timerOverhead);
	}

	private void writeResults(List<String> benchmarkJsons, long timerOverhead)
	{
		String resultPath = System.getenv().getOrDefault("METAFFI_TEST_RESULTS_FILE", "");
		if (resultPath.isEmpty())
		{
			String sourceRoot = System.getenv("METAFFI_SOURCE_ROOT");
			resultPath = sourceRoot + "/tests/results/java_to_go_metaffi.json";
		}

		// Build full JSON
		StringBuilder sb = new StringBuilder();
		sb.append("{\n");
		sb.append("  \"metadata\": {\n");
		sb.append("    \"host\": \"java\",\n");
		sb.append("    \"guest\": \"go\",\n");
		sb.append("    \"mechanism\": \"metaffi\",\n");
		sb.append("    \"timestamp\": \"").append(java.time.Instant.now().toString()).append("\",\n");
		sb.append("    \"environment\": {\n");
		sb.append("      \"os\": \"").append(System.getProperty("os.name").toLowerCase()).append("\",\n");
		sb.append("      \"arch\": \"").append(System.getProperty("os.arch")).append("\",\n");
		sb.append("      \"java_version\": \"").append(System.getProperty("java.version")).append("\"\n");
		sb.append("    },\n");
		sb.append("    \"config\": {\n");
		sb.append("      \"warmup_iterations\": ").append(WARMUP).append(",\n");
		sb.append("      \"measured_iterations\": ").append(ITERATIONS).append(",\n");
		sb.append("      \"timer_overhead_ns\": ").append(timerOverhead).append("\n");
		sb.append("    }\n");
		sb.append("  },\n");
		sb.append("  \"initialization\": {\n");
		sb.append("    \"load_runtime_plugin_ns\": ").append(loadRuntimePluginNs).append(",\n");
		sb.append("    \"load_module_ns\": ").append(loadModuleNs).append("\n");
		sb.append("  },\n");
		sb.append("  \"correctness\": null,\n");
		sb.append("  \"benchmarks\": [\n");

		for (int i = 0; i < benchmarkJsons.size(); i++)
		{
			if (i > 0) sb.append(",\n");
			sb.append(benchmarkJsons.get(i));
		}

		sb.append("\n  ]\n");
		sb.append("}\n");

		// Write to file
		try
		{
			File file = new File(resultPath);
			file.getParentFile().mkdirs();
			try (PrintWriter pw = new PrintWriter(new FileWriter(file)))
			{
				pw.print(sb.toString());
			}
			System.err.println("Results written to " + resultPath);
		}
		catch (Exception e)
		{
			System.err.println("Failed to write results: " + e.getMessage());
			fail("Failed to write benchmark results: " + e.getMessage());
		}
	}
}
