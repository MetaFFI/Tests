package pandas;

import metaffi_host.*;

public class Main_test
{
	public static void main(String[] args) throws metaffi.MetaFFIException
	{
		metaffi_host.pandas.load("pandas_MetaFFIGuest");
		metaffi_host.pandas_core_indexing.load("pandas_core_indexing_MetaFFIGuest");

        var df = new metaffi_host.DataFrame(pandas.read_csv("input.csv"));
        var str = df.to_string();

        var res = "   r11  r12  r13\n0  r21  r22  r23\n1  r31  r32  r33";
        if(!res.equals((String)str))
        {
            System.out.printf("Failed - \"%s\" != \"%s\"", str, res);
            System.exit(1);
        }

        System.out.println(str);

        var iloc = new metaffi_host._iLocIndexer((metaffi.MetaFFIHandle)df.Getiloc());
        var itemDF = new metaffi_host.DataFrame(iloc.__getitem__(1));

        str = itemDF.to_string();
        System.out.println(str);
	}
}