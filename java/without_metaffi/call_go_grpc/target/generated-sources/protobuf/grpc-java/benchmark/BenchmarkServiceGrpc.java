package benchmark;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 * <pre>
 * BenchmarkService wraps the Go guest module for cross-language benchmarking.
 * Each RPC maps to one of the 7 benchmark scenarios.
 * </pre>
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.62.2)",
    comments = "Source: benchmark.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class BenchmarkServiceGrpc {

  private BenchmarkServiceGrpc() {}

  public static final java.lang.String SERVICE_NAME = "benchmark.BenchmarkService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<benchmark.BenchmarkProto.VoidCallRequest,
      benchmark.BenchmarkProto.VoidCallResponse> getVoidCallMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "VoidCall",
      requestType = benchmark.BenchmarkProto.VoidCallRequest.class,
      responseType = benchmark.BenchmarkProto.VoidCallResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<benchmark.BenchmarkProto.VoidCallRequest,
      benchmark.BenchmarkProto.VoidCallResponse> getVoidCallMethod() {
    io.grpc.MethodDescriptor<benchmark.BenchmarkProto.VoidCallRequest, benchmark.BenchmarkProto.VoidCallResponse> getVoidCallMethod;
    if ((getVoidCallMethod = BenchmarkServiceGrpc.getVoidCallMethod) == null) {
      synchronized (BenchmarkServiceGrpc.class) {
        if ((getVoidCallMethod = BenchmarkServiceGrpc.getVoidCallMethod) == null) {
          BenchmarkServiceGrpc.getVoidCallMethod = getVoidCallMethod =
              io.grpc.MethodDescriptor.<benchmark.BenchmarkProto.VoidCallRequest, benchmark.BenchmarkProto.VoidCallResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "VoidCall"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.VoidCallRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.VoidCallResponse.getDefaultInstance()))
              .setSchemaDescriptor(new BenchmarkServiceMethodDescriptorSupplier("VoidCall"))
              .build();
        }
      }
    }
    return getVoidCallMethod;
  }

  private static volatile io.grpc.MethodDescriptor<benchmark.BenchmarkProto.DivIntegersRequest,
      benchmark.BenchmarkProto.DivIntegersResponse> getDivIntegersMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "DivIntegers",
      requestType = benchmark.BenchmarkProto.DivIntegersRequest.class,
      responseType = benchmark.BenchmarkProto.DivIntegersResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<benchmark.BenchmarkProto.DivIntegersRequest,
      benchmark.BenchmarkProto.DivIntegersResponse> getDivIntegersMethod() {
    io.grpc.MethodDescriptor<benchmark.BenchmarkProto.DivIntegersRequest, benchmark.BenchmarkProto.DivIntegersResponse> getDivIntegersMethod;
    if ((getDivIntegersMethod = BenchmarkServiceGrpc.getDivIntegersMethod) == null) {
      synchronized (BenchmarkServiceGrpc.class) {
        if ((getDivIntegersMethod = BenchmarkServiceGrpc.getDivIntegersMethod) == null) {
          BenchmarkServiceGrpc.getDivIntegersMethod = getDivIntegersMethod =
              io.grpc.MethodDescriptor.<benchmark.BenchmarkProto.DivIntegersRequest, benchmark.BenchmarkProto.DivIntegersResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "DivIntegers"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.DivIntegersRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.DivIntegersResponse.getDefaultInstance()))
              .setSchemaDescriptor(new BenchmarkServiceMethodDescriptorSupplier("DivIntegers"))
              .build();
        }
      }
    }
    return getDivIntegersMethod;
  }

  private static volatile io.grpc.MethodDescriptor<benchmark.BenchmarkProto.JoinStringsRequest,
      benchmark.BenchmarkProto.JoinStringsResponse> getJoinStringsMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "JoinStrings",
      requestType = benchmark.BenchmarkProto.JoinStringsRequest.class,
      responseType = benchmark.BenchmarkProto.JoinStringsResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<benchmark.BenchmarkProto.JoinStringsRequest,
      benchmark.BenchmarkProto.JoinStringsResponse> getJoinStringsMethod() {
    io.grpc.MethodDescriptor<benchmark.BenchmarkProto.JoinStringsRequest, benchmark.BenchmarkProto.JoinStringsResponse> getJoinStringsMethod;
    if ((getJoinStringsMethod = BenchmarkServiceGrpc.getJoinStringsMethod) == null) {
      synchronized (BenchmarkServiceGrpc.class) {
        if ((getJoinStringsMethod = BenchmarkServiceGrpc.getJoinStringsMethod) == null) {
          BenchmarkServiceGrpc.getJoinStringsMethod = getJoinStringsMethod =
              io.grpc.MethodDescriptor.<benchmark.BenchmarkProto.JoinStringsRequest, benchmark.BenchmarkProto.JoinStringsResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "JoinStrings"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.JoinStringsRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.JoinStringsResponse.getDefaultInstance()))
              .setSchemaDescriptor(new BenchmarkServiceMethodDescriptorSupplier("JoinStrings"))
              .build();
        }
      }
    }
    return getJoinStringsMethod;
  }

  private static volatile io.grpc.MethodDescriptor<benchmark.BenchmarkProto.EchoBytesRequest,
      benchmark.BenchmarkProto.EchoBytesResponse> getEchoBytesMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "EchoBytes",
      requestType = benchmark.BenchmarkProto.EchoBytesRequest.class,
      responseType = benchmark.BenchmarkProto.EchoBytesResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<benchmark.BenchmarkProto.EchoBytesRequest,
      benchmark.BenchmarkProto.EchoBytesResponse> getEchoBytesMethod() {
    io.grpc.MethodDescriptor<benchmark.BenchmarkProto.EchoBytesRequest, benchmark.BenchmarkProto.EchoBytesResponse> getEchoBytesMethod;
    if ((getEchoBytesMethod = BenchmarkServiceGrpc.getEchoBytesMethod) == null) {
      synchronized (BenchmarkServiceGrpc.class) {
        if ((getEchoBytesMethod = BenchmarkServiceGrpc.getEchoBytesMethod) == null) {
          BenchmarkServiceGrpc.getEchoBytesMethod = getEchoBytesMethod =
              io.grpc.MethodDescriptor.<benchmark.BenchmarkProto.EchoBytesRequest, benchmark.BenchmarkProto.EchoBytesResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "EchoBytes"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.EchoBytesRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.EchoBytesResponse.getDefaultInstance()))
              .setSchemaDescriptor(new BenchmarkServiceMethodDescriptorSupplier("EchoBytes"))
              .build();
        }
      }
    }
    return getEchoBytesMethod;
  }

  private static volatile io.grpc.MethodDescriptor<benchmark.BenchmarkProto.ObjectMethodRequest,
      benchmark.BenchmarkProto.ObjectMethodResponse> getObjectMethodMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ObjectMethod",
      requestType = benchmark.BenchmarkProto.ObjectMethodRequest.class,
      responseType = benchmark.BenchmarkProto.ObjectMethodResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<benchmark.BenchmarkProto.ObjectMethodRequest,
      benchmark.BenchmarkProto.ObjectMethodResponse> getObjectMethodMethod() {
    io.grpc.MethodDescriptor<benchmark.BenchmarkProto.ObjectMethodRequest, benchmark.BenchmarkProto.ObjectMethodResponse> getObjectMethodMethod;
    if ((getObjectMethodMethod = BenchmarkServiceGrpc.getObjectMethodMethod) == null) {
      synchronized (BenchmarkServiceGrpc.class) {
        if ((getObjectMethodMethod = BenchmarkServiceGrpc.getObjectMethodMethod) == null) {
          BenchmarkServiceGrpc.getObjectMethodMethod = getObjectMethodMethod =
              io.grpc.MethodDescriptor.<benchmark.BenchmarkProto.ObjectMethodRequest, benchmark.BenchmarkProto.ObjectMethodResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ObjectMethod"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.ObjectMethodRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.ObjectMethodResponse.getDefaultInstance()))
              .setSchemaDescriptor(new BenchmarkServiceMethodDescriptorSupplier("ObjectMethod"))
              .build();
        }
      }
    }
    return getObjectMethodMethod;
  }

  private static volatile io.grpc.MethodDescriptor<benchmark.BenchmarkProto.CallbackClientMsg,
      benchmark.BenchmarkProto.CallbackServerMsg> getCallbackAddMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "CallbackAdd",
      requestType = benchmark.BenchmarkProto.CallbackClientMsg.class,
      responseType = benchmark.BenchmarkProto.CallbackServerMsg.class,
      methodType = io.grpc.MethodDescriptor.MethodType.BIDI_STREAMING)
  public static io.grpc.MethodDescriptor<benchmark.BenchmarkProto.CallbackClientMsg,
      benchmark.BenchmarkProto.CallbackServerMsg> getCallbackAddMethod() {
    io.grpc.MethodDescriptor<benchmark.BenchmarkProto.CallbackClientMsg, benchmark.BenchmarkProto.CallbackServerMsg> getCallbackAddMethod;
    if ((getCallbackAddMethod = BenchmarkServiceGrpc.getCallbackAddMethod) == null) {
      synchronized (BenchmarkServiceGrpc.class) {
        if ((getCallbackAddMethod = BenchmarkServiceGrpc.getCallbackAddMethod) == null) {
          BenchmarkServiceGrpc.getCallbackAddMethod = getCallbackAddMethod =
              io.grpc.MethodDescriptor.<benchmark.BenchmarkProto.CallbackClientMsg, benchmark.BenchmarkProto.CallbackServerMsg>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.BIDI_STREAMING)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "CallbackAdd"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.CallbackClientMsg.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.CallbackServerMsg.getDefaultInstance()))
              .setSchemaDescriptor(new BenchmarkServiceMethodDescriptorSupplier("CallbackAdd"))
              .build();
        }
      }
    }
    return getCallbackAddMethod;
  }

  private static volatile io.grpc.MethodDescriptor<benchmark.BenchmarkProto.Empty,
      benchmark.BenchmarkProto.Empty> getReturnsAnErrorMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ReturnsAnError",
      requestType = benchmark.BenchmarkProto.Empty.class,
      responseType = benchmark.BenchmarkProto.Empty.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<benchmark.BenchmarkProto.Empty,
      benchmark.BenchmarkProto.Empty> getReturnsAnErrorMethod() {
    io.grpc.MethodDescriptor<benchmark.BenchmarkProto.Empty, benchmark.BenchmarkProto.Empty> getReturnsAnErrorMethod;
    if ((getReturnsAnErrorMethod = BenchmarkServiceGrpc.getReturnsAnErrorMethod) == null) {
      synchronized (BenchmarkServiceGrpc.class) {
        if ((getReturnsAnErrorMethod = BenchmarkServiceGrpc.getReturnsAnErrorMethod) == null) {
          BenchmarkServiceGrpc.getReturnsAnErrorMethod = getReturnsAnErrorMethod =
              io.grpc.MethodDescriptor.<benchmark.BenchmarkProto.Empty, benchmark.BenchmarkProto.Empty>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ReturnsAnError"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.Empty.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.Empty.getDefaultInstance()))
              .setSchemaDescriptor(new BenchmarkServiceMethodDescriptorSupplier("ReturnsAnError"))
              .build();
        }
      }
    }
    return getReturnsAnErrorMethod;
  }

  private static volatile io.grpc.MethodDescriptor<benchmark.BenchmarkProto.AnyEchoRequest,
      benchmark.BenchmarkProto.AnyEchoResponse> getAnyEchoMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "AnyEcho",
      requestType = benchmark.BenchmarkProto.AnyEchoRequest.class,
      responseType = benchmark.BenchmarkProto.AnyEchoResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<benchmark.BenchmarkProto.AnyEchoRequest,
      benchmark.BenchmarkProto.AnyEchoResponse> getAnyEchoMethod() {
    io.grpc.MethodDescriptor<benchmark.BenchmarkProto.AnyEchoRequest, benchmark.BenchmarkProto.AnyEchoResponse> getAnyEchoMethod;
    if ((getAnyEchoMethod = BenchmarkServiceGrpc.getAnyEchoMethod) == null) {
      synchronized (BenchmarkServiceGrpc.class) {
        if ((getAnyEchoMethod = BenchmarkServiceGrpc.getAnyEchoMethod) == null) {
          BenchmarkServiceGrpc.getAnyEchoMethod = getAnyEchoMethod =
              io.grpc.MethodDescriptor.<benchmark.BenchmarkProto.AnyEchoRequest, benchmark.BenchmarkProto.AnyEchoResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "AnyEcho"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.AnyEchoRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  benchmark.BenchmarkProto.AnyEchoResponse.getDefaultInstance()))
              .setSchemaDescriptor(new BenchmarkServiceMethodDescriptorSupplier("AnyEcho"))
              .build();
        }
      }
    }
    return getAnyEchoMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static BenchmarkServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<BenchmarkServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<BenchmarkServiceStub>() {
        @java.lang.Override
        public BenchmarkServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new BenchmarkServiceStub(channel, callOptions);
        }
      };
    return BenchmarkServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static BenchmarkServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<BenchmarkServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<BenchmarkServiceBlockingStub>() {
        @java.lang.Override
        public BenchmarkServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new BenchmarkServiceBlockingStub(channel, callOptions);
        }
      };
    return BenchmarkServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static BenchmarkServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<BenchmarkServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<BenchmarkServiceFutureStub>() {
        @java.lang.Override
        public BenchmarkServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new BenchmarkServiceFutureStub(channel, callOptions);
        }
      };
    return BenchmarkServiceFutureStub.newStub(factory, channel);
  }

  /**
   * <pre>
   * BenchmarkService wraps the Go guest module for cross-language benchmarking.
   * Each RPC maps to one of the 7 benchmark scenarios.
   * </pre>
   */
  public interface AsyncService {

    /**
     * <pre>
     * Scenario 1: void call (WaitABit(0))
     * </pre>
     */
    default void voidCall(benchmark.BenchmarkProto.VoidCallRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.VoidCallResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getVoidCallMethod(), responseObserver);
    }

    /**
     * <pre>
     * Scenario 2: primitive echo (DivIntegers(10, 2) -&gt; 5.0)
     * </pre>
     */
    default void divIntegers(benchmark.BenchmarkProto.DivIntegersRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.DivIntegersResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getDivIntegersMethod(), responseObserver);
    }

    /**
     * <pre>
     * Scenario 3: string echo (JoinStrings(["hello","world"]) -&gt; "hello,world")
     * </pre>
     */
    default void joinStrings(benchmark.BenchmarkProto.JoinStringsRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.JoinStringsResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getJoinStringsMethod(), responseObserver);
    }

    /**
     * <pre>
     * Scenario 4: array echo (EchoBytes(data) -&gt; data)
     * </pre>
     */
    default void echoBytes(benchmark.BenchmarkProto.EchoBytesRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.EchoBytesResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getEchoBytesMethod(), responseObserver);
    }

    /**
     * <pre>
     * Scenario 5: object method (NewTestMap() + GetName())
     * </pre>
     */
    default void objectMethod(benchmark.BenchmarkProto.ObjectMethodRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.ObjectMethodResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getObjectMethodMethod(), responseObserver);
    }

    /**
     * <pre>
     * Scenario 6: callback via bidirectional streaming
     * </pre>
     */
    default io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.CallbackClientMsg> callbackAdd(
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.CallbackServerMsg> responseObserver) {
      return io.grpc.stub.ServerCalls.asyncUnimplementedStreamingCall(getCallbackAddMethod(), responseObserver);
    }

    /**
     * <pre>
     * Scenario 7: error propagation (ReturnsAnError() -&gt; gRPC INTERNAL error)
     * </pre>
     */
    default void returnsAnError(benchmark.BenchmarkProto.Empty request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.Empty> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getReturnsAnErrorMethod(), responseObserver);
    }

    /**
     * <pre>
     * Scenario: dynamic any echo (mixed array payload)
     * </pre>
     */
    default void anyEcho(benchmark.BenchmarkProto.AnyEchoRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.AnyEchoResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getAnyEchoMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service BenchmarkService.
   * <pre>
   * BenchmarkService wraps the Go guest module for cross-language benchmarking.
   * Each RPC maps to one of the 7 benchmark scenarios.
   * </pre>
   */
  public static abstract class BenchmarkServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return BenchmarkServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service BenchmarkService.
   * <pre>
   * BenchmarkService wraps the Go guest module for cross-language benchmarking.
   * Each RPC maps to one of the 7 benchmark scenarios.
   * </pre>
   */
  public static final class BenchmarkServiceStub
      extends io.grpc.stub.AbstractAsyncStub<BenchmarkServiceStub> {
    private BenchmarkServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected BenchmarkServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new BenchmarkServiceStub(channel, callOptions);
    }

    /**
     * <pre>
     * Scenario 1: void call (WaitABit(0))
     * </pre>
     */
    public void voidCall(benchmark.BenchmarkProto.VoidCallRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.VoidCallResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getVoidCallMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Scenario 2: primitive echo (DivIntegers(10, 2) -&gt; 5.0)
     * </pre>
     */
    public void divIntegers(benchmark.BenchmarkProto.DivIntegersRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.DivIntegersResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getDivIntegersMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Scenario 3: string echo (JoinStrings(["hello","world"]) -&gt; "hello,world")
     * </pre>
     */
    public void joinStrings(benchmark.BenchmarkProto.JoinStringsRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.JoinStringsResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getJoinStringsMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Scenario 4: array echo (EchoBytes(data) -&gt; data)
     * </pre>
     */
    public void echoBytes(benchmark.BenchmarkProto.EchoBytesRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.EchoBytesResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getEchoBytesMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Scenario 5: object method (NewTestMap() + GetName())
     * </pre>
     */
    public void objectMethod(benchmark.BenchmarkProto.ObjectMethodRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.ObjectMethodResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getObjectMethodMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Scenario 6: callback via bidirectional streaming
     * </pre>
     */
    public io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.CallbackClientMsg> callbackAdd(
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.CallbackServerMsg> responseObserver) {
      return io.grpc.stub.ClientCalls.asyncBidiStreamingCall(
          getChannel().newCall(getCallbackAddMethod(), getCallOptions()), responseObserver);
    }

    /**
     * <pre>
     * Scenario 7: error propagation (ReturnsAnError() -&gt; gRPC INTERNAL error)
     * </pre>
     */
    public void returnsAnError(benchmark.BenchmarkProto.Empty request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.Empty> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getReturnsAnErrorMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * Scenario: dynamic any echo (mixed array payload)
     * </pre>
     */
    public void anyEcho(benchmark.BenchmarkProto.AnyEchoRequest request,
        io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.AnyEchoResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getAnyEchoMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service BenchmarkService.
   * <pre>
   * BenchmarkService wraps the Go guest module for cross-language benchmarking.
   * Each RPC maps to one of the 7 benchmark scenarios.
   * </pre>
   */
  public static final class BenchmarkServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<BenchmarkServiceBlockingStub> {
    private BenchmarkServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected BenchmarkServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new BenchmarkServiceBlockingStub(channel, callOptions);
    }

    /**
     * <pre>
     * Scenario 1: void call (WaitABit(0))
     * </pre>
     */
    public benchmark.BenchmarkProto.VoidCallResponse voidCall(benchmark.BenchmarkProto.VoidCallRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getVoidCallMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Scenario 2: primitive echo (DivIntegers(10, 2) -&gt; 5.0)
     * </pre>
     */
    public benchmark.BenchmarkProto.DivIntegersResponse divIntegers(benchmark.BenchmarkProto.DivIntegersRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getDivIntegersMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Scenario 3: string echo (JoinStrings(["hello","world"]) -&gt; "hello,world")
     * </pre>
     */
    public benchmark.BenchmarkProto.JoinStringsResponse joinStrings(benchmark.BenchmarkProto.JoinStringsRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getJoinStringsMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Scenario 4: array echo (EchoBytes(data) -&gt; data)
     * </pre>
     */
    public benchmark.BenchmarkProto.EchoBytesResponse echoBytes(benchmark.BenchmarkProto.EchoBytesRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getEchoBytesMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Scenario 5: object method (NewTestMap() + GetName())
     * </pre>
     */
    public benchmark.BenchmarkProto.ObjectMethodResponse objectMethod(benchmark.BenchmarkProto.ObjectMethodRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getObjectMethodMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Scenario 7: error propagation (ReturnsAnError() -&gt; gRPC INTERNAL error)
     * </pre>
     */
    public benchmark.BenchmarkProto.Empty returnsAnError(benchmark.BenchmarkProto.Empty request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getReturnsAnErrorMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * Scenario: dynamic any echo (mixed array payload)
     * </pre>
     */
    public benchmark.BenchmarkProto.AnyEchoResponse anyEcho(benchmark.BenchmarkProto.AnyEchoRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getAnyEchoMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service BenchmarkService.
   * <pre>
   * BenchmarkService wraps the Go guest module for cross-language benchmarking.
   * Each RPC maps to one of the 7 benchmark scenarios.
   * </pre>
   */
  public static final class BenchmarkServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<BenchmarkServiceFutureStub> {
    private BenchmarkServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected BenchmarkServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new BenchmarkServiceFutureStub(channel, callOptions);
    }

    /**
     * <pre>
     * Scenario 1: void call (WaitABit(0))
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<benchmark.BenchmarkProto.VoidCallResponse> voidCall(
        benchmark.BenchmarkProto.VoidCallRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getVoidCallMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Scenario 2: primitive echo (DivIntegers(10, 2) -&gt; 5.0)
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<benchmark.BenchmarkProto.DivIntegersResponse> divIntegers(
        benchmark.BenchmarkProto.DivIntegersRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getDivIntegersMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Scenario 3: string echo (JoinStrings(["hello","world"]) -&gt; "hello,world")
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<benchmark.BenchmarkProto.JoinStringsResponse> joinStrings(
        benchmark.BenchmarkProto.JoinStringsRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getJoinStringsMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Scenario 4: array echo (EchoBytes(data) -&gt; data)
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<benchmark.BenchmarkProto.EchoBytesResponse> echoBytes(
        benchmark.BenchmarkProto.EchoBytesRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getEchoBytesMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Scenario 5: object method (NewTestMap() + GetName())
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<benchmark.BenchmarkProto.ObjectMethodResponse> objectMethod(
        benchmark.BenchmarkProto.ObjectMethodRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getObjectMethodMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Scenario 7: error propagation (ReturnsAnError() -&gt; gRPC INTERNAL error)
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<benchmark.BenchmarkProto.Empty> returnsAnError(
        benchmark.BenchmarkProto.Empty request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getReturnsAnErrorMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * Scenario: dynamic any echo (mixed array payload)
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<benchmark.BenchmarkProto.AnyEchoResponse> anyEcho(
        benchmark.BenchmarkProto.AnyEchoRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getAnyEchoMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_VOID_CALL = 0;
  private static final int METHODID_DIV_INTEGERS = 1;
  private static final int METHODID_JOIN_STRINGS = 2;
  private static final int METHODID_ECHO_BYTES = 3;
  private static final int METHODID_OBJECT_METHOD = 4;
  private static final int METHODID_RETURNS_AN_ERROR = 5;
  private static final int METHODID_ANY_ECHO = 6;
  private static final int METHODID_CALLBACK_ADD = 7;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final AsyncService serviceImpl;
    private final int methodId;

    MethodHandlers(AsyncService serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_VOID_CALL:
          serviceImpl.voidCall((benchmark.BenchmarkProto.VoidCallRequest) request,
              (io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.VoidCallResponse>) responseObserver);
          break;
        case METHODID_DIV_INTEGERS:
          serviceImpl.divIntegers((benchmark.BenchmarkProto.DivIntegersRequest) request,
              (io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.DivIntegersResponse>) responseObserver);
          break;
        case METHODID_JOIN_STRINGS:
          serviceImpl.joinStrings((benchmark.BenchmarkProto.JoinStringsRequest) request,
              (io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.JoinStringsResponse>) responseObserver);
          break;
        case METHODID_ECHO_BYTES:
          serviceImpl.echoBytes((benchmark.BenchmarkProto.EchoBytesRequest) request,
              (io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.EchoBytesResponse>) responseObserver);
          break;
        case METHODID_OBJECT_METHOD:
          serviceImpl.objectMethod((benchmark.BenchmarkProto.ObjectMethodRequest) request,
              (io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.ObjectMethodResponse>) responseObserver);
          break;
        case METHODID_RETURNS_AN_ERROR:
          serviceImpl.returnsAnError((benchmark.BenchmarkProto.Empty) request,
              (io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.Empty>) responseObserver);
          break;
        case METHODID_ANY_ECHO:
          serviceImpl.anyEcho((benchmark.BenchmarkProto.AnyEchoRequest) request,
              (io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.AnyEchoResponse>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_CALLBACK_ADD:
          return (io.grpc.stub.StreamObserver<Req>) serviceImpl.callbackAdd(
              (io.grpc.stub.StreamObserver<benchmark.BenchmarkProto.CallbackServerMsg>) responseObserver);
        default:
          throw new AssertionError();
      }
    }
  }

  public static final io.grpc.ServerServiceDefinition bindService(AsyncService service) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          getVoidCallMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              benchmark.BenchmarkProto.VoidCallRequest,
              benchmark.BenchmarkProto.VoidCallResponse>(
                service, METHODID_VOID_CALL)))
        .addMethod(
          getDivIntegersMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              benchmark.BenchmarkProto.DivIntegersRequest,
              benchmark.BenchmarkProto.DivIntegersResponse>(
                service, METHODID_DIV_INTEGERS)))
        .addMethod(
          getJoinStringsMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              benchmark.BenchmarkProto.JoinStringsRequest,
              benchmark.BenchmarkProto.JoinStringsResponse>(
                service, METHODID_JOIN_STRINGS)))
        .addMethod(
          getEchoBytesMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              benchmark.BenchmarkProto.EchoBytesRequest,
              benchmark.BenchmarkProto.EchoBytesResponse>(
                service, METHODID_ECHO_BYTES)))
        .addMethod(
          getObjectMethodMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              benchmark.BenchmarkProto.ObjectMethodRequest,
              benchmark.BenchmarkProto.ObjectMethodResponse>(
                service, METHODID_OBJECT_METHOD)))
        .addMethod(
          getCallbackAddMethod(),
          io.grpc.stub.ServerCalls.asyncBidiStreamingCall(
            new MethodHandlers<
              benchmark.BenchmarkProto.CallbackClientMsg,
              benchmark.BenchmarkProto.CallbackServerMsg>(
                service, METHODID_CALLBACK_ADD)))
        .addMethod(
          getReturnsAnErrorMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              benchmark.BenchmarkProto.Empty,
              benchmark.BenchmarkProto.Empty>(
                service, METHODID_RETURNS_AN_ERROR)))
        .addMethod(
          getAnyEchoMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              benchmark.BenchmarkProto.AnyEchoRequest,
              benchmark.BenchmarkProto.AnyEchoResponse>(
                service, METHODID_ANY_ECHO)))
        .build();
  }

  private static abstract class BenchmarkServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    BenchmarkServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return benchmark.BenchmarkProto.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("BenchmarkService");
    }
  }

  private static final class BenchmarkServiceFileDescriptorSupplier
      extends BenchmarkServiceBaseDescriptorSupplier {
    BenchmarkServiceFileDescriptorSupplier() {}
  }

  private static final class BenchmarkServiceMethodDescriptorSupplier
      extends BenchmarkServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    BenchmarkServiceMethodDescriptorSupplier(java.lang.String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (BenchmarkServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new BenchmarkServiceFileDescriptorSupplier())
              .addMethod(getVoidCallMethod())
              .addMethod(getDivIntegersMethod())
              .addMethod(getJoinStringsMethod())
              .addMethod(getEchoBytesMethod())
              .addMethod(getObjectMethodMethod())
              .addMethod(getCallbackAddMethod())
              .addMethod(getReturnsAnErrorMethod())
              .addMethod(getAnyEchoMethod())
              .build();
        }
      }
    }
    return result;
  }
}
