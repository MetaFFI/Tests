package TestFuncs

import (
	"strings"
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

type TestMap struct{
	m map[string]interface{}
}

func NewTestMap() *TestMap{
	return &TestMap{ m: make(map[string]interface{})}
}

func (this *TestMap) SetKey(k string, v interface{}){
	this.m[k] = v
}

func (this *TestMap) GetKey(k string) interface{}{
	return this.m[k]
}

func (this *TestMap) ContainsKey(k string) bool{
	_, found := this.m[k]
	return found
}
