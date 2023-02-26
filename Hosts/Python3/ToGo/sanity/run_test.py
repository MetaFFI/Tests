import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):

	shutil.copyfile(tests_root_path+'/Guests/Go/sanity/TestFuncs.go', 'TestFuncs.go')
	build_metaffi('TestFuncs.go', None, 'python3', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('python3 -m unittest Main_test.TestSanity')
	
	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('TestFuncs.go')
	os.remove('TestFuncs_MetaFFIGuest'+dylib_ext)
	shutil.rmtree('__pycache__')
	os.remove('TestFuncs_MetaFFIHost.py')
