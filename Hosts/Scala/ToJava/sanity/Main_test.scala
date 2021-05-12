import openffi._;

class Main_test; object Main_test
{
	var t: Test = null;
	def main(args: Array[String])
	{
		try
		{
			t = new Test();

			testHelloWorld();
			testReturnsAnError();
			testDivIntegers();
			testJoinStrings();
		}
		catch
		{
			case e: Exception =>
				System.out.println("Unexpected exception has occurred during tests");
				e.printStackTrace();
				System.exit(1);
		}
	}

	def testHelloWorld()
	{
		t.helloWorld();
	}

	def testReturnsAnError()
	{
		try
		{
			t.returnsAnError();
			System.out.println("Test should have failed");
			System.exit(1);
		}
		catch
		{
			case e: Exception =>
				if(!e.getMessage().equals("java.lang.Exception: Returning an error"))
				{
					System.out.println("Unexpected error message.\nExpected: java.lang.Exception: Returning an error\nReceived: "+e.getMessage());
					System.exit(1);
				}
		}
	}

	def testDivIntegers()
	{
		var res = t.divIntegers(1, 2);
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
        catch
        {
            case e: Exception =>
	            if(!e.getMessage().equals("java.lang.ArithmeticException: Divisor is 0"))
	            {
	                System.out.println("Unexpected error message.\nExpected: java.lang.ArithmeticException: Divisor is 0\nReceived: "+e.getMessage());
	                System.exit(1);
	            }
        }
	}

	def testJoinStrings()
	{
		var res = t.joinStrings(Array("A","b","C"));
    	if(!res.equals("A,b,C"))
    	{
    	    System.out.println("Expected A,b,C. Got: "+res);
    	    System.exit(1);
    	}
	}
}