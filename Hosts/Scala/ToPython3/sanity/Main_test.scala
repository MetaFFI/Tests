package sanity;

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
		t.hello_world();
	}

	def testReturnsAnError()
	{
		try
		{
			t.returns_an_error();
			System.out.println("Test should have failed");
			System.exit(1);
		}
		catch
		{
			case e: Exception =>
				if(!e.getMessage().contains("Exception: Error"))
				{
					System.out.println("Unexpected error message.\nExpected to contain: Exception: Error\nReceived: "+e.getMessage());
					System.exit(1);
				}
		}
	}

	def testDivIntegers()
	{
		var res = t.div_integers(1, 2);
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
        catch
        {
            case e: Exception =>
	            if(!e.getMessage().contains("division by zero"))
	            {
	                System.out.println("Unexpected error message.\nExpected to contain: division by zero\nReceived: "+e.getMessage());
	                System.exit(1);
	            }
        }
	}

	def testJoinStrings()
	{
		var res = t.join_strings(Array("A","b","C"));
    	if(!res.equals("A,b,C"))
    	{
    	    System.out.println("Expected A,b,C. Got: "+res);
    	    System.exit(1);
    	}
	}
}