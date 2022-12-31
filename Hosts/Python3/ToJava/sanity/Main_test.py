import unittest
from TestFuncs_MetaFFIHost import *
import pathlib

filepath = pathlib.Path(__file__).resolve().parent
load('TestFuncs_MetaFFIGuest.so;{}/TestFuncs_MetaFFIGuest.jar'.format(filepath))
class TestSanity(unittest.TestCase):

	def test_hello_world(self):
		TestFuncs.helloWorld()
	#
	# def test_returns_an_error(self):
	# 	try:
	# 		TestFuncs.returnsAnError()
	# 		self.fail('Test should have failed')
	# 	except:
	# 		pass
	#
	# def test_div_integers(self):
	# 	res = TestFuncs.divIntegers(1, 2)
	# 	if res != 0.5:
	# 		self.fail('Expected 0.5, got: '+res)
	#
	# 	try:
	# 		TestFuncs.divIntegers(1, 0)
	# 		self.fail('Expected an error - divisor is 0')
	# 	except:
	# 		pass
	#
	#
	# def test_join_strings(self):
	# 	res = TestFuncs.joinStrings(['A','b','C'])
	# 	if res != 'A,b,C':
	# 		self.fail('Expected A,b,C. Got: '+res)