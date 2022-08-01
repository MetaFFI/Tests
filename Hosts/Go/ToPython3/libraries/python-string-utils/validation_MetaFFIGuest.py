
# Code generated by MetaFFI. Modify only in marked places.
# Guest code for validation.py

import traceback
import sys
import platform
import os
from typing import Any
from ctypes import *


import validation


"""
xllrHandle = None
def load_xllr():
	global xllrHandle
	
	if xllrHandle == None:
		xllrHandle = cdll.LoadLibrary(get_filename_to_load('xllr'))
"""

python_plugin_handle = None
def load_python_plugin():
	global python_plugin_handle
	
	if python_plugin_handle == None:
		python_plugin_handle = cdll.LoadLibrary(get_filename_to_load('xllr.python3'))

def get_filename_to_load(fname):
	osname = platform.system()
	if osname == 'Windows':
		return os.getenv('METAFFI_HOME')+'\\'+ fname + '.dll'
	elif osname == 'Darwin':
		return os.getenv('METAFFI_HOME')+'/' + fname + '.dylib'
	else:
		return os.getenv('METAFFI_HOME')+'/' + fname + '.so' # for everything that is not windows or mac, return .so





def EntryPoint_GetAny():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.Any)



def EntryPoint_SetAny(val):
	ret_val_types = ()
	validation.Any = val
	return (None, ret_val_types)




def EntryPoint_GetCAMEL_CASE_REPLACE_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.CAMEL_CASE_REPLACE_RE)



def EntryPoint_SetCAMEL_CASE_REPLACE_RE(val):
	ret_val_types = ()
	validation.CAMEL_CASE_REPLACE_RE = val
	return (None, ret_val_types)




def EntryPoint_GetCAMEL_CASE_TEST_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.CAMEL_CASE_TEST_RE)



def EntryPoint_SetCAMEL_CASE_TEST_RE(val):
	ret_val_types = ()
	validation.CAMEL_CASE_TEST_RE = val
	return (None, ret_val_types)




def EntryPoint_GetCREDIT_CARDS():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.CREDIT_CARDS)



def EntryPoint_SetCREDIT_CARDS(val):
	ret_val_types = ()
	validation.CREDIT_CARDS = val
	return (None, ret_val_types)




def EntryPoint_GetEMAILS_RAW_STRING():
	ret_val_types = (4096,)
	return (None, ret_val_types, validation.EMAILS_RAW_STRING)



def EntryPoint_SetEMAILS_RAW_STRING(val):
	ret_val_types = ()
	validation.EMAILS_RAW_STRING = val
	return (None, ret_val_types)




def EntryPoint_GetEMAILS_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.EMAILS_RE)



def EntryPoint_SetEMAILS_RE(val):
	ret_val_types = ()
	validation.EMAILS_RE = val
	return (None, ret_val_types)




def EntryPoint_GetEMAIL_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.EMAIL_RE)



def EntryPoint_SetEMAIL_RE(val):
	ret_val_types = ()
	validation.EMAIL_RE = val
	return (None, ret_val_types)




def EntryPoint_GetESCAPED_AT_SIGN():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.ESCAPED_AT_SIGN)



def EntryPoint_SetESCAPED_AT_SIGN(val):
	ret_val_types = ()
	validation.ESCAPED_AT_SIGN = val
	return (None, ret_val_types)




def EntryPoint_GetHTML_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.HTML_RE)



def EntryPoint_SetHTML_RE(val):
	ret_val_types = ()
	validation.HTML_RE = val
	return (None, ret_val_types)




def EntryPoint_GetHTML_TAG_ONLY_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.HTML_TAG_ONLY_RE)



def EntryPoint_SetHTML_TAG_ONLY_RE(val):
	ret_val_types = ()
	validation.HTML_TAG_ONLY_RE = val
	return (None, ret_val_types)




def EntryPoint_GetINSENSITIVE_LOCALE_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.INSENSITIVE_LOCALE_RE)



def EntryPoint_SetINSENSITIVE_LOCALE_RE(val):
	ret_val_types = ()
	validation.INSENSITIVE_LOCALE_RE = val
	return (None, ret_val_types)




def EntryPoint_GetIP_V6_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.IP_V6_RE)



def EntryPoint_SetIP_V6_RE(val):
	ret_val_types = ()
	validation.IP_V6_RE = val
	return (None, ret_val_types)




def EntryPoint_GetJSON_WRAPPER_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.JSON_WRAPPER_RE)



def EntryPoint_SetJSON_WRAPPER_RE(val):
	ret_val_types = ()
	validation.JSON_WRAPPER_RE = val
	return (None, ret_val_types)




def EntryPoint_GetLOCALE_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.LOCALE_RE)



def EntryPoint_SetLOCALE_RE(val):
	ret_val_types = ()
	validation.LOCALE_RE = val
	return (None, ret_val_types)




def EntryPoint_GetList():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.List)



def EntryPoint_SetList(val):
	ret_val_types = ()
	validation.List = val
	return (None, ret_val_types)




def EntryPoint_GetMARGIN_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.MARGIN_RE)



def EntryPoint_SetMARGIN_RE(val):
	ret_val_types = ()
	validation.MARGIN_RE = val
	return (None, ret_val_types)




def EntryPoint_GetNO_LETTERS_OR_NUMBERS_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.NO_LETTERS_OR_NUMBERS_RE)



def EntryPoint_SetNO_LETTERS_OR_NUMBERS_RE(val):
	ret_val_types = ()
	validation.NO_LETTERS_OR_NUMBERS_RE = val
	return (None, ret_val_types)




def EntryPoint_GetNUMBER_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.NUMBER_RE)



def EntryPoint_SetNUMBER_RE(val):
	ret_val_types = ()
	validation.NUMBER_RE = val
	return (None, ret_val_types)




def EntryPoint_GetOptional():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.Optional)



def EntryPoint_SetOptional(val):
	ret_val_types = ()
	validation.Optional = val
	return (None, ret_val_types)




def EntryPoint_GetPRETTIFY_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.PRETTIFY_RE)



def EntryPoint_SetPRETTIFY_RE(val):
	ret_val_types = ()
	validation.PRETTIFY_RE = val
	return (None, ret_val_types)




def EntryPoint_GetSHALLOW_IP_V4_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.SHALLOW_IP_V4_RE)



def EntryPoint_SetSHALLOW_IP_V4_RE(val):
	ret_val_types = ()
	validation.SHALLOW_IP_V4_RE = val
	return (None, ret_val_types)




def EntryPoint_GetSNAKE_CASE_REPLACE_DASH_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.SNAKE_CASE_REPLACE_DASH_RE)



def EntryPoint_SetSNAKE_CASE_REPLACE_DASH_RE(val):
	ret_val_types = ()
	validation.SNAKE_CASE_REPLACE_DASH_RE = val
	return (None, ret_val_types)




def EntryPoint_GetSNAKE_CASE_REPLACE_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.SNAKE_CASE_REPLACE_RE)



def EntryPoint_SetSNAKE_CASE_REPLACE_RE(val):
	ret_val_types = ()
	validation.SNAKE_CASE_REPLACE_RE = val
	return (None, ret_val_types)




def EntryPoint_GetSNAKE_CASE_TEST_DASH_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.SNAKE_CASE_TEST_DASH_RE)



def EntryPoint_SetSNAKE_CASE_TEST_DASH_RE(val):
	ret_val_types = ()
	validation.SNAKE_CASE_TEST_DASH_RE = val
	return (None, ret_val_types)




def EntryPoint_GetSNAKE_CASE_TEST_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.SNAKE_CASE_TEST_RE)



def EntryPoint_SetSNAKE_CASE_TEST_RE(val):
	ret_val_types = ()
	validation.SNAKE_CASE_TEST_RE = val
	return (None, ret_val_types)




def EntryPoint_GetSPACES_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.SPACES_RE)



def EntryPoint_SetSPACES_RE(val):
	ret_val_types = ()
	validation.SPACES_RE = val
	return (None, ret_val_types)




def EntryPoint_GetURLS_RAW_STRING():
	ret_val_types = (4096,)
	return (None, ret_val_types, validation.URLS_RAW_STRING)



def EntryPoint_SetURLS_RAW_STRING(val):
	ret_val_types = ()
	validation.URLS_RAW_STRING = val
	return (None, ret_val_types)




def EntryPoint_GetURLS_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.URLS_RE)



def EntryPoint_SetURLS_RE(val):
	ret_val_types = ()
	validation.URLS_RE = val
	return (None, ret_val_types)




def EntryPoint_GetURL_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.URL_RE)



def EntryPoint_SetURL_RE(val):
	ret_val_types = ()
	validation.URL_RE = val
	return (None, ret_val_types)




def EntryPoint_GetUUID_HEX_OK_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.UUID_HEX_OK_RE)



def EntryPoint_SetUUID_HEX_OK_RE(val):
	ret_val_types = ()
	validation.UUID_HEX_OK_RE = val
	return (None, ret_val_types)




def EntryPoint_GetUUID_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.UUID_RE)



def EntryPoint_SetUUID_RE(val):
	ret_val_types = ()
	validation.UUID_RE = val
	return (None, ret_val_types)




def EntryPoint_GetWORDS_COUNT_RE():
	ret_val_types = (32768,)
	return (None, ret_val_types, validation.WORDS_COUNT_RE)



def EntryPoint_SetWORDS_COUNT_RE(val):
	ret_val_types = ()
	validation.WORDS_COUNT_RE = val
	return (None, ret_val_types)






# Call to foreign contains_html
def EntryPoint_contains_html(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.contains_html(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_camel_case
def EntryPoint_is_camel_case(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_camel_case(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_credit_card
def EntryPoint_is_credit_card(input_string,card_type):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_credit_card(input_string,card_type)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_decimal
def EntryPoint_is_decimal(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_decimal(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_email
def EntryPoint_is_email(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_email(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_full_string
def EntryPoint_is_full_string(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_full_string(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_integer
def EntryPoint_is_integer(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_integer(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_ip
def EntryPoint_is_ip(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_ip(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_ip_v4
def EntryPoint_is_ip_v4(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_ip_v4(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_ip_v6
def EntryPoint_is_ip_v6(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_ip_v6(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_isbn
def EntryPoint_is_isbn(input_string,normalize):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_isbn(input_string,normalize)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_isbn_10
def EntryPoint_is_isbn_10(input_string,normalize):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_isbn_10(input_string,normalize)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_isbn_13
def EntryPoint_is_isbn_13(input_string,normalize):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_isbn_13(input_string,normalize)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_isogram
def EntryPoint_is_isogram(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_isogram(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_json
def EntryPoint_is_json(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_json(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_number
def EntryPoint_is_number(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_number(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_palindrome
def EntryPoint_is_palindrome(input_string,ignore_spaces,ignore_case):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_palindrome(input_string,ignore_spaces,ignore_case)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_pangram
def EntryPoint_is_pangram(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_pangram(input_string)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_slug
def EntryPoint_is_slug(input_string,separator):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_slug(input_string,separator)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_snake_case
def EntryPoint_is_snake_case(input_string,separator):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_snake_case(input_string,separator)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_string
def EntryPoint_is_string(obj):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_string(obj)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_url
def EntryPoint_is_url(input_string,allowed_schemes):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_url(input_string,allowed_schemes)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign is_uuid
def EntryPoint_is_uuid(input_string,allow_hex):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.is_uuid(input_string,allow_hex)
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)


# Call to foreign words_count
def EntryPoint_words_count(input_string):
	#global xllrHandle

	#load_xllr()

	try:
		# call function
		ret_0 = validation.words_count(input_string)
		
		ret_val_types = (32,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)





def EntryPoint_InvalidInputError_InvalidInputError(input_data):
	try:
		# call constructor
		ret_0 = validation.InvalidInputError(input_data)
		
		
		ret_val_types = (32768,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)







def EntryPoint_InvalidInputError_ReleaseInvalidInputError(this_instance):
	try:
		# xcall release object
		
		python_plugin_handle.release_object(this_instance)
	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)




def EntryPoint___ISBNChecker___ISBNChecker(input_string,normalize):
	try:
		# call constructor
		ret_0 = validation.__ISBNChecker(input_string,normalize)
		
		
		ret_val_types = (32768,)

		return ( None, ret_val_types , ret_0)

	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)





def EntryPoint___ISBNChecker_is_isbn_10(this_instance):
	try:
		# call method
		ret_0 = this_instance.is_isbn_10()
		
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)
		
	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)
	

def EntryPoint___ISBNChecker_is_isbn_13(this_instance):
	try:
		# call method
		ret_0 = this_instance.is_isbn_13()
		
		
		ret_val_types = (1024,)

		return ( None, ret_val_types , ret_0)
		
	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)
	



def EntryPoint___ISBNChecker_Release__ISBNChecker(this_instance):
	try:
		# xcall release object
		
		python_plugin_handle.release_object(this_instance)
	except Exception as e:
		errdata = traceback.format_exception(*sys.exc_info())
		return ('\n'.join(errdata),)





