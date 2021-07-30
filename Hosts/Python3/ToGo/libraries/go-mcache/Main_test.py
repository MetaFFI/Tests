import unittest
import time
from mcache_MetaFFIHost import *

class TestSanity(unittest.TestCase):

	def test_mcache(self):

		INFINITY = 87660*60*60*1000*1000*1000

		mcache = New()
		print(mcache.handle)
		Set(mcache, 'integer', 101, INFINITY)
		x, found = Get(mcache, 'integer')

		if x != 101:
			self.fail("x expected to be 101, while it is"+str(x))
			
		print(x)
