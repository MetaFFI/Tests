import benchmark.BenchmarkProto.*;
import benchmark.BenchmarkServiceGrpc;
import com.google.protobuf.ByteString;
import com.google.protobuf.ListValue;
import com.google.protobuf.Value;
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
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.Assert.*;

/**
 * Performance benchmarks: Java host -> Go guest via gRPC baseline.
 *
 * Starts the Go gRPC server (reuses the one built for Python3->Go tests),
 * runs 7 benchmark scenarios, writes results to java_to_go_grpc.json.
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

		// Start Go gRPC server
		String serverExe = sourceRoot.replace('\\', '/') +
			"/tests/python3/without_metaffi/call_go_grpc/server/server.exe";
		File serverFile = new File(serverExe);
		assertTrue("Go gRPC server not found at: " + serverExe, serverFile.exists());

		long startNs = System.nanoTime();
		ProcessBuilder pb = new ProcessBuilder(serverExe);
		pb.redirectErrorStream(false);
		serverProcess = pb.start();

		// Wait for "READY:<port>" on stdout
		BufferedReader reader = new BufferedReader(new InputStreamReader(serverProcess.getInputStream()));
		String line = reader.readLine();
		assertNotNull("Server process terminated without READY signal", line);
		assertTrue("Expected READY:<port>, got: " + line, line.startsWith("READY:"));
		int port = Integer.parseInt(line.substring("READY:".length()).trim());
		serverStartupNs = System.nanoTime() - startNs;

		System.err.println("Go gRPC server started on port " + port + " (startup: " + serverStartupNs / 1_000_000 + " ms)");

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

	private static Set<String> parseScenarioFilter()
	{
		String raw = System.getenv("METAFFI_TEST_SCENARIOS");
		if (raw == null || raw.trim().isEmpty())
		{
			return new HashSet<>();
		}

		Set<String> out = new HashSet<>();
		for (String part : raw.split(","))
		{
			String s = part.trim();
			if (!s.isEmpty())
			{
				out.add(s);
			}
		}
		return out;
	}

	private static String scenarioKey(String scenario, Integer dataSize)
	{
		return dataSize == null ? scenario : scenario + "_" + dataSize;
	}

	private static boolean shouldRunScenario(Set<String> filter, String scenario, Integer dataSize)
	{
		return filter.isEmpty() || filter.contains(scenarioKey(scenario, dataSize));
	}

	// ---- Statistical helpers (identical to MetaFFI benchmark) ----

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

		// Build JSON fragment
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
		Set<String> scenarioFilter = parseScenarioFilter();
		int selectedCount = 0;
		if (!scenarioFilter.isEmpty())
		{
			System.err.println("Scenario filter enabled: " + System.getenv("METAFFI_TEST_SCENARIOS"));
		}

		// --- Scenario 1: Void call ---
		if (shouldRunScenario(scenarioFilter, "void_call", null))
		{
			selectedCount++;
			benchmarkJsons.add(runBenchmark("void_call", null, WARMUP, ITERATIONS,
				() -> blockingStub.voidCall(VoidCallRequest.getDefaultInstance())));
		}

		// --- Scenario 2: Primitive echo ---
		if (shouldRunScenario(scenarioFilter, "primitive_echo", null))
		{
			selectedCount++;
			benchmarkJsons.add(runBenchmark("primitive_echo", null, WARMUP, ITERATIONS,
				() -> {
					DivIntegersResponse resp = blockingStub.divIntegers(
						DivIntegersRequest.newBuilder().setX(10).setY(2).build());
					if (Math.abs(resp.getResult() - 5.0) > 1e-10)
					{
						throw new RuntimeException("DivIntegers: got " + resp.getResult() + ", want 5.0");
					}
				}));
		}

		// --- Scenario 3: String echo ---
		if (shouldRunScenario(scenarioFilter, "string_echo", null))
		{
			selectedCount++;
			benchmarkJsons.add(runBenchmark("string_echo", null, WARMUP, ITERATIONS,
				() -> {
					JoinStringsResponse resp = blockingStub.joinStrings(
						JoinStringsRequest.newBuilder().addValues("hello").addValues("world").build());
					if (!"hello,world".equals(resp.getResult()))
					{
						throw new RuntimeException("JoinStrings: got " + resp.getResult());
					}
				}));
		}

		// --- Scenario 4: Array echo (varying sizes) ---
		for (int size : new int[]{10, 100, 1000, 10000})
		{
			if (!shouldRunScenario(scenarioFilter, "array_echo", size))
			{
				continue;
			}
			selectedCount++;

			byte[] data = new byte[size];
			for (int i = 0; i < size; i++) data[i] = (byte) (i % 256);
			final ByteString bsData = ByteString.copyFrom(data);
			final int finalSize = size;

			benchmarkJsons.add(runBenchmark("array_echo", size, WARMUP, ITERATIONS,
				() -> {
					EchoBytesResponse resp = blockingStub.echoBytes(
						EchoBytesRequest.newBuilder().setData(bsData).build());
					if (resp.getData().size() != finalSize)
					{
						throw new RuntimeException("EchoBytes: wrong length " + resp.getData().size());
					}
				}));
		}

		// --- Scenario: dynamic any echo (mixed array payload) ---
		final int anyEchoSize = 100;
		if (shouldRunScenario(scenarioFilter, "any_echo", anyEchoSize))
		{
			selectedCount++;
			ListValue.Builder values = ListValue.newBuilder();
			for (int i = 0; i < anyEchoSize; i++)
			{
				int mod = i % 3;
				if (mod == 0)
				{
					values.addValues(Value.newBuilder().setNumberValue(1).build());
				}
				else if (mod == 1)
				{
					values.addValues(Value.newBuilder().setStringValue("two").build());
				}
				else
				{
					values.addValues(Value.newBuilder().setNumberValue(3.0).build());
				}
			}

			final AnyEchoRequest req = AnyEchoRequest.newBuilder()
				.setValues(values.build())
				.build();

			benchmarkJsons.add(runBenchmark("any_echo", anyEchoSize, WARMUP, ITERATIONS,
				() -> {
					AnyEchoResponse resp = blockingStub.anyEcho(req);
					if (resp.getValues().getValuesCount() != anyEchoSize)
					{
						throw new RuntimeException("AnyEcho: got len " + resp.getValues().getValuesCount() + ", want " + anyEchoSize);
					}
				}));
		}

		// --- Scenario 5: Object method ---
		if (shouldRunScenario(scenarioFilter, "object_method", null))
		{
			selectedCount++;
			benchmarkJsons.add(runBenchmark("object_method", null, WARMUP, ITERATIONS,
				() -> {
					ObjectMethodResponse resp = blockingStub.objectMethod(
						ObjectMethodRequest.newBuilder().setName("bench").build());
					if (resp.getResult() == null || resp.getResult().isEmpty())
					{
						throw new RuntimeException("ObjectMethod: empty result");
					}
				}));
		}

		// --- Scenario 6: Callback via bidirectional streaming ---
		if (shouldRunScenario(scenarioFilter, "callback", null))
		{
			selectedCount++;
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
		}

		// --- Scenario 7: Error propagation ---
		if (shouldRunScenario(scenarioFilter, "error_propagation", null))
		{
			selectedCount++;
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
		}

		if (!scenarioFilter.isEmpty() && selectedCount == 0)
		{
			fail("METAFFI_TEST_SCENARIOS selected no benchmark scenarios: " + System.getenv("METAFFI_TEST_SCENARIOS"));
		}

		// --- Write results ---
		writeResults(benchmarkJsons, timerOverhead);
	}

	private void writeResults(List<String> benchmarkJsons, long timerOverhead)
	{
		String resultPath = System.getenv().getOrDefault("METAFFI_TEST_RESULTS_FILE", "");
		if (resultPath == null || resultPath.isEmpty())
		{
			String sourceRoot = System.getenv("METAFFI_SOURCE_ROOT");
			resultPath = sourceRoot + "/tests/results/java_to_go_grpc.json";
		}

		StringBuilder sb = new StringBuilder();
		sb.append("{\n");
		sb.append("  \"metadata\": {\n");
		sb.append("    \"host\": \"java\",\n");
		sb.append("    \"guest\": \"go\",\n");
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
