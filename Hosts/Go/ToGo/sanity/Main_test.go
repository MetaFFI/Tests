//+build maintest

package main

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
func TestTestMap(t* testing.T){

	m, err := NewTestMap()
	if err != nil{ t.Fatal(err) }
	
	err = SetKey(m, "k1", "v1")
	if err != nil{ t.Fatal(err) }

	exists, err := ContainsKey(m, "k1")
	if err != nil{ t.Fatal(err) }
	if !exists{ t.Fatalf("k1 should exist in map") }

	v, err := GetKey(m, "k1")
	if err != nil{ t.Fatal(err) }

	if v != "v1"{ t.Fatalf("k1 value should be v1, while it is: %v", v) }
}
//--------------------------------------------------------------------