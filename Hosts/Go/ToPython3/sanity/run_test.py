import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):

	shutil.copyfile(tests_root_path+'/Guests/Python3/sanity/TestFuncs.py', 'TestFuncs.py')
	build_metaffi('TestFuncs.py', None, 'go', 'package=sanity')


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('go get -u -t')
	exec_cmd('go test -v')
	
	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('TestFuncs.py')
	os.remove('TestFuncs_MetaFFIGuest.py')
	os.remove('metaffi_objects.py')
	os.remove('metaffi_objects_MetaFFIGuest.py')
	shutil.rmtree('__pycache__')
	shutil.rmtree('testfuncs')
