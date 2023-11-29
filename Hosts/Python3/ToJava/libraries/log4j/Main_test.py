import unittest
from Log4jClass_MetaFFIHost import *
from Logger_MetaFFIHost import *
import pathlib
import distutils.ccompiler

filepath = pathlib.Path(__file__).resolve().parent
dylib_ext = distutils.ccompiler.new_compiler().shared_lib_extension
metaffi_load('Log4jClass_MetaFFIGuest{};{}/Log4jClass_MetaFFIGuest.jar'.format(dylib_ext, filepath))
metaffi_load('Logger_MetaFFIGuest{};{}/Logger_MetaFFIGuest.jar'.format(dylib_ext, filepath))
class TestSanity(unittest.TestCase):

	def test_log(self):
		obj = Log4jClass()
		logger_handle = obj.Getlogger_metaffi_getter()
		logger = Logger(logger_handle)
		logger.trace("Trace Message!")
		logger.debug("Debug Message!")
		logger.info("Info Message!")
		logger.warn("Warn Message!")
		logger.error("Error Message!")
		logger.fatal("Fatal Message!")
		

