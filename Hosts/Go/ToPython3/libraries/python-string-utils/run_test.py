import os
import platform
import shutil
from typing import Callable, Optional
import sysconfig
from platform import python_version

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):
	sitepack_path = sysconfig.get_path('purelib')
	sitepack_path = sitepack_path.replace('/usr', sysconfig.get_config_var('userbase'))

	manipulations_file = sitepack_path+'/string_utils/manipulation.py'
	validations_file = sitepack_path+'/string_utils/validation.py'

	build_metaffi(manipulations_file, None, 'go', None)
	build_metaffi(validations_file, None, 'go', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('go get -u')
	exec_cmd('go test')


	
def cleanup(tests_root_path: str):
	os.remove('manipulation_MetaFFIGuest.py')
	os.remove('validation_MetaFFIGuest.py')
	shutil.rmtree('__pycache__')
	os.remove('manipulation_MetaFFIHost.go')
	os.remove('validation_MetaFFIHost.go')
	os.remove('go.sum')
