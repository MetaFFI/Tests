package PythonStringUtils

import "testing"
import "fmt"

//--------------------------------------------------------------------
func TestIsJSON(t *testing.T){
	isJson, err := Is_json("[1, 2, 3]")
	if err != nil{ t.Fatal(err) }

	fmt.Printf("[1, 2, 3]? %v\n", isJson)

	isJson, _ = Is_json("{NOT JSON}")
    fmt.Printf("{NOT JSON}? %v\n", isJson)
}
//--------------------------------------------------------------------
func TestStripHTML(t *testing.T){
	stripped, err := Strip_html(`"test: <a href="foo/bar">click here</a>"`)
	if err != nil{ t.Fatal(err) }
	fmt.Printf("Before: %v\n", `"test: <a href="foo/bar">click here</a>"`)
	fmt.Printf("After: %v\n", stripped)
}
//--------------------------------------------------------------------
