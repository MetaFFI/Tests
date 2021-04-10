package sanity;

class TestFuncs{
	companion object{

		@JvmStatic
		fun helloWorld() {
			println("Hello World - From Java");
		}

		@JvmStatic
		fun returnsAnError() {
			throw Exception("Returning an error");
		}

		@JvmStatic
		fun divIntegers(x: Int, y: Int): Float {
			if(y == 0)
				throw ArithmeticException("Divisor is 0");

			return x.toFloat().div(y.toFloat());
		}

		@JvmStatic
		fun joinStrings(arr: Array<String>): String{
			return arr.joinToString(",")
		}
	}
}