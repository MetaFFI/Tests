
# Code generated by MetaFFI. DO NOT EDIT.
# Guest code for Test.json

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
	python_plugin_handle.convert_host_return_values_from_cdts.argstype = [py_object, py_object]
	python_plugin_handle.convert_host_return_values_from_cdts.restype = py_object

def get_filename_to_load(fname):
	osname = platform.system()
	if osname == 'Windows':
		return os.getenv('METAFFI_HOME')+'\\'+ fname + '.dll'
	elif osname == 'Darwin':
		return os.getenv('METAFFI_HOME')+'/' + fname + '.dylib'
	else:
		return os.getenv('METAFFI_HOME')+'/' + fname + '.so' # for everything that is not windows or mac, return .so

runtime_plugin = """xllr.go""".encode("utf-8")



GetFiveSeconds_id = -1




HelloWorld_id = -1

ReturnsAnError_id = -1

DivIntegers_id = -1

JoinStrings_id = -1

WaitABit_id = -1





TestMap_GetName_id = -1
TestMap_SetName_id = -1



TestMap_NewTestMap_id = -1



TestMap_Set_id = -1

TestMap_Get_id = -1

TestMap_Contains_id = -1


TestMap_ReleaseTestMap_id = -1



# load foreign functions
load_xllr_and_python_plugin()

err = POINTER(c_ubyte)()
out_err = POINTER(POINTER(c_ubyte))(c_void_p(addressof(err)))
err_len = c_uint32()
out_err_len = POINTER(c_uint32)(c_void_p(addressof(err_len)))
	




GetFiveSeconds_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_GetFiveSeconds,metaffi_guest_lib=Test_MetaFFIGuest'.encode("utf-8"), len('entrypoint_function=EntryPoint_GetFiveSeconds,metaffi_guest_lib=Test_MetaFFIGuest'.encode("utf-8")), GetFiveSeconds_id, out_err, out_err_len)
if GetFiveSeconds_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))


 


HelloWorld_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_HelloWorld,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8"), len('entrypoint_function=EntryPoint_HelloWorld,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8")), HelloWorld_id, out_err, out_err_len)
if HelloWorld_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))

ReturnsAnError_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_ReturnsAnError,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8"), len('metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs,entrypoint_function=EntryPoint_ReturnsAnError'.encode("utf-8")), ReturnsAnError_id, out_err, out_err_len)
if ReturnsAnError_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))

DivIntegers_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_DivIntegers,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8"), len('entrypoint_function=EntryPoint_DivIntegers,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8")), DivIntegers_id, out_err, out_err_len)
if DivIntegers_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))

JoinStrings_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'module=$PWD,package=TestFuncs,entrypoint_function=EntryPoint_JoinStrings,metaffi_guest_lib=Test_MetaFFIGuest'.encode("utf-8"), len('entrypoint_function=EntryPoint_JoinStrings,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8")), JoinStrings_id, out_err, out_err_len)
if JoinStrings_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))

WaitABit_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_WaitABit,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8"), len('entrypoint_function=EntryPoint_WaitABit,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8")), WaitABit_id, out_err, out_err_len)
if WaitABit_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))




TestMap_NewTestMap_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_NewTestMap,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8"), len('module=$PWD,package=TestFuncs,entrypoint_function=EntryPoint_NewTestMap,metaffi_guest_lib=Test_MetaFFIGuest'.encode("utf-8")), TestMap_NewTestMap_id, out_err, out_err_len)
if TestMap_NewTestMap_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))




TestMap_GetName_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_GetName,metaffi_guest_lib=Test_MetaFFIGuest'.encode("utf-8"), len('entrypoint_function=EntryPoint_GetName,metaffi_guest_lib=Test_MetaFFIGuest'.encode("utf-8")), TestMap_GetName_id, out_err, out_err_len)
if TestMap_GetName_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))


TestMap_SetName_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_SetName,metaffi_guest_lib=Test_MetaFFIGuest'.encode("utf-8"), len('entrypoint_function=EntryPoint_SetName,metaffi_guest_lib=Test_MetaFFIGuest'.encode("utf-8")), TestMap_SetName_id, out_err, out_err_len)
if TestMap_SetName_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))

 


TestMap_Set_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_class=TestMap,entrypoint_function=EntryPoint_Set,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8"), len('entrypoint_class=TestMap,entrypoint_function=EntryPoint_Set,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8")), TestMap_Set_id, out_err, out_err_len)
if TestMap_Set_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))

TestMap_Get_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_Get,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs,entrypoint_class=TestMap'.encode("utf-8"), len('entrypoint_class=TestMap,entrypoint_function=EntryPoint_Get,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8")), TestMap_Get_id, out_err, out_err_len)
if TestMap_Get_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))

TestMap_Contains_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_class=TestMap,entrypoint_function=EntryPoint_Contains,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8"), len('entrypoint_class=TestMap,entrypoint_function=EntryPoint_Contains,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8")), TestMap_Contains_id, out_err, out_err_len)
if TestMap_Contains_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))



TestMap_ReleaseTestMap_id = xllr_handle.load_function(runtime_plugin, len(runtime_plugin), 'entrypoint_function=EntryPoint_ReleaseTestMap,metaffi_guest_lib=Test_MetaFFIGuest,module=$PWD,package=TestFuncs'.encode("utf-8"), len('module=$PWD,package=TestFuncs,entrypoint_function=EntryPoint_ReleaseTestMap,metaffi_guest_lib=Test_MetaFFIGuest'.encode("utf-8")), TestMap_ReleaseTestMap_id, out_err, out_err_len)
if TestMap_ReleaseTestMap_id == -1: # failed to load function
	err_text = string_at(out_err.contents, out_err_len.contents.value)
	raise RuntimeError('\n'+str(err_text).replace("\\n", "\n"))


	

	


# Code to call foreign functions in module Sanity via XLLR

# globals


def GetFiveSeconds():
	global xllr_handle
	global GetFiveSeconds_id
	global runtime_plugin
	global python_plugin_handle

	
	params = ()
	params_types = ()
	parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
	return_values_buffer = xllr_handle.alloc_cdts_buffer(1)

	# call function
	
	out_error = (c_char_p * 1)(0)
	out_error_len = (c_ulonglong)(0)
	xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
					c_ulonglong(GetFiveSeconds_id), \
					c_void_p(parameters_buffer), c_ulonglong(0), \
					c_void_p(return_values_buffer), c_ulonglong(1), \
					out_error, byref(out_error_len))
			
	# check for error
	if out_error != None and out_error[0] != None:
		err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
		raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))

	# unpack results

	ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 1)

	return ret_vals[0]
 




# Call to foreign HelloWorld
def HelloWorld() -> ():

	global xllr_handle
	global HelloWorld_id
	global runtime_plugin
	global python_plugin_handle

	if python_plugin_handle is None:
		raise RuntimeError('handle is None')

	
	params = ()
	params_types = ()
	parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
	return_values_buffer = xllr_handle.alloc_cdts_buffer(0)

	# call function
	
	out_error = (c_char_p * 1)(0)
	out_error_len = (c_ulonglong)(0)
	xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
					c_ulonglong(HelloWorld_id), \
					c_void_p(parameters_buffer), c_ulonglong(0), \
					c_void_p(return_values_buffer), c_ulonglong(0), \
					out_error, byref(out_error_len))
	
	
	# check for error
	if out_error != None and out_error[0] != None:
		err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
		raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))

	# unpack results

	ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 0)

	return 

# Call to foreign ReturnsAnError
def ReturnsAnError() -> ():

	global xllr_handle
	global ReturnsAnError_id
	global runtime_plugin
	global python_plugin_handle

	if python_plugin_handle is None:
		raise RuntimeError('handle is None')

	
	params = ()
	params_types = ()
	parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
	return_values_buffer = xllr_handle.alloc_cdts_buffer(0)

	# call function
	
	out_error = (c_char_p * 1)(0)
	out_error_len = (c_ulonglong)(0)
	xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
					c_ulonglong(ReturnsAnError_id), \
					c_void_p(parameters_buffer), c_ulonglong(0), \
					c_void_p(return_values_buffer), c_ulonglong(0), \
					out_error, byref(out_error_len))
	
	
	# check for error
	if out_error != None and out_error[0] != None:
		err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
		raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))

	# unpack results

	ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 0)

	return 

# Call to foreign DivIntegers
def DivIntegers( x:int, y:int) -> (float):

	global xllr_handle
	global DivIntegers_id
	global runtime_plugin
	global python_plugin_handle

	if python_plugin_handle is None:
		raise RuntimeError('handle is None')

	
	params = ( x, y)
	params_types = ( 32, 32)
	parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
	return_values_buffer = xllr_handle.alloc_cdts_buffer(1)

	# call function
	
	out_error = (c_char_p * 1)(0)
	out_error_len = (c_ulonglong)(0)
	xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
					c_ulonglong(DivIntegers_id), \
					c_void_p(parameters_buffer), c_ulonglong(2), \
					c_void_p(return_values_buffer), c_ulonglong(1), \
					out_error, byref(out_error_len))
	
	
	# check for error
	if out_error != None and out_error[0] != None:
		err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
		raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))

	# unpack results

	ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 1)

	return ret_vals[0]

# Call to foreign JoinStrings
def JoinStrings( strings:List[str]) -> (str):

	global xllr_handle
	global JoinStrings_id
	global runtime_plugin
	global python_plugin_handle

	if python_plugin_handle is None:
		raise RuntimeError('handle is None')

	
	params = ( strings,)
	params_types = ( 69632,)
	parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
	return_values_buffer = xllr_handle.alloc_cdts_buffer(1)

	# call function
	
	out_error = (c_char_p * 1)(0)
	out_error_len = (c_ulonglong)(0)
	xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
					c_ulonglong(JoinStrings_id), \
					c_void_p(parameters_buffer), c_ulonglong(1), \
					c_void_p(return_values_buffer), c_ulonglong(1), \
					out_error, byref(out_error_len))
	
	
	# check for error
	if out_error != None and out_error[0] != None:
		err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
		raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))

	# unpack results

	ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 1)

	return ret_vals[0]

# Call to foreign WaitABit
def WaitABit( d:int) -> (py_object):

	global xllr_handle
	global WaitABit_id
	global runtime_plugin
	global python_plugin_handle

	if python_plugin_handle is None:
		raise RuntimeError('handle is None')

	
	params = ( d,)
	params_types = ( 32,)
	parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
	return_values_buffer = xllr_handle.alloc_cdts_buffer(1)

	# call function
	
	out_error = (c_char_p * 1)(0)
	out_error_len = (c_ulonglong)(0)
	xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
					c_ulonglong(WaitABit_id), \
					c_void_p(parameters_buffer), c_ulonglong(1), \
					c_void_p(return_values_buffer), c_ulonglong(1), \
					out_error, byref(out_error_len))
	
	
	# check for error
	if out_error != None and out_error[0] != None:
		err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
		raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))

	# unpack results

	ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 1)

	return ret_vals[0]



# Class to call methods of foreign class TestMap
class TestMap:
	obj_handle = None
	
	
	def __init__(self ):
		global xllr_handle
		global TestMap_NewTestMap_id
		global runtime_plugin
		global python_plugin_handle
	
		
		params = ()
		params_types = ()
		parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
		return_values_buffer = xllr_handle.alloc_cdts_buffer(1)
	
		# call function
		
		out_error = (c_char_p * 1)(0)
		out_error_len = (c_ulonglong)(0)
		xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
						c_ulonglong(TestMap_NewTestMap_id), \
						c_void_p(parameters_buffer), c_ulonglong(0), \
						c_void_p(return_values_buffer), c_ulonglong(1), \
						out_error, byref(out_error_len))
		
		
		# check for error
		if out_error != None and out_error[0] != None:
			err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
			raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))
	
		# unpack results
	
		ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 1)
		self.obj_handle = ret_vals[0] # NOTICE: assuming first ret_val is the handle
	

	
	
	def GetName(self):
		global xllr_handle
		global TestMap_GetName_id
		global runtime_plugin
		global python_plugin_handle
	
		
		params = (self.obj_handle ,)
		params_types = ( 32768,)
		parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
		return_values_buffer = xllr_handle.alloc_cdts_buffer(1)
	
		# call function
		
		out_error = (c_char_p * 1)(0)
		out_error_len = (c_ulonglong)(0)
		xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
						c_ulonglong(TestMap_GetName_id), \
						c_void_p(parameters_buffer), c_ulonglong(1), \
						c_void_p(return_values_buffer), c_ulonglong(1), \
						out_error, byref(out_error_len))
				
		# check for error
		if out_error != None and out_error[0] != None:
			err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
			raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))
	
		# unpack results
	
		ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 1)

		return ret_vals[0]
	 
	
	def SetName(self, Name ):
		global xllr_handle
		global TestMap_SetName_id
		global runtime_plugin
		global python_plugin_handle
	
		
		params = (self.obj_handle , Name)
		params_types = ( 32768, 4096)
		parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
		return_values_buffer = xllr_handle.alloc_cdts_buffer(0)
	
		# call function
		
		out_error = (c_char_p * 1)(0)
		out_error_len = (c_ulonglong)(0)
		xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
						c_ulonglong(TestMap_SetName_id), \
						c_void_p(parameters_buffer), c_ulonglong(2), \
						c_void_p(return_values_buffer), c_ulonglong(0), \
						out_error, byref(out_error_len))
				
		# check for error
		if out_error != None and out_error[0] != None:
			err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
			raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))
	
		# unpack results
	
		ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 0)

		return 
	
	

	
	# released foreign object handle
	def __del__(self):
		global xllr_handle
		global TestMap_ReleaseTestMap_id
		global runtime_plugin
		global python_plugin_handle
	
		
		params = (self.obj_handle,)
		params_types = (32768,)
		parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
		return_values_buffer = xllr_handle.alloc_cdts_buffer(0)
	
		# call function
		
		out_error = (c_char_p * 1)(0)
		out_error_len = (c_ulonglong)(0)
		xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
						c_ulonglong(TestMap_ReleaseTestMap_id), \
						c_void_p(parameters_buffer), c_ulonglong(1), \
						c_void_p(return_values_buffer), c_ulonglong(0), \
						out_error, byref(out_error_len))
		
		
		# check for error
		if out_error != None and out_error[0] != None:
			err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
			raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))
	

	
	def Set(self, key:str, value:Any):
		global xllr_handle
		global TestMap_Set_id
		global runtime_plugin
		global python_plugin_handle
	
		
		params = (self.obj_handle , key, value)
		params_types = ( 32768, 4096, 4194304)
		parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
		return_values_buffer = xllr_handle.alloc_cdts_buffer(0)
	
		# call function
		
		out_error = (c_char_p * 1)(0)
		out_error_len = (c_ulonglong)(0)
		xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
						c_ulonglong(TestMap_Set_id), \
						c_void_p(parameters_buffer), c_ulonglong(3), \
						c_void_p(return_values_buffer), c_ulonglong(0), \
						out_error, byref(out_error_len))
		
		
		# check for error
		if out_error != None and out_error[0] != None:
			err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
			raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))
	
		# unpack results
	
		ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 0)

		return 
	
	def Get(self, key:str):
		global xllr_handle
		global TestMap_Get_id
		global runtime_plugin
		global python_plugin_handle
	
		
		params = (self.obj_handle , key)
		params_types = ( 32768, 4096)
		parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
		return_values_buffer = xllr_handle.alloc_cdts_buffer(1)
	
		# call function
		
		out_error = (c_char_p * 1)(0)
		out_error_len = (c_ulonglong)(0)
		xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
						c_ulonglong(TestMap_Get_id), \
						c_void_p(parameters_buffer), c_ulonglong(2), \
						c_void_p(return_values_buffer), c_ulonglong(1), \
						out_error, byref(out_error_len))
		
		
		# check for error
		if out_error != None and out_error[0] != None:
			err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
			raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))
	
		# unpack results
	
		ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 1)

		return ret_vals[0]
	
	def Contains(self, key:str):
		global xllr_handle
		global TestMap_Contains_id
		global runtime_plugin
		global python_plugin_handle
	
		
		params = (self.obj_handle , key)
		params_types = ( 32768, 4096)
		parameters_buffer = python_plugin_handle.convert_host_params_to_cdts(py_object(params), py_object(params_types))
		return_values_buffer = xllr_handle.alloc_cdts_buffer(1)
	
		# call function
		
		out_error = (c_char_p * 1)(0)
		out_error_len = (c_ulonglong)(0)
		xllr_handle.call(c_char_p(runtime_plugin), c_ulonglong(len(runtime_plugin)), \
						c_ulonglong(TestMap_Contains_id), \
						c_void_p(parameters_buffer), c_ulonglong(2), \
						c_void_p(return_values_buffer), c_ulonglong(1), \
						out_error, byref(out_error_len))
		
		
		# check for error
		if out_error != None and out_error[0] != None:
			err_msg = string_at(out_error[0], out_error_len.value).decode('utf-8')
			raise RuntimeError('\n'+err_msg.replace("\\n", "\n"))
	
		# unpack results
	
		ret_vals = python_plugin_handle.convert_host_return_values_from_cdts(c_void_p(return_values_buffer), 1)

		return ret_vals[0]
	




