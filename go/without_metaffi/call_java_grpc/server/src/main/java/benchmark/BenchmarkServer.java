package benchmark;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.Status;
import io.grpc.stub.StreamObserver;
import com.google.protobuf.ListValue;
import com.google.protobuf.Value;

import java.io.IOException;
import java.util.List;
import java.util.function.IntBinaryOperator;

import guest.ArrayFunctions;
import guest.CoreFunctions;
import guest.SomeClass;

/**
 * gRPC server wrapping the Java guest module for benchmark scenarios.
 *
 * Usage:
 *   java -cp "server-all.jar;guest_java.jar" benchmark.BenchmarkServer [--port <port>]
 *
 * Prints "READY:<port>" to stdout when ready.
 */
public class BenchmarkServer extends BenchmarkServiceGrpc.BenchmarkServiceImplBase {

    // --- Scenario 1: void call ---
    @Override
    public void voidCall(BenchmarkProto.VoidCallRequest request,
                         StreamObserver<BenchmarkProto.VoidCallResponse> responseObserver) {
        CoreFunctions.noOp();
        responseObserver.onNext(BenchmarkProto.VoidCallResponse.getDefaultInstance());
        responseObserver.onCompleted();
    }

    // --- Scenario 2: primitive echo ---
    @Override
    public void divIntegers(BenchmarkProto.DivIntegersRequest request,
                            StreamObserver<BenchmarkProto.DivIntegersResponse> responseObserver) {
        double result = CoreFunctions.divIntegers(request.getX(), request.getY());
        responseObserver.onNext(BenchmarkProto.DivIntegersResponse.newBuilder()
                .setResult(result).build());
        responseObserver.onCompleted();
    }

    // --- Scenario 3: string echo ---
    @Override
    public void joinStrings(BenchmarkProto.JoinStringsRequest request,
                            StreamObserver<BenchmarkProto.JoinStringsResponse> responseObserver) {
        List<String> values = request.getValuesList();
        String[] arr = values.toArray(new String[0]);
        String result = CoreFunctions.joinStrings(arr);
        responseObserver.onNext(BenchmarkProto.JoinStringsResponse.newBuilder()
                .setResult(result).build());
        responseObserver.onCompleted();
    }

    // --- Scenario 4: array sum ---
    @Override
    public void arraySum(BenchmarkProto.ArraySumRequest request,
                         StreamObserver<BenchmarkProto.ArraySumResponse> responseObserver) {
        // Proto uses int64; Java sumRaggedArray uses int[][]. Convert.
        List<Long> values = request.getValuesList();
        int[] row = new int[values.size()];
        for (int i = 0; i < values.size(); i++) {
            row[i] = values.get(i).intValue();
        }
        int[][] arr = new int[][]{row};
        int sum = ArrayFunctions.sumRaggedArray(arr);
        responseObserver.onNext(BenchmarkProto.ArraySumResponse.newBuilder()
                .setSum(sum).build());
        responseObserver.onCompleted();
    }

    // --- Scenario 5: object method ---
    @Override
    public void objectMethod(BenchmarkProto.ObjectMethodRequest request,
                             StreamObserver<BenchmarkProto.ObjectMethodResponse> responseObserver) {
        SomeClass instance = new SomeClass(request.getName());
        String result = instance.print();
        responseObserver.onNext(BenchmarkProto.ObjectMethodResponse.newBuilder()
                .setResult(result).build());
        responseObserver.onCompleted();
    }

    // --- Scenario 6: callback (bidirectional streaming) ---
    @Override
    public StreamObserver<BenchmarkProto.CallbackClientMsg> callbackAdd(
            StreamObserver<BenchmarkProto.CallbackServerMsg> responseObserver) {
        return new StreamObserver<BenchmarkProto.CallbackClientMsg>() {
            @Override
            public void onNext(BenchmarkProto.CallbackClientMsg msg) {
                if (msg.hasInvoke()) {
                    // Ask client to compute add(1, 2)
                    responseObserver.onNext(BenchmarkProto.CallbackServerMsg.newBuilder()
                            .setCompute(BenchmarkProto.CallbackArgs.newBuilder()
                                    .setA(1).setB(2).build())
                            .build());

                } else if (msg.hasAddResult()) {
                    long result = msg.getAddResult();
                    if (result != 3) {
                        responseObserver.onError(Status.INTERNAL
                                .withDescription("callback: expected 3, got " + result)
                                .asRuntimeException());
                        return;
                    }
                    responseObserver.onNext(BenchmarkProto.CallbackServerMsg.newBuilder()
                            .setFinalResult(result)
                            .build());
                    responseObserver.onCompleted();
                }
            }

            @Override
            public void onError(Throwable t) {
                // Client error -- nothing to do
            }

            @Override
            public void onCompleted() {
                // Client done -- nothing to do
            }
        };
    }

    // --- Scenario 7: error propagation ---
    @Override
    public void returnsAnError(BenchmarkProto.Empty request,
                               StreamObserver<BenchmarkProto.Empty> responseObserver) {
        try {
            CoreFunctions.returnsAnError();
            // Should not reach here
            responseObserver.onNext(BenchmarkProto.Empty.getDefaultInstance());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onError(Status.INTERNAL
                    .withDescription(e.getMessage())
                    .asRuntimeException());
        }
    }

    // --- Scenario: dynamic any echo (mixed-type array payload) ---
    @Override
    public void anyEcho(BenchmarkProto.AnyEchoRequest request,
                        StreamObserver<BenchmarkProto.AnyEchoResponse> responseObserver) {
        ListValue values = request.getValues();
        if (values.getValuesCount() == 0) {
            responseObserver.onError(Status.INVALID_ARGUMENT
                    .withDescription("AnyEcho requires non-empty values")
                    .asRuntimeException());
            return;
        }

        Value.KindCase[] expected = new Value.KindCase[]{
                Value.KindCase.NUMBER_VALUE,
                Value.KindCase.STRING_VALUE,
                Value.KindCase.NUMBER_VALUE
        };
        for (int i = 0; i < expected.length; i++) {
            Value.KindCase got = values.getValues(i).getKindCase();
            if (got != expected[i]) {
                responseObserver.onError(Status.INVALID_ARGUMENT
                        .withDescription("AnyEcho type mismatch at index " + i + ": expected " + expected[i] + ", got " + got)
                        .asRuntimeException());
                return;
            }
        }

        responseObserver.onNext(BenchmarkProto.AnyEchoResponse.newBuilder()
                .setValues(values)
                .build());
        responseObserver.onCompleted();
    }

    // --- Entry point ---
    public static void main(String[] args) throws IOException, InterruptedException {
        int port = 0;
        for (int i = 0; i < args.length; i++) {
            if ("--port".equals(args[i]) && i + 1 < args.length) {
                port = Integer.parseInt(args[i + 1]);
            }
        }

        Server server = ServerBuilder.forPort(port)
                .addService(new BenchmarkServer())
                .build()
                .start();

        int actualPort = server.getPort();
        System.out.println("READY:" + actualPort);
        System.out.flush();

        server.awaitTermination();
    }
}
