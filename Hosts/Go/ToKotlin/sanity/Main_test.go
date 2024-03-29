package sanity

import "testing"

//--------------------------------------------------------------------
func TestHelloWorld(t *testing.T){
	err := HelloWorld()
	if err != nil{
		t.Fatal(err)
	}
}
//--------------------------------------------------------------------
func TestReturnsAnError(t *testing.T){
	err := ReturnsAnError()
	if err == nil{
		t.Fatal("Error expected")
	}
}
//--------------------------------------------------------------------
func TestDivIntegers(t *testing.T){
	res, err := DivIntegers(1, 2)
	if err != nil{
		t.Fatal(err)
	}

	if res != 0.5{
		t.Fatalf("Expected 0.5, got: %v", res)
	}

	res, err = DivIntegers(1, 0)
	if err == nil{
		t.Fatal("Expected an error - divisor is 0")
	}
}
//--------------------------------------------------------------------
func TestJoinStrings(t *testing.T){
	res, err := JoinStrings([]string{"A", "b", "C"})
	if err != nil{
		t.Fatal(err)
	}

	if res != "A,b,C"{
		t.Fatalf("Expected A,b,C. Got: %v", res)
	}
}
//--------------------------------------------------------------------