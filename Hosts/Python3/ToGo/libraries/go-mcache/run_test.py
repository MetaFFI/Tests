import os
import shutil
from typing import Callable, Optional

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	build_metaffi('$GOPATH/pkg/mod/github.com/!orlov!evgeny/go-mcache@v0.0.0-20200121124330-1a8195b34f3a/mcache.go', None, 'python3', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('python3 -m unittest Main_test.TestSanity')
	
	
def cleanup(tests_root_path: str):
	os.remove('mcache_MetaFFIGuest.so')
	os.remove('mcache_MetaFFIHost.py')
	shutil.rmtree('__pycache__')