package beautifulsoup;

import metaffi.MetaFFIHandle;
import metaffi_host.*;

public class Main_test
{
	public static void main(String[] args) throws metaffi.MetaFFIException
	{
        /*
			url = 'https://www.microsoft.com'
		    response = requests.get(url)
		    soup = BeautifulSoup(response.text, 'html.parser')

		    for link in soup.find_all('a'):
		        print(link.get('href'))
	    */

		bs4.metaffi_load("bs4_MetaFFIGuest");
		requests.metaffi_load("requests_MetaFFIGuest");
        builtins.metaffi_load("builtins_MetaFFIGuest");

        var response = new Response((MetaFFIHandle)requests.get("https://www.microsoft.com"));
        var bs = new BeautifulSoup(response.Gettext_MetaFFIGetter(), "html.parser");

        var links = new list(bs.find_all("a"));

        for(int i=0 ; i<links.__len__() ; i++)
        {
            var link = new Tag((MetaFFIHandle)links.__getitem__(i));

            System.out.printf("Link: %s", link.get("href"));
        }

	}
}