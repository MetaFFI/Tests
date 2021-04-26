package sanity;

class TestFuncs; object TestFuncs{
	def helloWorld() = {
		System.out.println("Hello World - From Scala");
	}

	def returnsAnError() = {
		throw new Exception("Returning an error");
	}

	def divIntegers(x: Int, y: Int): Float = {
		if(y == 0)
			throw new ArithmeticException("Divisor is 0");

		return x.toFloat / y.toFloat;
	}

	def joinStrings(arr: Array[String]): String = {
		return arr.mkString(",")
	}
}