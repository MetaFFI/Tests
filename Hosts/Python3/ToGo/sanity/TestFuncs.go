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
