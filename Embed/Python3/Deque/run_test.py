import os
import shutil
from typing import Callable, Optional


def build(build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None]):
	build_metaffi('Main_test.py', 'TestFuncs.go', 'python3')


def execute(exec_cmd: Callable[[str], None]):
	exec_cmd('python3 -m unittest Main_test.TestGoDeque')
	
	
def cleanup():
	os.remove('TestFuncs_MetaFFIGuest.so')
	shutil.rmtree('__pycache__')
	os.remove('TestFuncs_MetaFFIHost.py')
