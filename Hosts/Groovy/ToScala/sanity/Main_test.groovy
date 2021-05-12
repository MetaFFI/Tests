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
		t.helloWorld();
	}

	private static void testReturnsAnError() throws Exception
	{
		try
		{
			t.returnsAnError();
			System.out.println("Test should have failed");
			System.exit(1);
		}
		catch(Exception e)
		{
			if(!e.getMessage().equals("java.lang.Exception: Returning an error"))
			{
				System.out.println("Unexpected error message.\nExpected: java.lang.Exception: Returning an error\nReceived: "+e.getMessage());
				System.exit(1);
			}
		}
	}

	private static void testDivIntegers() throws Exception
	{
		float res = t.divIntegers(1, 2);
        if(res != 0.5)
        {
            System.out.println("Expected 0.5, got: "+res);
            System.exit(1);
        }

        try
        {
            t.divIntegers(1, 0);
            System.out.println("Expected an error - divisor is 0");
            System.exit(1);
        }
        catch(Exception e)
        {
            if(!e.getMessage().equals("java.lang.ArithmeticException: Divisor is 0"))
            {
                System.out.println("Unexpected error message.\nExpected: java.lang.ArithmeticException: Divisor is 0\nReceived: "+e.getMessage());
                System.exit(1);
            }
        }
	}

	private static void testJoinStrings() throws Exception
	{
		String res = t.joinStrings(new String[]{"A","b","C"});
    	if(!res.equals("A,b,C"))
    	{
    	    System.out.println("Expected A,b,C. Got: "+res);
    	    System.exit(1);
    	}
	}
}