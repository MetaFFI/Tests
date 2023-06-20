import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):

	shutil.copyfile(tests_root_path+'/Guests/Python3/sanity/TestFuncs.py', 'TestFuncs.py')
	build_metaffi('TestFuncs.py', None, 'openjdk', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	metaffi_home = os.getenv("METAFFI_HOME")
	exec_cmd('javac -cp ".{0}./..{0}TestFuncs_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" Main_test.java'.format(os.pathsep, metaffi_home))
	exec_cmd('java -cp ".{0}./..{0}TestFuncs_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" sanity.Main_test'.format(os.pathsep, metaffi_home))
	
	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('TestFuncs.py')
	os.remove('TestFuncs_MetaFFIGuest.py')
	shutil.rmtree('__pycache__')
	os.remove('TestFuncs_MetaFFIHost.jar')
	os.remove('Main_test.class')
	os.remove('metaffi_objects.py')
	os.remove('metaffi_objects_MetaFFIGuest.py')


