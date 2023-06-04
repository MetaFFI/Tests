package extended;

import metaffi.MetaFFIHandle;
import metaffi_host.*;

public class Main_test
{
	public static void main(String[] args)
	{
		try
		{
 			metaffi_host.collections.load("collections_MetaFFIGuest");
 			metaffi_host.extended_testModule.load("extended_test_MetaFFIGuest");
            metaffi_host.metaffi_objects.load("metaffi_objects_MetaFFIGuest");
            System.out.println("--- test_property");
            test_property();

            System.out.println("--- test_positional_or_named");
			test_positional_or_named();

            System.out.println("--- test_positional_or_named_multi_type_hint");
			test_positional_or_named_multi_type_hint();

            System.out.println("--- test_list_args");
			test_list_args();

            System.out.println("--- test_dict_args");
            test_dict_args();

            System.out.println("--- test_named_only");
			test_named_only();

            System.out.println("--- test_positional_only");
			test_positional_only();

            System.out.println("--- test_arg_positional_arg_named");
			test_arg_positional_arg_named();
		}
		catch(Exception e)
		{
			System.out.println("Unexpected exception has occurred during tests");
			e.printStackTrace();
			System.exit(1);
		}
	}

    private static void test_property() throws Exception
    {
        var ext = new extended_test();

        ext.Setx(4);
        var x = ext.Getx();

        if(x != 4)
        {
            throw new Exception(String.format("Expected to return 4, returned %d", x));
        }
    }

	private static void test_positional_or_named() throws Exception
	{
        var ext = new extended_test();

        var str = ext.positional_or_named("PositionalOrNamed"); // positional_or_named('PositionalOrNamed')
        if(!str.equals("PositionalOrNamed")){
            throw new Exception(String.format("\"str\" != %s", str));
        }
	}

	private static void test_positional_or_named_multi_type_hint() throws Exception
	{
		var ext = new extended_test();

        var str = ext.positional_or_named_multi_type_hint("arg1"); // positional_or_named_multi_type_hint('arg1')
        if(!str.equals("arg1")){
            throw new Exception(String.format("\"arg1\" != %s", str));
        }

        str = ext.positional_or_named_multi_type_hint("arg1", "arg2"); // positional_or_named_multi_type_hint('arg1')
        if(!str.equals("arg1 arg2")){
            throw new Exception(String.format("\"arg1 arg2\" != %s", str));
        }
	}

	private static void test_list_args() throws Exception
	{
		var ext = new extended_test();

        MetaFFIHandle listHandle = (MetaFFIHandle)ext.list_args(); // list_args()

        var lst = new metaffi_host.UserList(listHandle);

        var item0 = lst.__getitem__(0); // get first item
        if (!((String)item0).equals("default")){
            throw new Exception(String.format("\"default\" != %s", (String)item0));
        }

		//---------------

        listHandle = (MetaFFIHandle)ext.list_args("None Default"); // list_args()

        lst = new metaffi_host.UserList(listHandle);

        item0 = lst.__getitem__(0); // get first item
        if (!((String)item0).equals("None Default")){
            throw new Exception(String.format("\"None Default\" != %s", (String)item0));
        }

        //---------------

		var list_args = new metaffi_host.metaffi_positional_args();
		list_args.set_arg("arg1");
		list_args.set_arg("arg2");
		list_args.set_arg("arg3");

        listHandle = (MetaFFIHandle)ext.list_args("None-Default 2", list_args.getHandle()); // list_args()

        lst = new metaffi_host.UserList(listHandle);

        item0 = lst.__getitem__(0); // get first item
        if (!((String)item0).equals("None-Default 2")){
            throw new Exception(String.format("\"None-Default 2\" != %s", (String)item0));
        }

        var item1 = lst.__getitem__(1);
        if (!((String)item1).equals("arg1")){
            throw new Exception(String.format("\"arg1\" != %s", (String)item1));
        }

        var item2 = lst.__getitem__(2);
        if (!((String)item2).equals("arg2")){
            throw new Exception(String.format("\"arg2\" != %s", (String)item2));
        }

        var item3 = lst.__getitem__(3);
        if (!((String)item3).equals("arg3")){
            throw new Exception(String.format("\"arg3\" != %s", (String)item3));
        }
	}

	private static void test_dict_args() throws Exception
    {
        var ext = new extended_test();

        MetaFFIHandle lstHandle = (MetaFFIHandle)ext.dict_args();
        var lst = new metaffi_host.UserList(lstHandle);

        var item0 = lst.__getitem__(0);
        if (!((String)item0).equals("default")){
            throw new Exception(String.format("\"default\" != %s", (String)item0));
        }

        //-------

		lstHandle = (MetaFFIHandle)ext.dict_args("none-default");
		lst = new metaffi_host.UserList(lstHandle);
		item0 = lst.__getitem__(0);
        if (!((String)item0).equals("none-default")){
            throw new Exception(String.format("\"none-default\" != %s", (String)item0));
        }

        //-------

        var keyword_args = new metaffi_keyword_args();
        keyword_args.set_arg("key1", "val1");

        lstHandle = (MetaFFIHandle)ext.dict_args("none-default", keyword_args.getHandle());

		lst = new metaffi_host.UserList(lstHandle);
        item0 = lst.__getitem__(0);
        if (!((String)item0).equals("none-default")){
            throw new Exception(String.format("\"none-default\" != %s", (String)item0));
        }

        lst = new metaffi_host.UserList(lstHandle);
        var item1 = lst.__getitem__(1);
        if (!((String)item1).equals("key1")){
            throw new Exception(String.format("\"key1\" != %s", (String)item1));
        }

        lst = new metaffi_host.UserList(lstHandle);
        var item2 = lst.__getitem__(2);
        if (!((String)item2).equals("val1")){
            throw new Exception(String.format("\"val1\" != %s", (String)item2));
        }
    }

	private static void test_named_only() throws Exception
    {
        var ext = new extended_test();
        var keyword_args = new metaffi_keyword_args();
        keyword_args.set_arg("named", "test");

        var res = ext.named_only(keyword_args.getHandle());

		if (!res.equals("test")){
            throw new Exception(String.format("\"test\" != %s", res));
        }
    }

    private static void test_positional_only() throws Exception
    {
        var ext = new extended_test();

        String res = ext.positional_only("word1");

        if (!res.equals("word1 default")){
            throw new Exception(String.format("\"word1 default\" != %s", res));
        }

        res = ext.positional_only("word1", "word2");

        if (!res.equals("word1 word2")){
            throw new Exception(String.format("\"word1 word2\" != %s", res));
        }
    }

    private static void test_arg_positional_arg_named() throws Exception
    {
        var ext = new extended_test();
		var lstHandle = ext.arg_positional_arg_named();

		var lst = new metaffi_host.UserList(lstHandle);
		var item0 = lst.__getitem__(0);
        if (!((String)item0).equals("default")){
            throw new Exception(String.format("\"default\" != %s", (String)item0));
        }

		//-----

		lstHandle = (MetaFFIHandle)ext.arg_positional_arg_named("positional arg");
        lst = new metaffi_host.UserList(lstHandle);
        item0 = lst.__getitem__(0);
        if (!((String)item0).equals("positional arg")){
            throw new Exception(String.format("\"default\" != %s", (String)item0));
        }

        //-----

	    var listArgs = new metaffi_positional_args();
	    listArgs.set_arg("var positional arg");

        lstHandle = (MetaFFIHandle)ext.arg_positional_arg_named("positional arg", listArgs.getHandle());

        lst = new metaffi_host.UserList(lstHandle);
        item0 = lst.__getitem__(0);
        if (!((String)item0).equals("positional arg")){
            throw new Exception(String.format("\"default\" != %s", (String)item0));
        }

        var item1 = lst.__getitem__(1);
        if (!((String)item1).equals("var positional arg")){
            throw new Exception(String.format("\"var positional arg\" != %s", (String)item1));
        }

        //-----
        var keyword_args = new metaffi_keyword_args();
        keyword_args.set_arg("key1", "val1");

        lstHandle = ext.arg_positional_arg_named("positional arg", listArgs.getHandle(), keyword_args.getHandle());

        lst = new metaffi_host.UserList(lstHandle);
        item0 = lst.__getitem__(0);
        if (!((String)item0).equals("positional arg")){
            throw new Exception(String.format("\"default\" != %s", (String)item0));
        }

        item1 = lst.__getitem__(1);
        if (!((String)item1).equals("var positional arg")){
            throw new Exception(String.format("\"var positional arg\" != %s", (String)item1));
        }

        var item2 = lst.__getitem__(2);
        if (!((String)item2).equals("key1")){
            throw new Exception(String.format("\"key1\" != %s", (String)item2));
        }

        var item3 = lst.__getitem__(3);
        if (!((String)item3).equals("val1")){
            throw new Exception(String.format("\"val1\" != %s", (String)item3));
        }
    }
}