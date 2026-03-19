module grpc_go_server

go 1.24.0

require (
	google.golang.org/grpc v1.79.3
	google.golang.org/protobuf v1.36.10
	metaffi_guest_go v0.0.0
)

replace metaffi_guest_go => ../../../../../sdk/test_modules/guest_modules/go

require (
	github.com/golang/protobuf v1.5.4 // indirect
	golang.org/x/net v0.48.0 // indirect
	golang.org/x/sys v0.39.0 // indirect
	golang.org/x/text v0.32.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20251202230838-ff82c1b0f217 // indirect
)
