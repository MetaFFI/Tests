import unittest
from TestFuncs_MetaFFIHost import *
import collections
from datetime import datetime


"""metaffi-block: name=TestFuncs.go

package TestFuncs

import (
	"github.com/edwingeng/deque"
)

type GoDeque struct{
	d deque.Deque
	Name string
}

func NewGoDeque() *GoDeque{
	return &GoDeque{ 
		d: deque.NewDeque(),
	}
}

func (this *GoDeque) Push(v interface{}){
	this.d.PushBack(v)
}

func (this *GoDeque) Pop() interface{}{
	return this.d.PopFront()
}
metaffi-end"""


class TestGoDeque(unittest.TestCase):
	# TODO - Remove HelloWorld function!

	def test_go_deque(self):
		d = GoDeque()

		d.Push(250)
		d.Push(['test', 'me'])

		deq = collections.deque()
		deq.append(600)
		d.Push(deq)

		self.assertEqual(d.Pop(), 250)
		self.assertEqual(d.Pop(), ['test', 'me'])
		self.assertEqual(d.Pop(), deq)

		d.SetName('GoDeque')
		self.assertEqual(d.GetName(), 'GoDeque')




		
