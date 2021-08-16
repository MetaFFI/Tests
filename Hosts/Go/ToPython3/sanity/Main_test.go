package sanity

import (
	"testing"
)

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
func TestWaitABit(t *testing.T){

	fsec, err := GetFiveSeconds()
	if err != nil{
		t.Fatal(err)
	}
	
	shouldBeNullError, mffiError := WaitABit(fsec)
	if mffiError != nil{
		t.Fatal(mffiError)
	}
	
	if shouldBeNullError != nil{
		t.Fatal(shouldBeNullError)
	}
}
//--------------------------------------------------------------------
func TestTestMap(t *testing.T){

	m, err := Testmap()
	if err != nil{
		t.Fatal(err)
	}

	err = m.Set("one", 1)
	if err != nil{
		t.Fatal(err)
	}

	one, err := m.Get("one")
	if err != nil{
		t.Fatal(err)
	}

	if one.(int64) != 1{
		t.Fatalf("Expected one=1. one=%v", one)
	}

	err = m.SetName("TheMap!")
	if err != nil{
		t.Fatal(err)
	}

	name, err := m.GetName()
	if err != nil{
		t.Fatal(err)
	}

	if name != "TheMap!"{
		t.Fatalf("Expected name=TheMap!. name=%v", name)
	}

	type User struct{
		ID string
	}

	u1 := User{ID:"TheUser!"}
	
	err = m.Set("user", u1)
	if err != nil{
		t.Fatal(err)
	}

	u2, err := m.Get("user")
	if err != nil{
		t.Fatal(err)
	}

	u2User, ok := u2.(User)
	if !ok{
		t.Fatalf("u2 is not of type User. u2=%v", u2)
	}

	if u1.ID != u2User.ID{
		t.Fatalf("user ID expeceted to be TheUser!. u2.ID=%v", u2User.ID)
	}
}
//--------------------------------------------------------------------
