package main


/*
#cgo !windows LDFLAGS: -L. -ldl
#cgo CFLAGS: -I/mnt/c/src/github.com/MetaFFI/out/ubuntu/x64/debug

#include <include/cdt_capi_loader.c>

metaffi_handle get_null_handle()
{
	return METAFFI_NULL_HANDLE;
}

metaffi_size get_int_item(metaffi_size* array, int index)
{
	return array[index];
}

void* convert_union_to_ptr(void* p)
{
	return p;
}

void set_cdt_type(struct cdt* p, metaffi_type t)
{
	p->type = t;
}

metaffi_type get_cdt_type(struct cdt* p)
{
	return p->type;
}

#ifdef _WIN32
metaffi_size len_to_metaffi_size(long long i)
#else
metaffi_size len_to_metaffi_size(long long i)
#endif
{
	return (metaffi_size)i;
}


*/
import "C"