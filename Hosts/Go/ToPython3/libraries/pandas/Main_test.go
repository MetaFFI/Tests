package main

import (
	"fmt"
	metaffi "github.com/MetaFFI/lang-plugin-go/go-runtime"
	"os"
	"test/metaffi_objects"
	"test/pandas"
 	"test/pandas_core_indexing"
	"testing"
	"strings"
)

func TestMain(m *testing.M) {

	pandas.MetaFFILoad("pandas_MetaFFIGuest")
	metaffi_objects.MetaFFILoad("metaffi_objects_MetaFFIGuest")
 	pandas_core_indexing.MetaFFILoad("pandas_core_indexing_MetaFFIGuest")

	exitVal := m.Run()

	os.Exit(exitVal)
}

func TestPandas(t *testing.T) {

	dfHandle, err := pandas.Read_Csv1("input.csv")
	if err != nil {
		t.Fatal(err)
	}

	df := pandas.DataFrame{}
	df.SetHandle(dfHandle.(metaffi.Handle))

	str, err := df.To_String1()
	if err != nil {
		t.Fatal(err)
	}

	res := `  col1 col2 col3
0  r11  r12  r13
1  r21  r22  r23`

	fmt.Println("df.to_string()")
	fmt.Println(str)

	if strings.TrimSpace(str.(string)) != strings.TrimSpace(res) {
		t.Fatalf("\"%v\" != \"%v\"", str, res)
	}

	ilocHandle, err := df.Getiloc_MetaFFIGetter()
	if err != nil {
		t.Fatal(err)
	}

	// TODO: if starts with "_" remove "_"
	iloc := pandas_core_indexing.U__ILocIndexer{}
	iloc.SetHandle(ilocHandle.(metaffi.Handle))

	dfHandle, err = iloc.U___Getitem____(1)
	if err != nil {
		t.Fatal(err)
	}

	df.SetHandle(dfHandle.(metaffi.Handle))

	str, err = df.To_String1()
	if err != nil {
		t.Fatal(err)
	}

	fmt.Println("iloc[1].to_string()")
	fmt.Println(str)

}
