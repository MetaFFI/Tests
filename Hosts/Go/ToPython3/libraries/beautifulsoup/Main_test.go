package main

import (
	"fmt"
	"os"
	"test/bs4"
	"test/builtins"
	"test/requests"
	"testing"

	metaffi "github.com/MetaFFI/lang-plugin-go/go-runtime"
)

func TestMain(m *testing.M) {

	bs4.MetaFFILoad("bs4_MetaFFIGuest")
	requests.MetaFFILoad("requests_MetaFFIGuest")
	builtins.MetaFFILoad("builtins_MetaFFIGuest")

	exitVal := m.Run()

	os.Exit(exitVal)
}

func TestBeautifulSoup(t *testing.T) {

	/*
			url = 'https://www.microsoft.com'
		    response = requests.get(url)
		    soup = BeautifulSoup(response.text, 'html.parser')

		    for link in soup.find_all('a'):
		        print(link.get('href'))
	*/
	responseHandle, err := requests.Get_Overload1("https://www.microsoft.com")
	if err != nil {
		t.Fatal(err)
	}

	res := requests.Response{}
	res.SetHandle(responseHandle.(metaffi.Handle))

	text, err := res.Gettext_MetaFFIGetter()
	if err != nil {
		t.Fatal(err)
	}

	bs, err := bs4.NewBeautifulSoup_Overload3(text, "html.parser")
	if err != nil {
		t.Fatal(err)
	}

	linksArray, err := bs.Find_All_Overload2("a")
	if err != nil {
		t.Fatal(err)
	}

	lst := builtins.List{}
	lst.SetHandle(linksArray.(metaffi.Handle))

	l, err := lst.U___Len____()
	if err != nil {
		t.Fatal(err)
	}

	for i := int64(0); i < l; i++ {
		tagHandle, err := lst.U___Getitem____(i)
		if err != nil {
			t.Fatal(err)
		}

		tag := bs4.Tag{}
		tag.SetHandle(tagHandle.(metaffi.Handle))

		link, err := tag.Get_Overload1("href")
		if err != nil {
			t.Fatal(err)
		}

		fmt.Printf("Link: %v\n", link)
	}
}
