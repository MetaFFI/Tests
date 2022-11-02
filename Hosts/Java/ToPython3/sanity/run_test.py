import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):

	shutil.copyfile(tests_root_path+'/Guests/Python3/sanity/TestFuncs.py', 'TestFuncs.py')
	build_metaffi('TestFuncs.py', None, 'openjdk', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('javac -cp ".:./..:TestFuncs_MetaFFIHost.jar:$METAFFI_HOME/xllr.openjdk.bridge.jar:" Main_test.java')
	exec_cmd('java -cp ".:./..:TestFuncs_MetaFFIHost.jar:$METAFFI_HOME/xllr.openjdk.bridge.jar:" sanity.Main_test')
	
	
def cleanup(tests_root_path: str):
	os.remove('TestFuncs.py')
	os.remove('TestFuncs_MetaFFIGuest.py')
	shutil.rmtree('__pycache__')
	os.remove('TestFuncs_MetaFFIHost.jar')
	os.remove('Main_test.class')
	os.remove('testmap.java')
	os.remove('TestFuncs.java')


