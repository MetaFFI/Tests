import benchmark.BenchmarkProto.*;
import benchmark.BenchmarkServiceGrpc;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import io.grpc.StatusRuntimeException;
import io.grpc.stub.StreamObserver;
import org.junit.AfterClass;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.Assert.*;

/**
 * Performance benchmarks: Java host -> Python3 guest via gRPC baseline.
 *
 * Starts the Python gRPC server (reuses the one built for Go->Python3 tests),
 * runs 7 benchmark scenarios, writes results to java_to_python3_grpc.json.
 */
public class BenchmarkTest
{
	private static Process serverProcess;
	private static ManagedChannel channel;
	private static BenchmarkServiceGrpc.BenchmarkServiceBlockingStub blockingStub;
	private static BenchmarkServiceGrpc.BenchmarkServiceStub asyncStub;
	private static long serverStartupNs;

	private static int WARMUP;
	private static int ITERATIONS;

	@BeforeClass
	public static void setUp() throws Exception
	{
		String sourceRoot = System.getenv("METAFFI_SOURCE_ROOT");
		assertNotNull("METAFFI_SOURCE_ROOT must be set", sourceRoot);

		WARMUP = parseIntEnv("METAFFI_TEST_WARMUP", 100);
		ITERATIONS = parseIntEnv("METAFFI_TEST_ITERATIONS", 10000);

		// Start Python gRPC server (reuse from go/without_metaffi/call_python3_grpc)
		String serverDir = sourceRoot.replace('\\', '/') +
			"/tests/go/without_metaffi/call_python3_grpc/server";
		String serverScript = serverDir + "/server.py";
		String modulePath = sourceRoot.replace('\\', '/') +
			"/sdk/test_modules/guest_modules/python3";

		assertTrue("Python gRPC server not found at: " + serverScript, new File(serverScript).exists());

		long startNs = System.nanoTime();
		ProcessBuilder pb = new ProcessBuilder("python", serverScript,
			"--module-path", modulePath);
		pb.directory(new File(serverDir));
		pb.redirectErrorStream(false);
		serverProcess = pb.start();

		// Wait for "READY:<port>" on stdout
		BufferedReader reader = new BufferedReader(new InputStreamReader(serverProcess.getInputStream()));
		String line = reader.readLine();
		assertNotNull("Server process terminated without READY signal", line);
		assertTrue("Expected READY:<port>, got: " + line, line.startsWith("READY:"));
		int port = Integer.parseInt(line.substring("READY:".length()).trim());
		serverStartupNs = System.nanoTime() - startNs;

		System.err.println("Python gRPC server started on port " + port + " (startup: " + serverStartupNs / 1_000_000 + " ms)");

		// Create gRPC channel
		channel = ManagedChannelBuilder.forAddress("127.0.0.1", port)
			.usePlaintext()
			.build();
		blockingStub = BenchmarkServiceGrpc.newBlockingStub(channel);
		asyncStub = BenchmarkServiceGrpc.newStub(channel);
	}

	@AfterClass
	public static void tearDown()
	{
		if (channel != null)
		{
			channel.shutdownNow();
			try { channel.awaitTermination(5, TimeUnit.SECONDS); } catch (InterruptedException ignored) {}
		}
		if (serverProcess != null)
		{
			serverProcess.destroyForcibly();
			try { serverProcess.waitFor(5, TimeUnit.SECONDS); } catch (InterruptedException ignored) {}
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

		// Warmup
		for (int i = 0; i < warmup; i++)
		{
			try { fn.run(); }
			catch (Throwable e)
			{
				throw new RuntimeException("Benchmark '" + scenario + "' warmup iteration " + i + ": " + e.getMessage(), e);
			}
		}

		// Measurement
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
			() -> blockingStub.voidCall(VoidCallRequest.newBuilder().setSecs(0).build())));

		// --- Scenario 2: Primitive echo ---
		benchmarkJsons.add(runBenchmark("primitive_echo", null, WARMUP, ITERATIONS,
			() -> {
				DivIntegersResponse resp = blockingStub.divIntegers(
					DivIntegersRequest.newBuilder().setX(10).setY(2).build());
				if (Math.abs(resp.getResult() - 5.0) > 1e-10)
				{
					throw new RuntimeException("DivIntegers: got " + resp.getResult() + ", want 5.0");
				}
			}));

		// --- Scenario 3: String echo ---
		benchmarkJsons.add(runBenchmark("string_echo", null, WARMUP, ITERATIONS,
			() -> {
				JoinStringsResponse resp = blockingStub.joinStrings(
					JoinStringsRequest.newBuilder().addValues("hello").addValues("world").build());
				if (!"hello,world".equals(resp.getResult()))
				{
					throw new RuntimeException("JoinStrings: got " + resp.getResult());
				}
			}));

		// --- Scenario 4: Array sum (varying sizes) ---
		for (int size : new int[]{10, 100, 1000, 10000})
		{
			ArraySumRequest.Builder reqBuilder = ArraySumRequest.newBuilder();
			long expectedSum = 0;
			for (int i = 1; i <= size; i++)
			{
				reqBuilder.addValues(i);
				expectedSum += i;
			}
			final ArraySumRequest req = reqBuilder.build();
			final long expectedSumFinal = expectedSum;

			benchmarkJsons.add(runBenchmark("array_sum", size, WARMUP, ITERATIONS,
				() -> {
					ArraySumResponse resp = blockingStub.arraySum(req);
					if (resp.getSum() != expectedSumFinal)
					{
						throw new RuntimeException("ArraySum: got " + resp.getSum() + ", want " + expectedSumFinal);
					}
				}));
		}

		// --- Scenario 5: Object method ---
		benchmarkJsons.add(runBenchmark("object_method", null, WARMUP, ITERATIONS,
			() -> {
				ObjectMethodResponse resp = blockingStub.objectMethod(
					ObjectMethodRequest.newBuilder().setName("bench").build());
				if (resp.getResult() == null || resp.getResult().isEmpty())
				{
					throw new RuntimeException("ObjectMethod: empty result");
				}
			}));

		// --- Scenario 6: Callback via bidirectional streaming ---
		try
		{
			benchmarkJsons.add(runBenchmark("callback", null, WARMUP, ITERATIONS,
				() -> {
					CountDownLatch doneLatch = new CountDownLatch(1);
					AtomicLong finalResult = new AtomicLong(-1);
					AtomicReference<Throwable> error = new AtomicReference<>();
					AtomicReference<StreamObserver<CallbackClientMsg>> reqHolder = new AtomicReference<>();

					StreamObserver<CallbackClientMsg> requestObserver = asyncStub.callbackAdd(
						new StreamObserver<CallbackServerMsg>()
						{
							@Override
							public void onNext(CallbackServerMsg msg)
							{
								if (msg.hasCompute())
								{
									long result = msg.getCompute().getA() + msg.getCompute().getB();
									StreamObserver<CallbackClientMsg> req = reqHolder.get();
									req.onNext(CallbackClientMsg.newBuilder().setAddResult(result).build());
									req.onCompleted();
								}
								else if (msg.hasFinalResult())
								{
									finalResult.set(msg.getFinalResult());
								}
							}

							@Override
							public void onError(Throwable t) { error.set(t); doneLatch.countDown(); }

							@Override
							public void onCompleted() { doneLatch.countDown(); }
						});

					reqHolder.set(requestObserver);
					requestObserver.onNext(CallbackClientMsg.newBuilder().setInvoke(true).build());

					assertTrue("Callback timed out", doneLatch.await(10, TimeUnit.SECONDS));
					if (error.get() != null) throw error.get();
					if (finalResult.get() != 3L)
					{
						throw new RuntimeException("Callback: got " + finalResult.get() + ", want 3");
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
					blockingStub.returnsAnError(Empty.newBuilder().build());
					throw new RuntimeException("ReturnsAnError did not throw");
				}
				catch (StatusRuntimeException e)
				{
					// Expected: gRPC INTERNAL error
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
			resultPath = sourceRoot + "/tests/results/java_to_python3_grpc.json";
		}

		StringBuilder sb = new StringBuilder();
		sb.append("{\n");
		sb.append("  \"metadata\": {\n");
		sb.append("    \"host\": \"java\",\n");
		sb.append("    \"guest\": \"python3\",\n");
		sb.append("    \"mechanism\": \"grpc\",\n");
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
		sb.append("    \"server_startup_ns\": ").append(serverStartupNs).append("\n");
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
