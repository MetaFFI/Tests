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

	pandas.Load("pandas_MetaFFIGuest")
	metaffi_objects.Load("metaffi_objects_MetaFFIGuest")
 	pandas_core_indexing.Load("pandas_core_indexing_MetaFFIGuest")

	exitVal := m.Run()

	os.Exit(exitVal)
}

func TestPandas(t *testing.T) {

	dfHandle, err := pandas.ReadCsv1("input.csv")
	if err != nil {
		t.Fatal(err)
	}

	df := pandas.DataFrame{}
	df.SetHandle(dfHandle.(metaffi.Handle))

	str, err := df.ToString1()
	if err != nil {
		t.Fatal(err)
	}

	res := `   r11  r12  r13
0  r21  r22  r23
1  r31  r32  r33
`

	fmt.Println("df.to_string()")
	fmt.Println(str)

	if strings.TrimSpace(str.(string)) != strings.TrimSpace(res) {
		t.Fatalf("\"%v\" != \"%v\"", str, res)
	}

	ilocHandle, err := df.Getiloc()
	if err != nil {
		t.Fatal(err)
	}

	// TODO: if starts with "_" remove "_"
	iloc := pandas_core_indexing.U_ILocIndexer{}
	iloc.SetHandle(ilocHandle.(metaffi.Handle))

	dfHandle, err = iloc.U_Getitem__(1)
	if err != nil {
		t.Fatal(err)
	}

	df.SetHandle(dfHandle.(metaffi.Handle))

	str, err = df.ToString1()
	if err != nil {
		t.Fatal(err)
	}

	fmt.Println("iloc[1].to_string()")
	fmt.Println(str)

	// ************  TODO:  metaffi -c --idl pandas.core.indexing.py --idl-plugin py -g -h go;
	//                      generates pandas.core_MetaFFIGuest, and it should be "pandas_core_indexing_MetaFFIGuest"
}
