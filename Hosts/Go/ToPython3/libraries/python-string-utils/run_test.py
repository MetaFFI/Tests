import os
import platform
import shutil
from typing import Callable, Optional
import site
from platform import python_version


def find_vendor_lib_path(lib_name:str):
	pathes_to_check = [site.getusersitepackages()]
	pathes_to_check.extend(site.getsitepackages())

	for p in pathes_to_check:
		if os.path.exists(p+'/'+lib_name):
			return p.replace('\\', '/')

	# none were found
	raise RuntimeError('None of the pathes contains the library "{}". Checked pathes: {}'.format(lib_name, pathes_to_check))


# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str], Optional[str]], None], exec_cmd: Callable[[str], None]):
	# sitepack_path = find_vendor_lib_path('string_utils')
	#
	# manipulations_file = sitepack_path+'/string_utils/manipulation.py'
	# validations_file = sitepack_path+'/string_utils/validation.py'

	build_metaffi('string_utils', 'py', 'go', None)
	# build_metaffi(validations_file, None, 'go', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	exec_cmd('go get -u -t')
	exec_cmd('go test -v')


	
def cleanup(tests_root_path: str, dylib_ext: str):
	shutil.rmtree('__pycache__')
	shutil.rmtree('string_utils')
	os.remove('string_utils_MetaFFIGuest.py')
	os.remove('metaffi_objects.py')
	os.remove('metaffi_objects_MetaFFIGuest.py')
