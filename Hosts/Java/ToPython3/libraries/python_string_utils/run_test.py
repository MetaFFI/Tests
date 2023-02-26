import os
import shutil
from typing import Callable, Optional
import sysconfig

# build_metaffi(idl: str, idl_block: Optional[str], host_lang: str, host_options: Optional[str] = None)
def build(tests_root_path: str, build_metaffi: Callable[[str, Optional[str], str, Optional[str]], None], exec_cmd: Callable[[str], None]):

	sitepack_path = sysconfig.get_path('purelib')
	sitepack_path = sitepack_path.replace('/usr', sysconfig.get_config_var('userbase'))

	manipulations_file = sitepack_path+'/string_utils/manipulation.py'
	validations_file = sitepack_path+'/string_utils/validation.py'

	build_metaffi(manipulations_file, None, 'openjdk', None)
	build_metaffi(validations_file, None, 'openjdk', None)


def execute(tests_root_path: str, exec_cmd: Callable[[str], None]):
	metaffi_home = os.getenv("METAFFI_HOME")
	exec_cmd('javac -cp ".{0}./..{0}validation_MetaFFIHost.jar{0}manipulation_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" Main_test.java'.format(os.pathsep, metaffi_home))
	exec_cmd('java -cp ".{0}./..{0}validation_MetaFFIHost.jar{0}manipulation_MetaFFIHost.jar{0}{1}/xllr.openjdk.bridge.jar" python_string_utils.Main_test'.format(os.pathsep, metaffi_home))
	
	
def cleanup(tests_root_path: str, dylib_ext: str):
	os.remove('__ISBNChecker.java')
	os.remove('__RomanNumbers.java')
	os.remove('__StringCompressor.java')
	os.remove('__StringFormatter.java')
	os.remove('InvalidInputError.java')
	os.remove('Main_test.class')
	os.remove('manipulation.java')
	os.remove('manipulation_MetaFFIGuest.py')
	os.remove('manipulation_MetaFFIHost.jar')
	os.remove('validation.java')
	os.remove('validation_MetaFFIGuest.py')
	os.remove('validation_MetaFFIHost.jar')
	shutil.rmtree('__pycache__')


