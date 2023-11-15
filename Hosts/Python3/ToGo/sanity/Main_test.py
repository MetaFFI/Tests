import unittest
from TestFuncs_MetaFFIHost import *
import collections

metaffi_load('TestFuncs_MetaFFIGuest')
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

	def test_wait_a_bit(self):
		fivesec = GetFiveSeconds_metaffi_getter()
		WaitABit(fivesec)

	def test_test_map(self):
		map = TestMap(NewTestMap())

		map.Set('x', 250)
		if not map.Contains('x'):
			self.fail('Map should contain x')

		if map.Get('x') != 250:
			self.fail('x should be 250')

		map.Set('y', 'test')
		if not map.Contains('y'):
			self.fail('Map should contain y')

		if map.Get('y') != 'test':
			self.fail('y should be \'test\'')

		deq = collections.deque()
		deq.append(600)
		map.Set('z', deq)
		if not map.Contains('z'):
			self.fail('Map should contain z')

		mapped_deq = map.Get('z')
		val = mapped_deq.pop()
		if val != 600:
			self.fail('mapped_deq should contain 600')

		map.SetName_metaffi_setter('MyName')
		newname = map.GetName_metaffi_getter()
		if newname != 'MyName':
			self.fail('TestMap.Name should be MyName and it is '+newname)
		
		
		
