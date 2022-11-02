import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):

	shutil.copyfile(tests_root_path+'/Guests/Go/sanity/TestFuncs.go', 'TestFuncs.go')
	shutil.copyfile(tests_root_path+'/Guests/Go/sanity/go.mod', 'go.mod')
	build_metaffi('TestFuncs.go', None, 'openjdk', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('javac -cp ".:./..:TestFuncs_MetaFFIHost.jar:$METAFFI_HOME/xllr.openjdk.bridge.jar:" Main_test.java')
	exec_cmd('java -cp ".:./..:TestFuncs_MetaFFIHost.jar:$METAFFI_HOME/xllr.openjdk.bridge.jar:" sanity.Main_test')
	
	
def cleanup(tests_root_path: str):
	os.remove('TestFuncs.go')
	os.remove('go.mod')
	os.remove('TestFuncs_MetaFFIGuest.so')
	os.remove('TestFuncs_MetaFFIHost.jar')
	os.remove('Main_test.class')
	os.remove('TestMap.java')
	os.remove('go.java')


