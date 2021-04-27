import openffi.*;
fun main() {
	var strUtils = python_string_utils();
    var resTrue = strUtils.is_json("[1, 2, 3]");
    System.out.println("[1, 2, 3]? "+resTrue);
    var stripped = strUtils.strip_html("\"test: <a href=\"foo/bar\">click here</a>\"");
    System.out.println("Before: \"test: <a href=\"foo/bar\">click here</a>\"");
    System.out.println("After: "+stripped+"\n");
}