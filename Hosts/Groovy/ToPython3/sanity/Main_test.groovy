package sanity;

import openffi.*;

public class Main_test
{
	private static Test t = null;
	public static void main(String[] args)
	{
		try
		{
			t = new Test();

			testHelloWorld();
			testReturnsAnError();
			testDivIntegers();
			testJoinStrings();
		}
		catch(Exception e)
		{
			System.out.println("Unexpected exception has occurred during tests");
			e.printStackTrace();
			System.exit(1);
		}
	}

	private static void testHelloWorld() throws Exception
	{
		t.hello_world();
	}

	private static void testReturnsAnError() throws Exception
	{
		try
		{
			t.returns_an_error();
			System.out.println("Test should have failed");
			System.exit(1);
		}
		catch(Exception e)
		{
			if(!e.getMessage().contains("Exception: Error"))
			{
				System.out.println("Unexpected error message.\nExpected to contain: Exception: Error\nReceived: "+e.getMessage());
				System.exit(1);
			}
		}
	}

	private static void testDivIntegers() throws Exception
	{
		float res = t.div_integers(1, 2);
        if(res != 0.5)
        {
            System.out.println("Expected 0.5, got: "+res);
            System.exit(1);
        }

        try
        {
            t.div_integers(1, 0);
            System.out.println("Expected an error - divisor is 0");
            System.exit(1);
        }
        catch(Exception e)
        {
            if(!e.getMessage().contains("division by zero"))
            {
                System.out.println("Unexpected error message.\nExpected to contain: division by zero\nReceived: "+e.getMessage());
                System.exit(1);
            }
        }
	}

	private static void testJoinStrings() throws Exception
	{
		String res = t.join_strings(new String[]{"A","b","C"});
    	if(!res.equals("A, b, C"))
    	{
    	    System.out.println("Expected A,b,C. Got: "+res);
    	    System.exit(1);
    	}
	}
}