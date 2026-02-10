module grpc_go_server

go 1.21

require (
	google.golang.org/grpc v1.62.2
	google.golang.org/protobuf v1.33.0
	metaffi_guest_go v0.0.0
)

replace metaffi_guest_go => ../../../../../sdk/test_modules/guest_modules/go

require (
	github.com/golang/protobuf v1.5.3 // indirect
	golang.org/x/net v0.22.0 // indirect
	golang.org/x/sys v0.18.0 // indirect
	golang.org/x/text v0.14.0 // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20240318140521-94a12d6c2237 // indirect
)
