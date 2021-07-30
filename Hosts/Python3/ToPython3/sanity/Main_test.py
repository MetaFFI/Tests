import unittest
from Test_MetaFFIHost import *

class TestSanity(unittest.TestCase):

	def test_hello_world(self):
		hello_world()

	def test_returns_an_error(self):
		try:
			returns_an_error()
			self.fail('Test should have failed')
		except:
			pass


	def test_div_integers(self):
		res = div_integers(1, 2)
		if res != 0.5:
			self.fail('Expected 0.5, got: '+str(res))

		try:
			div_integers(1, 0)
			self.fail('Expected an error - divisor is 0')
		except:
			pass

	def test_join_strings(self):
		res = join_strings(['A','b','C'])
		if res != 'A,b,C':
			self.fail('Expected A,b,C. Got: '+res)

	def test_testmap(self):
		m = testmap()
		set_key(m, 'k1', 'v1')
		if not contains_key(m, 'k1'):
			self.fail('Key k1 should be set')

		v = get_key(m, 'k1')
		if v != 'v1':
			self.fail('value of k1 expected to be v1, while it is: '+v)