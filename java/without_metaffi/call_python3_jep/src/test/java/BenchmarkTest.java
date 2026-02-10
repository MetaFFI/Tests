import jep.Interpreter;
import jep.SharedInterpreter;
import jep.JepException;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.junit.Assert.*;

/**
 * Performance benchmarks: Java host -> Python3 guest via Jep (embedded CPython).
 *
 * Uses Jep SharedInterpreter to call Python functions directly from Java.
 * Outputs results to tests/results/java_to_python3_jep.json.
 */
public class BenchmarkTest
{
	private static Interpreter interp;
	private static long interpStartupNs;

	private static int WARMUP;
	private static int ITERATIONS;

	@BeforeClass
	public static void setUp() throws Exception
	{
		String sourceRoot = System.getenv("METAFFI_SOURCE_ROOT");
		assertNotNull("METAFFI_SOURCE_ROOT must be set", sourceRoot);

		WARMUP = parseIntEnv("METAFFI_TEST_WARMUP", 100);
		ITERATIONS = parseIntEnv("METAFFI_TEST_ITERATIONS", 10000);

		// Start Jep interpreter and import guest module
		long startNs = System.nanoTime();

		interp = new SharedInterpreter();
		interp.exec("import sys");

		String modulePath = sourceRoot.replace('\\', '/') +
			"/sdk/test_modules/guest_modules/python3";
		interp.exec("sys.path.insert(0, '" + modulePath + "')");

		// Import guest module functions
		interp.exec("from module.core_functions import (wait_a_bit, div_integers, " +
			"join_strings, call_callback_add, returns_an_error)");
		interp.exec("from module.objects_and_classes import SomeClass, TestMap");
		interp.exec("from module.types_and_arrays import accepts_ragged_array");

		interpStartupNs = System.nanoTime() - startNs;
		System.err.println("Jep interpreter started (startup: " + interpStartupNs / 1_000_000 + " ms)");
	}

	@AfterClass
	public static void tearDown()
	{
		if (interp != null)
		{
			try { interp.close(); } catch (Exception ignored) {}
			interp = null;
		}
	}

	private static int parseIntEnv(String name, int defaultValue)
	{
		String val = System.getenv(name);
		if (val == null || val.isEmpty()) return defaultValue;
		return Integer.parseInt(val);
	}

	// ---- Statistical helpers ----

	private static double[] computeStats(long[] sortedNs)
	{
		int n = sortedNs.length;
		if (n == 0) return new double[]{0, 0, 0, 0, 0, 0, 0};

		double sum = 0;
		for (long v : sortedNs) sum += v;
		double mean = sum / n;

		double median = (n % 2 == 1) ? sortedNs[n / 2] : (sortedNs[n / 2 - 1] + sortedNs[n / 2]) / 2.0;
		double p95 = sortedNs[(int) (n * 0.95)];
		double p99 = sortedNs[Math.min((int) (n * 0.99), n - 1)];

		double sqDiffSum = 0;
		for (long v : sortedNs) sqDiffSum += (v - mean) * (v - mean);
		double stddev = Math.sqrt(sqDiffSum / n);
		double se = stddev / Math.sqrt(n);

		return new double[]{mean, median, p95, p99, stddev, mean - 1.96 * se, mean + 1.96 * se};
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
			if (v >= lower && v <= upper) cleaned.add(v);
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
	interface BenchFn { void run() throws Throwable; }

	private static String runBenchmark(String scenario, Integer dataSize, int warmup, int iterations, BenchFn fn) throws Throwable
	{
		String label = scenario + (dataSize != null ? "[" + dataSize + "]" : "");
		System.err.println("  Benchmark: " + label + " (" + warmup + " warmup + " + iterations + " iterations)...");
		System.err.flush();

		for (int i = 0; i < warmup; i++)
		{
			try { fn.run(); }
			catch (Throwable e)
			{
				throw new RuntimeException("Benchmark '" + scenario + "' warmup iteration " + i + ": " + e.getMessage(), e);
			}
		}

		long[] rawNs = new long[iterations];
		for (int i = 0; i < iterations; i++)
		{
			long start = System.nanoTime();
			fn.run();
			rawNs[i] = System.nanoTime() - start;
		}

		long[] sortedNs = rawNs.clone();
		Arrays.sort(sortedNs);
		long[] cleaned = removeOutliersIQR(sortedNs);
		double[] stats = computeStats(cleaned);

		System.err.println("  Done: " + label + " (mean ~" + String.format("%.0f", stats[0]) + " ns)");

		StringBuilder sb = new StringBuilder();
		sb.append("    {\n");
		sb.append("      \"scenario\": \"").append(scenario).append("\",\n");
		sb.append("      \"data_size\": ").append(dataSize == null ? "null" : dataSize).append(",\n");
		sb.append("      \"status\": \"PASS\",\n");
		sb.append("      \"raw_iterations_ns\": [");
		for (int i = 0; i < rawNs.length; i++)
		{
			if (i > 0) sb.append(", ");
			sb.append(rawNs[i]);
		}
		sb.append("],\n");
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

		List<String> benchmarkJsons = new ArrayList<>();

		// --- Scenario 1: Void call ---
		benchmarkJsons.add(runBenchmark("void_call", null, WARMUP, ITERATIONS,
			() -> interp.exec("wait_a_bit(0)")));

		// --- Scenario 2: Primitive echo ---
		benchmarkJsons.add(runBenchmark("primitive_echo", null, WARMUP, ITERATIONS,
			() -> {
				interp.exec("_r = div_integers(10, 2)");
				Object result = interp.getValue("_r");
				double val = ((Number) result).doubleValue();
				if (Math.abs(val - 5.0) > 1e-10)
				{
					throw new RuntimeException("div_integers: got " + val + ", want 5.0");
				}
			}));

		// --- Scenario 3: String echo ---
		benchmarkJsons.add(runBenchmark("string_echo", null, WARMUP, ITERATIONS,
			() -> {
				interp.exec("_r = join_strings(['hello', 'world'])");
				String result = (String) interp.getValue("_r");
				if (!"hello,world".equals(result))
				{
					throw new RuntimeException("join_strings: got " + result);
				}
			}));

		// --- Scenario 4: Array sum (varying sizes) ---
		for (int size : new int[]{10, 100, 1000, 10000})
		{
			// Pre-create the Python list for this size
			interp.exec("_arr_" + size + " = [[i+1 for i in range(" + size + ")]]");
			long expectedSum = (long) size * (size + 1) / 2;
			final long expected = expectedSum;
			final String arrName = "_arr_" + size;

			benchmarkJsons.add(runBenchmark("array_sum", size, WARMUP, ITERATIONS,
				() -> {
					interp.exec("_r = accepts_ragged_array(" + arrName + ")");
					Object result = interp.getValue("_r");
					long val = ((Number) result).longValue();
					if (val != expected)
					{
						throw new RuntimeException("array_sum: got " + val + ", want " + expected);
					}
				}));
		}

		// --- Scenario 5: Object method ---
		benchmarkJsons.add(runBenchmark("object_method", null, WARMUP, ITERATIONS,
			() -> {
				interp.exec("_obj = SomeClass('bench')");
				interp.exec("_r = _obj.print()");
				String result = (String) interp.getValue("_r");
				if (result == null || !result.contains("bench"))
				{
					throw new RuntimeException("SomeClass.print: got " + result);
				}
			}));

		// --- Scenario 6: Callback ---
		try
		{
			// Define a Python callback function that adds two numbers
			interp.exec("def _java_add(a, b): return a + b");

			benchmarkJsons.add(runBenchmark("callback", null, WARMUP, ITERATIONS,
				() -> {
					interp.exec("_r = call_callback_add(_java_add)");
					Object result = interp.getValue("_r");
					long val = ((Number) result).longValue();
					if (val != 3L)
					{
						throw new RuntimeException("call_callback_add: got " + val + ", want 3");
					}
				}));
		}
		catch (Throwable e)
		{
			System.err.println("Callback scenario failed: " + e.getMessage());
			benchmarkJsons.add(makeFailedResult("callback", null, e.getMessage()));
		}

		// --- Scenario 7: Error propagation ---
		benchmarkJsons.add(runBenchmark("error_propagation", null, WARMUP, ITERATIONS,
			() -> {
				try
				{
					interp.exec("returns_an_error()");
					throw new RuntimeException("returns_an_error did not throw");
				}
				catch (JepException e)
				{
					// Expected: Python error -> JepException
				}
			}));

		// --- Write results ---
		writeResults(benchmarkJsons, timerOverhead);
	}

	private void writeResults(List<String> benchmarkJsons, long timerOverhead)
	{
		String resultPath = System.getenv().getOrDefault("METAFFI_TEST_RESULTS_FILE", "");
		if (resultPath == null || resultPath.isEmpty())
		{
			String sourceRoot = System.getenv("METAFFI_SOURCE_ROOT");
			resultPath = sourceRoot + "/tests/results/java_to_python3_jep.json";
		}

		StringBuilder sb = new StringBuilder();
		sb.append("{\n");
		sb.append("  \"metadata\": {\n");
		sb.append("    \"host\": \"java\",\n");
		sb.append("    \"guest\": \"python3\",\n");
		sb.append("    \"mechanism\": \"jep\",\n");
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
		sb.append("    \"interpreter_startup_ns\": ").append(interpStartupNs).append("\n");
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
