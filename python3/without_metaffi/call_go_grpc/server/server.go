package main

import (
	"context"
	"fmt"
	"io"
	"net"
	"os"

	pb "grpc_go_server/pb"

	guest "metaffi_guest_go"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

// ---------------------------------------------------------------------------
// gRPC Server implementation
// ---------------------------------------------------------------------------

type benchmarkServer struct {
	pb.UnimplementedBenchmarkServiceServer
}

// Scenario 1: void call
func (s *benchmarkServer) VoidCall(_ context.Context, req *pb.VoidCallRequest) (*pb.VoidCallResponse, error) {
	guest.WaitABit(req.Ms)
	return &pb.VoidCallResponse{}, nil
}

// Scenario 2: primitive echo
func (s *benchmarkServer) DivIntegers(_ context.Context, req *pb.DivIntegersRequest) (*pb.DivIntegersResponse, error) {
	result := guest.DivIntegers(req.X, req.Y)
	return &pb.DivIntegersResponse{Result: result}, nil
}

// Scenario 3: string echo
func (s *benchmarkServer) JoinStrings(_ context.Context, req *pb.JoinStringsRequest) (*pb.JoinStringsResponse, error) {
	result := guest.JoinStrings(req.Values)
	return &pb.JoinStringsResponse{Result: result}, nil
}

// Scenario 4: array echo (bytes)
func (s *benchmarkServer) EchoBytes(_ context.Context, req *pb.EchoBytesRequest) (*pb.EchoBytesResponse, error) {
	result := guest.EchoBytes(req.Data)
	return &pb.EchoBytesResponse{Data: result}, nil
}

// Scenario 5: object create + method call
func (s *benchmarkServer) ObjectMethod(_ context.Context, _ *pb.ObjectMethodRequest) (*pb.ObjectMethodResponse, error) {
	tm := guest.NewTestMap()
	return &pb.ObjectMethodResponse{Result: tm.Name}, nil
}

// Scenario 6: callback via bidirectional streaming
func (s *benchmarkServer) CallbackAdd(stream pb.BenchmarkService_CallbackAddServer) error {
	for {
		msg, err := stream.Recv()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}

		switch m := msg.Msg.(type) {
		case *pb.CallbackClientMsg_Invoke:
			if m.Invoke {
				// Ask client to compute add(1, 2)
				err = stream.Send(&pb.CallbackServerMsg{
					Msg: &pb.CallbackServerMsg_Compute{
						Compute: &pb.CallbackArgs{A: 1, B: 2},
					},
				})
				if err != nil {
					return err
				}
			}

		case *pb.CallbackClientMsg_AddResult:
			// Client computed the result, send it back as final
			err = stream.Send(&pb.CallbackServerMsg{
				Msg: &pb.CallbackServerMsg_FinalResult{
					FinalResult: m.AddResult,
				},
			})
			if err != nil {
				return err
			}
		}
	}
}

// Scenario 7: error propagation
func (s *benchmarkServer) ReturnsAnError(_ context.Context, _ *pb.Empty) (*pb.Empty, error) {
	err := guest.ReturnsAnError()
	if err != nil {
		return nil, status.Errorf(codes.Internal, "%v", err)
	}
	return &pb.Empty{}, nil
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

func main() {
	lis, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to listen: %v\n", err)
		os.Exit(1)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterBenchmarkServiceServer(grpcServer, &benchmarkServer{})

	// Print READY:<port> so the client knows we're up
	port := lis.Addr().(*net.TCPAddr).Port
	fmt.Printf("READY:%d\n", port)
	os.Stdout.Sync()

	if err := grpcServer.Serve(lis); err != nil {
		fmt.Fprintf(os.Stderr, "Server failed: %v\n", err)
		os.Exit(1)
	}
}
