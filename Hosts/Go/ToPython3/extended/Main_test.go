package sanity

import (
	"test/extended_test"
	"test/collections"
	"test/metaffi_objects"
	"os"
	"testing"
	. "github.com/MetaFFI/lang-plugin-go/go-runtime"
	"fmt"
)

// --------------------------------------------------------------------
func TestMain(m *testing.M) {
	extended_test.MetaFFILoad("extended_test_MetaFFIGuest")
	collections.MetaFFILoad("collections_MetaFFIGuest")
	metaffi_objects.MetaFFILoad("metaffi_objects_MetaFFIGuest")

	exitVal := m.Run()

	os.Exit(exitVal)
}
//--------------------------------------------------------------------
func TestPositionalOrNamed(t *testing.T) {
	ext, err := extended_test.NewExtended_Test()
	if err != nil{ t.Fatal(err) }

	err = ext.Setx_MetaFFISetter(4)
	if err != nil{ t.Fatal(err) }

	x, err := ext.Getx_MetaFFIGetter()
	if err != nil{ t.Fatal(err) }

	if x != 4{
		t.Fatalf("x != 4. x == %v", x)
	}

	// PositionalOrNamed()

	str, err := ext.Positional_Or_Named("PositionalOrNamed") // positional_or_named('PositionalOrNamed')
	if err != nil{ t.Fatal(err) }

	if str != "PositionalOrNamed"{
		t.Fatalf("\"str\" != %v", str)
	}
}
//--------------------------------------------------------------------
func TestPositionalOrNamedMultiTypeHint1(t *testing.T){

	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

	str, err := ext.Positional_Or_Named_Multi_Type_Hint1("arg1") // positional_or_named_multi_type_hint('arg1')
    if err != nil{ t.Fatal(err) }
    if str != "arg1"{
        t.Fatalf("\"arg1\" != %v", str)
    }
}
//--------------------------------------------------------------------
func TestPositionalOrNamedMultiTypeHint(t *testing.T){

	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

	str, err := ext.Positional_Or_Named_Multi_Type_Hint("arg1", "arg2")  // positional_or_named_multi_type_hint('arg1', 'arg2')
    if err != nil{ t.Fatal(err) }
    if str != "arg1 arg2"{
        t.Fatalf("\"arg1 arg2\" != %v", str)
    }
}
//--------------------------------------------------------------------
func TestListArgs1(t *testing.T){

	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

	listHandle, err := ext.List_Args1() // list_args()
    if err != nil{ t.Fatal(err) }

    lst := collections.UserList{}
    lst.SetHandle(listHandle.(Handle))

    item0, err := lst.U___Getitem____(0) // get first item
    if err != nil{ t.Fatal(err) }

    if item0.(string) != "default"{
        t.Fatalf("\"default\" != %v", item0)
    }
}
//--------------------------------------------------------------------
func TestListArgs2(t *testing.T){

	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

	listHandle, err := ext.List_Args2("None Default") // list_args('None Default')
    if err != nil{ t.Fatal(err) }

    lst := collections.UserList{}
    lst.SetHandle(listHandle.(Handle))

    item0, err := lst.U___Getitem____(0) // get first item
    if err != nil{ t.Fatal(err) }

    if item0.(string) != "None Default"{
        t.Fatalf("\"None Default\" != %v", item0)
    }
}
//--------------------------------------------------------------------
func TestListArgs(t *testing.T){

	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

    listArgs, err := metaffi_objects.NewMetaffi_Positional_Args()
    if err != nil{ t.Fatal(err) }

    err = listArgs.Set_Arg("arg1")
    if err != nil{ t.Fatal(err) }

    err = listArgs.Set_Arg("arg2")
    if err != nil{ t.Fatal(err) }

    err = listArgs.Set_Arg("arg3")
    if err != nil{ t.Fatal(err) }

    listHandle, err := ext.List_Args("None-Default 2", listArgs.GetHandle())
    if err != nil{ t.Fatal(err) }

    lst := collections.UserList{}
    lst.SetHandle(listHandle.(Handle))

	len, err := lst.U___Len____()
	if err != nil{ t.Fatal(err) }
	fmt.Printf("returned list size: %v\n", len)

    item0, err := lst.U___Getitem____(0) // get first item
    if err != nil{ t.Fatal(err) }
    if item0.(string) != "None-Default 2"{
        t.Fatalf("\"None-Default 2\" != %v", item0)
    }

    item1, err := lst.U___Getitem____(1) // get first item
    if err != nil{ t.Fatal(err) }
    if item1.(string) != "arg1"{
        t.Fatalf("\"arg1\" != %v", item1)
    }

    item2, err := lst.U___Getitem____(2) // get first item
    if err != nil{ t.Fatal(err) }
    if item2.(string) != "arg2"{
        t.Fatalf("\"arg2\" != %v", item2)
    }

    item3, err := lst.U___Getitem____(3) // get first item
    if err != nil{ t.Fatal(err) }
    if item3.(string) != "arg3"{
        t.Fatalf("\"arg3\" != %v", item3)
    }

}
//--------------------------------------------------------------------
func TestDictArgs1(t *testing.T){

	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

	res, err := ext.Dict_Args1()
	if err != nil{ t.Fatal(err) }

	lst := collections.UserList{}
    lst.SetHandle(res.(Handle))

    item0, err := lst.U___Getitem____(0) // get first item
    if err != nil{ t.Fatal(err) }
    if item0.(string) != "default"{
        t.Fatalf("\"default\" != %v", item0)
    }
}
//--------------------------------------------------------------------
func TestDictArgs2(t *testing.T){

	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

	res, err := ext.Dict_Args2("none-default")
	if err != nil{ t.Fatal(err) }

	lst := collections.UserList{}
    lst.SetHandle(res.(Handle))

    item0, err := lst.U___Getitem____(0) // get first item
    if err != nil{ t.Fatal(err) }
    if item0.(string) != "none-default"{
        t.Fatalf("\"none-default\" != %v", item0)
    }
}
//--------------------------------------------------------------------
func TestDictArgs(t *testing.T){

	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

	dictArgs, err := metaffi_objects.NewMetaffi_Keyword_Args()
	if err != nil{ t.Fatal(err) }

	err = dictArgs.Set_Arg("key1", "val1");
	if err != nil{ t.Fatal(err) }

	res, err := ext.Dict_Args("none-default", dictArgs.GetHandle())
	if err != nil{ t.Fatal(err) }

	lst := collections.UserList{}
    lst.SetHandle(res.(Handle))

    item0, err := lst.U___Getitem____(0) // get first item
    if err != nil{ t.Fatal(err) }
    if item0.(string) != "none-default"{
        t.Fatalf("\"none-default\" != %v", item0)
    }

    item1, err := lst.U___Getitem____(1) // get first item
    if err != nil{ t.Fatal(err) }
    if item1.(string) != "key1"{
        t.Fatalf("\"key1\" != %v", item1)
    }

    item2, err := lst.U___Getitem____(2) // get first item
    if err != nil{ t.Fatal(err) }
    if item2.(string) != "val1"{
        t.Fatalf("\"val1\" != %v", item2)
    }
}
//--------------------------------------------------------------------
func TestNamedOnly(t *testing.T){

	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

    kwargs, err := metaffi_objects.NewMetaffi_Keyword_Args()
    if err != nil{ t.Fatal(err) }
    kwargs.Set_Arg("named", "test")

	res, err := ext.Named_Only(kwargs.GetHandle())
	if err != nil{ t.Fatal(err) }

	if res != "test"{
		t.Fatalf("\"test\" != %v", res)
	}
}
//--------------------------------------------------------------------
func TestPositionalOnly1(t *testing.T){
	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

    res, err := ext.Positional_Only1("word1")
    if err != nil{ t.Fatal(err) }

    if res != "word1 default"{
        t.Fatalf("\"word1 default\" != %v", res)
    }
}
//--------------------------------------------------------------------
func TestPositionalOnly(t *testing.T){
	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

    res, err := ext.Positional_Only("word1", "word2")
    if err != nil{ t.Fatal(err) }

    if res != "word1 word2"{
        t.Fatalf("\"word1 word2\" != %v", res)
    }
}
//--------------------------------------------------------------------
func TestArgPositionalArgNamed1(t *testing.T){
	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

    lstHandle, err := ext.Arg_Positional_Arg_Named1()
    if err != nil{ t.Fatal(err) }

    lst := collections.UserList{}
    lst.SetHandle(lstHandle.(Handle))

    item0, err := lst.U___Getitem____(0) // get first item
    if err != nil{ t.Fatal(err) }
    if item0.(string) != "default"{
        t.Fatalf("\"default\" != %v", item0)
    }

}
//--------------------------------------------------------------------
func TestArgPositionalArgNamed2(t *testing.T){
	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

    lstHandle, err := ext.Arg_Positional_Arg_Named2("positional arg")
    if err != nil{ t.Fatal(err) }

    lst := collections.UserList{}
    lst.SetHandle(lstHandle.(Handle))

    item0, err := lst.U___Getitem____(0) // get first item
    if err != nil{ t.Fatal(err) }
    if item0.(string) != "positional arg"{
        t.Fatalf("\"positional arg\" != %v", item0)
    }

}
//--------------------------------------------------------------------
func TestArgPositionalArgNamed3(t *testing.T){
	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

    listArgs, err := metaffi_objects.NewMetaffi_Positional_Args()
    if err != nil{ t.Fatal(err) }

    err = listArgs.Set_Arg("var positional arg")
    if err != nil{ t.Fatal(err) }

    lstHandle, err := ext.Arg_Positional_Arg_Named3("positional arg", listArgs.GetHandle())
    if err != nil{ t.Fatal(err) }

    lst := collections.UserList{}
    lst.SetHandle(lstHandle.(Handle))

    item0, err := lst.U___Getitem____(0) // get first item
    if err != nil{ t.Fatal(err) }
    if item0.(string) != "positional arg"{
        t.Fatalf("\"positional arg\" != %v", item0)
    }

    item1, err := lst.U___Getitem____(1) // get first item
    if err != nil{ t.Fatal(err) }
    if item1.(string) != "var positional arg"{
        t.Fatalf("\"var positional arg\" != %v", item1)
    }
}
//--------------------------------------------------------------------
func TestArgPositionalArgNamed(t *testing.T){
	ext, err := extended_test.NewExtended_Test()
    if err != nil{ t.Fatal(err) }

    listArgs, err := metaffi_objects.NewMetaffi_Positional_Args()
    if err != nil{ t.Fatal(err) }

    err = listArgs.Set_Arg("var positional arg")
    if err != nil{ t.Fatal(err) }

    kwargs, err := metaffi_objects.NewMetaffi_Keyword_Args()
	if err != nil{ t.Fatal(err) }

	err = kwargs.Set_Arg("key1", "val1")
	if err != nil{ t.Fatal(err) }

    lstHandle, err := ext.Arg_Positional_Arg_Named("positional arg", listArgs.GetHandle(), kwargs.GetHandle())
    if err != nil{ t.Fatal(err) }

    lst := collections.UserList{}
    lst.SetHandle(lstHandle.(Handle))

    item0, err := lst.U___Getitem____(0) // get first item
    if err != nil{ t.Fatal(err) }
    if item0.(string) != "positional arg"{
        t.Fatalf("\"positional arg\" != %v", item0)
    }

    item1, err := lst.U___Getitem____(1) // get first item
    if err != nil{ t.Fatal(err) }
    if item1.(string) != "var positional arg"{
        t.Fatalf("\"var positional arg\" != %v", item1)
    }

    item2, err := lst.U___Getitem____(2) // get first item
    if err != nil{ t.Fatal(err) }
    if item2.(string) != "key1"{
        t.Fatalf("\"key1\" != %v", item2)
    }

    item3, err := lst.U___Getitem____(3) // get first item
    if err != nil{ t.Fatal(err) }
    if item3.(string) != "val1"{
        t.Fatalf("\"val1\" != %v", item3)
    }
}
//--------------------------------------------------------------------