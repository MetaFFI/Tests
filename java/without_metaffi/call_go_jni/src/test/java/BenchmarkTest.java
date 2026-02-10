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
 * Performance benchmarks: Java host -> Go guest via JNI + cgo.
 *
 * Uses GoBridge native methods backed by go_jni_bridge.dll.
 * Outputs results to tests/results/java_to_go_jni.json.
 */
public class BenchmarkTest
{
	private static int WARMUP;
	private static int ITERATIONS;

	@BeforeClass
	public static void setUp()
	{
		String sourceRoot = System.getenv("METAFFI_SOURCE_ROOT");
		assertNotNull("METAFFI_SOURCE_ROOT must be set", sourceRoot);

		WARMUP = parseIntEnv("METAFFI_TEST_WARMUP", 100);
		ITERATIONS = parseIntEnv("METAFFI_TEST_ITERATIONS", 10000);

		// Verify native library loads
		try
		{
			GoBridge.waitABit(0);
		}
		catch (UnsatisfiedLinkError e)
		{
			fail("Failed to load go_jni_bridge.dll: " + e.getMessage() +
				"\njava.library.path=" + System.getProperty("java.library.path"));
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
			() -> GoBridge.waitABit(0)));

		// --- Scenario 2: Primitive echo ---
		benchmarkJsons.add(runBenchmark("primitive_echo", null, WARMUP, ITERATIONS,
			() -> {
				double result = GoBridge.divIntegers(10, 2);
				if (Math.abs(result - 5.0) > 1e-10)
				{
					throw new RuntimeException("DivIntegers: got " + result + ", want 5.0");
				}
			}));

		// --- Scenario 3: String echo ---
		String[] joinArgs = new String[]{"hello", "world"};
		benchmarkJsons.add(runBenchmark("string_echo", null, WARMUP, ITERATIONS,
			() -> {
				String result = GoBridge.joinStrings(joinArgs);
				if (!"hello,world".equals(result))
				{
					throw new RuntimeException("JoinStrings: got " + result);
				}
			}));

		// --- Scenario 4: Array echo (varying sizes) ---
		for (int size : new int[]{10, 100, 1000, 10000})
		{
			byte[] data = new byte[size];
			for (int i = 0; i < size; i++) data[i] = (byte) (i % 256);
			final byte[] finalData = data;
			final int finalSize = size;

			benchmarkJsons.add(runBenchmark("array_echo", size, WARMUP, ITERATIONS,
				() -> {
					byte[] result = GoBridge.echoBytes(finalData);
					if (result.length != finalSize)
					{
						throw new RuntimeException("EchoBytes: wrong length " + result.length);
					}
				}));
		}

		// --- Scenario 5: Object create + method call ---
		benchmarkJsons.add(runBenchmark("object_method", null, WARMUP, ITERATIONS,
			() -> {
				long handle = GoBridge.newTestMap();
				String name = GoBridge.testMapGetName(handle);
				GoBridge.freeHandle(handle);
				if (!"name1".equals(name))
				{
					throw new RuntimeException("TestMap.Name: got " + name);
				}
			}));

		// --- Scenario 6: Callback ---
		try
		{
			benchmarkJsons.add(runBenchmark("callback", null, WARMUP, ITERATIONS,
				() -> {
					long result = GoBridge.callCallbackAdd((a, b) -> a + b);
					if (result != 3L)
					{
						throw new RuntimeException("CallCallbackAdd: got " + result + ", want 3");
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
				String err = GoBridge.returnsAnError();
				if (err == null)
				{
					throw new RuntimeException("ReturnsAnError did not return error");
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
			resultPath = sourceRoot + "/tests/results/java_to_go_jni.json";
		}

		StringBuilder sb = new StringBuilder();
		sb.append("{\n");
		sb.append("  \"metadata\": {\n");
		sb.append("    \"host\": \"java\",\n");
		sb.append("    \"guest\": \"go\",\n");
		sb.append("    \"mechanism\": \"jni\",\n");
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
		sb.append("  \"initialization\": null,\n");
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
