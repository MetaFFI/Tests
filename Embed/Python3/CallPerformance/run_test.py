import os
import shutil
from typing import Callable, Optional


def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	build_metaffi('Main_test.py', 'TestFuncs.go', 'python3', None)
	os.chdir('GoDequeDirect')
	exec_cmd('go build -buildmode=c-shared -o GoDequeDirect.so')
	os.chdir('..')
	shutil.copyfile('GoDequeDirect/GoDequeDirect.so', 'GoDequeDirect.so')


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('python3 -m unittest Main_test.TestCallPerformance')
	
	
def cleanup(tests_root_path: str):
	os.remove('TestFuncs_MetaFFIGuest.so')
	shutil.rmtree('__pycache__')
	os.remove('TestFuncs_MetaFFIHost.py')
	os.remove('GoDequeDirect.so')
	os.remove('GoDequeDirect/GoDequeDirect.so')
	os.remove('GoDequeDirect/GoDequeDirect.h')
