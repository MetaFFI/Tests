import unittest
import time
from mcache_MetaFFIHost import *

class TestSanity(unittest.TestCase):

	def test_mcache(self):

		INFINITY = GetTTL_FOREVER()

		mcache = CacheDriver()
		mcache.Set('integer', 101, INFINITY)
		l = mcache.Len()
		print('length: {}'.format(l))
		x, found = mcache.Get('integer')

		if x != 101:
			self.fail("x expected to be 101, while it is"+str(x))
			
		print(x)
