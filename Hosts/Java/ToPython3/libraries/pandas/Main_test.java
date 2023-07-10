package pandas;

import metaffi_host.*;

public class Main_test
{
	public static void main(String[] args) throws metaffi.MetaFFIException
	{
		pandas.metaffi_load("pandas_MetaFFIGuest");
		pandas_core_indexing.metaffi_load("pandas_core_indexing_MetaFFIGuest");
        var df = new DataFrame(pandas.read_csv("input.csv"));
        var iloc = new _iLocIndexer((metaffi.MetaFFIHandle)df.Getiloc_MetaFFIGetter());
        var dfSecondRow = new DataFrame(iloc.__getitem__(1));
        System.out.println(dfSecondRow.to_string());
	}
}