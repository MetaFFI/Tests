import os
import shutil
from typing import Callable, Optional


def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	build_metaffi('Main_test.py', 'TestFuncs.go', 'python3')


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('python3 -m unittest Main_test.TestSanity')
	
	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('TestFuncs_MetaFFIGuest'+dylib_ext)
	shutil.rmtree('__pycache__')
	os.remove('TestFuncs_MetaFFIHost.py')
