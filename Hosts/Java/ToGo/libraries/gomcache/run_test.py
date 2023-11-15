import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	shutil.copyfile(tests_root_path+'/Guests/Go/libraries/gomcache/go.mod', 'go.mod')
	shutil.copyfile(tests_root_path+'/Guests/Go/libraries/gomcache/go.sum', 'go.sum')
	exec_cmd('go get github.com/OrlovEvgeny/go-mcache@v0.0.0-20200121124330-1a8195b34f3a')
	build_metaffi('$GOPATH/pkg/mod/github.com/!orlov!evgeny/go-mcache@v0.0.0-20200121124330-1a8195b34f3a/mcache.go', None, 'openjdk', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	metaffi_home = os.getenv("METAFFI_HOME")
	exec_cmd('javac -cp ".{0}./..{0}mcache_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" Main_test.java'.format(os.pathsep, metaffi_home))
	exec_cmd('java -cp ".{0}./..{0}mcache_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" gomcache.Main_test'.format(os.pathsep, metaffi_home))


def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('mcache_MetaFFIGuest'+dylib_ext)
	os.remove('mcache_MetaFFIHost.jar')
	os.remove('Main_test.class')
	os.remove('go.mod')
	os.remove('go.sum')
