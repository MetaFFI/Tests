"""gRPC server wrapping the Python guest module for benchmark scenarios.

Usage:
    python server.py --module-path <path-to-python3-guest-parent> [--port <port>]

The server prints "READY:<port>" to stdout when ready to accept connections.
"""

import argparse
import sys
from concurrent import futures

import grpc

# Generated protobuf/gRPC stubs (run generate.sh first)
import benchmark_pb2
import benchmark_pb2_grpc


class BenchmarkServicer(benchmark_pb2_grpc.BenchmarkServiceServicer):
    """Implements the 7 benchmark scenarios by delegating to the Python guest module."""

    def __init__(self, module):
        self._mod = module

    # --- Scenario 1: void call ---
    def VoidCall(self, request, context):
        self._mod.wait_a_bit(request.secs)
        return benchmark_pb2.VoidCallResponse()

    # --- Scenario 2: primitive echo ---
    def DivIntegers(self, request, context):
        result = self._mod.div_integers(request.x, request.y)
        return benchmark_pb2.DivIntegersResponse(result=result)

    # --- Scenario 3: string echo ---
    def JoinStrings(self, request, context):
        result = self._mod.join_strings(list(request.values))
        return benchmark_pb2.JoinStringsResponse(result=result)

    # --- Scenario 4: array sum ---
    def ArraySum(self, request, context):
        arr = [list(request.values)]  # wrap as 2D for accepts_ragged_array
        result = self._mod.accepts_ragged_array(arr)
        return benchmark_pb2.ArraySumResponse(sum=result)

    # --- Scenario 5: object method ---
    def ObjectMethod(self, request, context):
        instance = self._mod.SomeClass(request.name)
        result = instance.print()
        return benchmark_pb2.ObjectMethodResponse(result=result)

    # --- Scenario 6: callback (bidirectional streaming) ---
    def CallbackAdd(self, request_iterator, context):
        for msg in request_iterator:
            if msg.HasField("invoke"):
                # Ask client to compute add(1, 2) -- matches call_callback_add's behavior
                yield benchmark_pb2.CallbackServerMsg(
                    compute=benchmark_pb2.CallbackArgs(a=1, b=2)
                )

            elif msg.HasField("add_result"):
                result = msg.add_result
                if result != 3:
                    context.abort(
                        grpc.StatusCode.INTERNAL,
                        f"callback: expected 3, got {result}",
                    )
                    return
                yield benchmark_pb2.CallbackServerMsg(final_result=result)
                return

    # --- Scenario 7: error propagation ---
    def ReturnsAnError(self, request, context):
        try:
            self._mod.returns_an_error()
            # Should not reach here
            return benchmark_pb2.Empty()
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, str(e))


def serve(module_path: str, port: int):
    """Start the gRPC server."""

    # Add module parent to sys.path and import
    sys.path.insert(0, module_path)
    import module  # noqa: E402

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    benchmark_pb2_grpc.add_BenchmarkServiceServicer_to_server(
        BenchmarkServicer(module), server
    )

    # port=0 means pick a random available port
    actual_port = server.add_insecure_port(f"localhost:{port}")
    server.start()

    # Signal readiness to parent process
    print(f"READY:{actual_port}", flush=True)
    server.wait_for_termination()


def main():
    parser = argparse.ArgumentParser(description="Benchmark gRPC server")
    parser.add_argument(
        "--module-path",
        required=True,
        help="Parent directory of the 'module' Python package",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port to listen on (0 = random)",
    )
    args = parser.parse_args()
    serve(args.module_path, args.port)


if __name__ == "__main__":
    main()
