package python_string_utils;

import metaffi_host.*;

public class Main_test
{
	public static void main(String[] args) throws metaffi.MetaFFIException
	{
		metaffi_host.string_utils.load("string_utils_MetaFFIGuest");
		//defer metaffi_host.validation.free();
		var pyval = new metaffi_host.string_utils();
        boolean resTrue = pyval.is_json("[1, 2, 3]");
        System.out.println("[1, 2, 3]? "+resTrue);

        String stripped = pyval.strip_html("\"test: <a href=\"foo/bar\">click here</a>\"", true);
        System.out.println("Before: \"test: <a href=\"foo/bar\">click here</a>\"");
        System.out.println("After: "+stripped+"\n");


	}
}