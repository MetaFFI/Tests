import os
import shutil
from typing import Callable, Optional


def build(build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None]):
	build_metaffi('Main_test.go', 'TestFuncs.py', 'go', 'package=sanity')


def execute(exec_cmd: Callable[[str], None]):
	exec_cmd('go get -u')
	exec_cmd('go test')
	
	
def cleanup():
	os.remove('TestFuncs.py')
	os.remove('TestFuncs_MetaFFIGuest.py')
	shutil.rmtree('__pycache__')
	os.remove('TestFuncs_MetaFFIHost.go')
	os.remove('go.sum')
