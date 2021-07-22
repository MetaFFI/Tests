package main

import "testing"

//--------------------------------------------------------------------
func TestInitials(t *testing.T){
	res, err := Initials("James Tiberius Kirk")
	if err != nil{
		t.Fatal(err)
	}

	if res != "JTK"{
		t.Fatalf("Expected JTK, got: %v", res)
	}
}
//--------------------------------------------------------------------
