import unittest
from Test_OpenFFIHost import *

class TestSanity(unittest.TestCase):

	def test_hello_world(self):
		HelloWorld()

	def test_returns_an_error(self):
		try:
			ReturnsAnError()
			self.fail('Test should have failed')
		except:
			pass


	def test_div_integers(self):
		res = DivIntegers(1, 2)
		if res != 0.5:
			self.fail('Expected 0.5, got: '+str(res))

		try:
			DivIntegers(1, 0)
			self.fail('Expected an error - divisor is 0')
		except:
			pass

	def test_join_strings(self):
		res = JoinStrings(['A','b','C'])
		if res != 'A,b,C':
			self.fail('Expected A,b,C. Got: '+res)
