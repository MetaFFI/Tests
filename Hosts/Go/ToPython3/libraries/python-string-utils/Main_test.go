package pythonStringUtils

import (
	"fmt"
	"testing"
	"pythonStringUtils/string_utils"
)

func TestMain(t *testing.T){

	string_utils.Load("string_utils_MetaFFIGuest")
	//defer string_utils.Free()

	isJson, err := string_utils.IsJson("[1, 2, 3")
	if err != nil{ t.Fatal(err) }
	fmt.Printf("[1, 2, 3? %v\n", isJson)

	isJson, err = string_utils.IsJson(`{ "a": 1 }`)
	if err != nil{ t.Fatal(err) }
    fmt.Printf("{ \"a\": 1 }? %v\n", isJson)

	stripped, err := string_utils.StripHtml(`"test: <a href="foo/bar">click here</a>"`, true)
	if err != nil{ t.Fatal(err) }

	fmt.Printf("Before: %v\n", `"test: <a href="foo/bar">click here</a>"`)
	fmt.Printf("After: %v\n", stripped)
}

