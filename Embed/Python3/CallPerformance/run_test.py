import os
import shutil
from typing import Callable, Optional
import distutils.ccompiler

def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	dylib_ext: str = distutils.ccompiler.new_compiler().shared_lib_extension

	build_metaffi('Main_test.py', 'TestFuncs.go', 'python3', None)
	os.chdir('GoDequeDirect')
	exec_cmd('go build -buildmode=c-shared -o GoDequeDirect'+dylib_ext)
	os.chdir('..')
	shutil.copyfile('GoDequeDirect/GoDequeDirect'+dylib_ext, 'GoDequeDirect'+dylib_ext)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('python3 -m unittest Main_test.TestCallPerformance')
	
	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('TestFuncs_MetaFFIGuest'+dylib_ext)
	shutil.rmtree('__pycache__')
	os.remove('TestFuncs_MetaFFIHost.py')
	os.remove('GoDequeDirect'+dylib_ext)
	os.remove('GoDequeDirect/GoDequeDirect'+dylib_ext)
	os.remove('GoDequeDirect/GoDequeDirect.h')
