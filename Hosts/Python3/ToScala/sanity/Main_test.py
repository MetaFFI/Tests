import unittest
from Test_MetaFFIHost_pb2 import *

class TestSanity(unittest.TestCase):

	def test_hello_world(self):
		helloWorld()

	def test_returns_an_error(self):
		try:
			returnsAnError()
			self.fail('Test should have failed')
		except:
			pass

	def test_div_integers(self):
		res = divIntegers(1, 2)
		if res != 0.5:
			self.fail('Expected 0.5, got: '+res)

		try:
			divIntegers(1, 0)
			self.fail('Expected an error - divisor is 0')
		except:
			pass


	def test_join_strings(self):
		res = joinStrings(['A','b','C'])
		if res != 'A,b,C':
			self.fail('Expected A,b,C. Got: '+res)