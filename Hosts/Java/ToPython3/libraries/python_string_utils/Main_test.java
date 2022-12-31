package python_string_utils;

import metaffi_host.*;

public class Main_test
{
	public static void main(String[] args) throws metaffi.MetaFFIException
	{
		metaffi_host.validation.load("validation_MetaFFIGuest");
		metaffi_host.manipulation.load("manipulation_MetaFFIGuest");

		var pyval = new metaffi_host.validation();
        boolean resTrue = pyval.is_json("[1, 2, 3]");
        System.out.println("[1, 2, 3]? "+resTrue);

        var pyman = new metaffi_host.manipulation();
        String stripped = pyman.strip_html("\"test: <a href=\"foo/bar\">click here</a>\"", true);
        System.out.println("Before: \"test: <a href=\"foo/bar\">click here</a>\"");
        System.out.println("After: "+stripped+"\n");
	}
}