package python_string_utils;

import openffi.*;
public class Main_test
{
	public static void main(String[] args)
	{
		try
		{
			python_string_utils pyStringUtils = new python_string_utils();
            boolean resTrue = pyStringUtils.is_json("[1, 2, 3]");
            System.out.println("[1, 2, 3]? "+resTrue);
            String stripped = pyStringUtils.strip_html("\"test: <a href=\"foo/bar\">click here</a>\"");
            System.out.println("Before: \"test: <a href=\"foo/bar\">click here</a>\"");
            System.out.println("After: "+stripped+"\n");
		}
		catch(OpenFFIException e){e.printStackTrace();}
		catch(Exception e){e.printStackTrace();}
	}
}