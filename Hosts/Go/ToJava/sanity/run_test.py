import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):

	shutil.copyfile(tests_root_path+'/Guests/Java/sanity/TestFuncs.java', 'TestFuncs.java')
	build_metaffi('TestFuncs.java', None, 'go', 'package=sanity')


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('go get -u')
	exec_cmd('go test')
	
	
def cleanup(tests_root_path: str):
	os.remove('TestFuncs.java')
	os.remove('TestFuncs_MetaFFIGuest.jar')
	os.remove('TestFuncs_MetaFFIGuest.so')
	os.remove('TestFuncs_MetaFFIHost.go')
	os.remove('go.sum')