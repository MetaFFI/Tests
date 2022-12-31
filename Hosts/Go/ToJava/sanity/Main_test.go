package sanity

import "testing"
import tf "GoToJava/testfuncs"
import tm "GoToJava/testmap"
import "fmt"
import "runtime"
import "os"

func trace(s string) {
    pc := make([]uintptr, 10)  // at least 1 entry needed
    runtime.Callers(2, pc)
    f := runtime.FuncForPC(pc[0])
    file, line := f.FileLine(pc[0])
    fmt.Printf("+++ (%v) %s:%d %s\n", s, file, line, f.Name())
}

func getDynamicLibSuffix() string{
	switch runtime.GOOS{
		case "windows": return ".dll"
		case "darwin": return ".dylib"
		default: // We might need to make this more specific in the future
			return ".so"
	}
}

func TestMain(m *testing.M) {
	p, err := os.Getwd()
	if err != nil{
		panic(err)
	}

	tf.Load(fmt.Sprintf("%v/TestFuncs_MetaFFIGuest%v;%v/TestFuncs_MetaFFIGuest.jar", p, getDynamicLibSuffix(), p))
	tm.Load(fmt.Sprintf("%v/TestMap_MetaFFIGuest%v;%v/TestMap_MetaFFIGuest.jar", p, getDynamicLibSuffix(), p))
    exitVal := m.Run()
    os.Exit(exitVal)
}
//--------------------------------------------------------------------
func TestHelloWorld(t *testing.T){

	err := tf.TestFuncs_HelloWorld()
	if err != nil{
		t.Fatal(err)
	}
}
//--------------------------------------------------------------------
func TestReturnsAnError(t *testing.T){

	err := tf.TestFuncs_ReturnsAnError()
	if err == nil{
		t.Fatal("Error expected")
	}
}
//--------------------------------------------------------------------
func TestDivIntegers(t *testing.T){

	res, err := tf.TestFuncs_DivIntegers(1, 2)
	if err != nil{
		t.Fatal(err)
	}

	if res != 0.5{
		t.Fatalf("Expected 0.5, got: %v", res)
	}

	res, err = tf.TestFuncs_DivIntegers(1, 0)
	if err == nil{
		t.Fatal("Expected an error - divisor is 0")
	}
}
//--------------------------------------------------------------------
func TestJoinStrings(t *testing.T){

	res, err := tf.TestFuncs_JoinStrings([]string{"A", "b", "C"})
	if err != nil{
		t.Fatal(err)
	}

	if res != "A,b,C"{
		t.Fatalf("Expected A,b,C. Got: %v", res)
	}
}
//--------------------------------------------------------------------
func TestWaitABit(t *testing.T){

	fsec, err := tf.TestFuncs_GetfiveSeconds()
	if err != nil{
		t.Fatal(err)
	}

	mffiError := tf.TestFuncs_WaitABit(fsec)
	if mffiError != nil{
		t.Fatal(mffiError)
	}

}
//--------------------------------------------------------------------

func TestTestMap(t *testing.T){

	m, err := tm.NewTestMap()
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

	err = m.Setname("TheMap!")
	if err != nil{
		t.Fatal(err)
	}

	name, err := m.Getname()
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