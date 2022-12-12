import os
import shutil
from typing import Callable, Optional


def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	build_metaffi('Main_test.go', 'TestFuncs.py', 'go', 'package=sanity')


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('go get -u')
	exec_cmd('go test')
	
	
def cleanup(tests_root_path: str):
	os.remove('TestFuncs.py')
	os.remove('TestFuncs_MetaFFIGuest.py')
	shutil.rmtree('__pycache__')
	shutil.rmtree('testfuncs')
