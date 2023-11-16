import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	os.mkdir('sanity')
	shutil.copyfile(tests_root_path +'/Guests/Java/sanity_bytecode/TestFuncs.class', 'sanity/TestFuncs.class')
	build_metaffi('sanity\\TestFuncs.class', 'java', 'python3', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('python3 -m unittest Main_test.TestSanity')
	
	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('TestFuncs_MetaFFIGuest.jar')
	os.remove('TestFuncs_MetaFFIGuest'+dylib_ext)
	shutil.rmtree('__pycache__')
	os.remove('TestFuncs_MetaFFIHost.py')
	os.remove('sanity/TestFuncs.class')
	os.rmdir('sanity')
