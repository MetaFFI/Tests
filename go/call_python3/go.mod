module github.com/MetaFFI/tests/go/call_python3

go 1.23.0

toolchain go1.24.4

replace github.com/MetaFFI/sdk/api/go => ../../../sdk/api/go

replace github.com/MetaFFI/sdk/idl_entities/go => ../../../sdk/idl_entities/go

require (
	github.com/MetaFFI/sdk/api/go v0.0.0-00010101000000-000000000000
	github.com/MetaFFI/sdk/idl_entities/go v0.0.0
)
