import unittest
from TestFuncs_MetaFFIHost import *
import collections


"""metaffi-block: name=TestFuncs.go

package TestFuncs

import (
	"strings"
	"time"
)

func HelloWorld() {
	println("Hello World, From Go!")
}

func ReturnsAnError(){
	panic("An error from ReturnsAnError")
}

func DivIntegers(x int, y int) float32{

	if y == 0{
		panic("Divisor is 0")
	}

	return float32(x) / float32(y)
}

func JoinStrings(arrs []string) string{
	return strings.Join(arrs, ",")
}

const FiveSeconds = time.Second*5
func WaitABit(d time.Duration) error{
	time.Sleep(d)
	return nil
}

type TestMap struct{
	m map[string]interface{}
	Name string
}

func NewTestMap() *TestMap{
	return &TestMap{ 
		m: make(map[string]interface{}),
		Name: "TestMap Name",
	}
}

func (this *TestMap) Set(k string, v interface{}){
	this.m[k] = v
}

func (this *TestMap) Get(k string) interface{}{
	return this.m[k]
}

func (this *TestMap) Contains(k string) bool{
	_, found := this.m[k]
	return found
}

metaffi-end"""


class TestSanity(unittest.TestCase):

	def test_hello_world(self):
		print('Before hello world')
		HelloWorld()
		print('After hello world')
	

	def test_returns_an_error(self):
		try:
			print('before return an error')
			ReturnsAnError()
			self.fail('Test should have failed')
		except:
			print('after return an error')
			pass


	def test_div_integers(self):
		print('Before div integer 1')
		res = DivIntegers(1, 2)
		print('After div integer 1')
		if res != 0.5:
			self.fail('Expected 0.5, got: '+str(res))

		try:
			print('Before div integer 2')
			DivIntegers(1, 0)
			print('After div integer 2')
			self.fail('Expected an error - divisor is 0')
		except:
			pass


	def test_join_strings(self):
		print('Before join strings')
		res = JoinStrings(['A','b','C'])
		if res != 'A,b,C':
			self.fail('Expected A,b,C. Got: '+res)
		print('After join strings')

	def test_wait_a_bit(self):
		print('before sleep')
		fivesec = GetFiveSeconds()
		WaitABit(fivesec)
		print('after sleep')

	def test_test_map(self):
		print('before map cstr')
		map = TestMap()
		print('after map cstr')

		print('before map set')
		map.Set('x', 250)
		if not map.Contains('x'):
			self.fail('Map should contain x')
		print('after map set')

		print('before map get')
		if map.Get('x') != 250:
			self.fail('x should be 250')
		print('after map get')

		print('before map set 2')
		map.Set('y', 'test')
		if not map.Contains('y'):
			self.fail('Map should contain y')
		print('after map set 2')

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

		print('before set name')
		map.SetName('MyName')
		newname = map.GetName()
		if newname != 'MyName':
			self.fail('TestMap.Name should be MyName and it is '+newname)
		print('after set name')

		print('before del')
		del map
		print('after del')




