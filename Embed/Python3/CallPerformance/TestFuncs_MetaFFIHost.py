
# Code generated by MetaFFI. DO NOT EDIT.
# Guest code for Main_test.py#TestFuncs.go

from ctypes import *
import ctypes.util
from typing import List
from typing import Any
import platform
import os
from enum import Enum

xllr_handle = None
python_plugin_handle = None

def free_metaffi():
	global xllr_handle
	global runtime_plugin

	err = pointer((c_char * 1)(0))
	err_len = (c_ulonglong)(0)
	xllr_handle.free_runtime_plugin(runtime_plugin, len(runtime_plugin), byref(err), byref(err_len))

def load_xllr_and_python_plugin():
	global xllr_handle
	global python_plugin_handle
	
	if xllr_handle == None:
		xllr_handle = cdll.LoadLibrary(get_filename_to_load('xllr'))

	if python_plugin_handle == None:
		python_plugin_handle = cdll.LoadLibrary(get_filename_to_load('xllr.python3'))

		err = pointer((c_char * 1)(0))
		err_len = (c_ulonglong)(0)
		python_plugin_handle.load_runtime(byref(err), byref(err_len)) # in order to initialize python environment (e.g. define metaffi_handle class)

	# set restypes
	python_plugin_handle.convert_host_params_to_cdts.argstype = [py_object, py_object]
	python_plugin_handle.convert_host_params_to_cdts.restype = c_void_p
	python_plugin_handle.convert_host_return_values_from_cdts.argstype = [c_void_p, c_uint64]
	python_plugin_handle.convert_host_return_values_from_cdts.restype = py_object
	xllr_handle.alloc_cdts_buffer.restype = c_void_p
	xllr_handle.load_function.restype = c_void_p

def get_filename_to_load(fname):
	osname = platform.system()
	if os.getenv('METAFFI_HOME') is None:
		raise RuntimeError('No METAFFI_HOME environment variable')
	elif fname is None:
		raise RuntimeError('fname is None')

	if osname == 'Windows':
		return os.getenv('METAFFI_HOME')+'\\'+ fname + '.dll'
	elif osname == 'Darwin':
		return os.getenv('METAFFI_HOME')+'/' + fname + '.dylib'
	else:
		return os.getenv('METAFFI_HOME')+'/' + fname + '.so' # for everything that is not windows or mac, return .so



cfunctype_params_ret = CFUNCTYPE(None)
cfunctype_params_ret.argtypes = [c_void_p, POINTER(POINTER(c_ubyte)), POINTER(c_ulonglong)]
cfunctype_params_no_ret = CFUNCTYPE(None)
cfunctype_params_no_ret.argtypes = [c_void_p, POINTER(POINTER(c_ubyte)), POINTER(c_ulonglong)]
cfunctype_no_params_ret = CFUNCTYPE(None)
cfunctype_no_params_ret.argtypes = [c_void_p, POINTER(POINTER(c_ubyte)), POINTER(c_ulonglong)]
cfunctype_no_params_no_ret = CFUNCTYPE(None)
cfunctype_no_params_no_ret.argtypes = [POINTER(POINTER(c_ubyte)), POINTER(c_ulonglong)]

runtime_plugin = """xllr.go""".encode("utf-8")





DoNothing_id = c_void_p(0)




# load foreign functions
load_xllr_and_python_plugin()

err = POINTER(c_ubyte)()
out_err = POINTER(POINTER(c_ubyte))(c_void_p(addressof(err)))
err_len = c_uint32()
out_err_len = POINTER(c_uint32)(c_void_p(addressof(err_len)))
	


 


DoNothing_id = cfunctype_no_params_no_ret(xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_DoNothing,metaffi_guest_lib=TestFuncs_MetaFFIGuest,module=/mnt/c/src/github.com/MetaFFI/Tests/Embed/Python3/CallPerformance,package=TestFuncs'.encode("utf-8"), len('package=TestFuncs,entrypoint_function=EntryPoint_DoNothing,metaffi_guest_lib=TestFuncs_MetaFFIGuest,module=/mnt/c/src/github.com/MetaFFI/Tests/Embed/Python3/CallPerformance'.encode("utf-8")), DoNothing_id, 0, 0, out_err, out_err_len))
if DoNothing_id == cfunctype_no_params_no_ret(0): # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))


	

	


# Code to call foreign functions in module go via XLLR

# globals



# Call to foreign DoNothing
def DoNothing() -> ():

	global xllr_handle
	global DoNothing_id
	global runtime_plugin
	global python_plugin_handle

	

	# xcall function
	out_error = (c_char_p * 1)(0)
	out_error_len = (c_ulonglong)(0)
	DoNothing_id(out_error, byref(out_error_len))	
	if out_error != None and out_error[0] != None:
		err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
		raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))


	
	return 





