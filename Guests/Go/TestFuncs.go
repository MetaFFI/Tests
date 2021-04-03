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

func PrintMap(m map[string]string){
	println(m)
}

func JoinStrings(arrs []string) string{
	return strings.Join(arrs, ",")
}