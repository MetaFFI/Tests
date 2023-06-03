import builtins


class extended_test:
	def __init__(self):
		self._x = 0

	@property
	def x(self) -> int:
		return self._x

	@x.setter
	def x(self, val1: int):
		self._x = val1

	def positional_or_named(self, value: str) -> str:
		print(value)
		return value

	def positional_or_named_multi_type_hint(self, value: str, value2: str | None = None) -> str:
		if value2 is not None:
			print(value + " " + value2)
			return value + " " + value2
		else:
			print(value)
			return value

	def list_args(self, value='default', *args) -> list:
		print(value)
		res = [value]
		for a in args:
			print(a)
			res.append(a)
		return res

	def dict_args(self, value='default', **named_args) -> list[str]:
		res = [value]
		print(value)
		for k, v in named_args.items():
			res.append(k)
			res.append(v)
			print('{}={}'.format(k, v))
		return res

	def named_only(self, *, named: str) -> str:
		print(named)
		return named

	def positional_only(self, v1: str, v2: str = 'default', /) -> str:
		print(v1 + ' ' + v2)
		return v1 + ' ' + v2

	def arg_positional_arg_named(self, value: str = 'default', *args, **named_args) -> list[str]:

		res = [value]
		print(value)

		for a in args:
			print(a)
			res.append(a)

		for k, v in named_args.items():
			print('{}={}'.format(k, v))
			res.append(k)
			res.append(v)
		return res


def create_extended_test_instance() -> extended_test:
	return extended_test()


if '__main__' == __name__:
	from inspect import *

	for f in getmembers(extended_test):
		if isfunction(f[1]):
			print('function {} :'.format(f[0]))
			sig = signature(f[1])
			for name, data in sig.parameters.items():
				print('\t{} - {}'.format(name, data.kind))
		elif isinstance(f[1], builtins.property):
			print('property {} get:'.format(f[0]))

			if f[1].fget is not None:
				sig = signature(f[1].fget)
				for name, data in sig.parameters.items():
					print('\t{} - {}'.format(name, data.kind))

			if f[1].fset is not None:
				print('property {} set:'.format(f[0]))
				sig = signature(f[1].fset)
				for name, data in sig.parameters.items():
					print('\t{} - {}'.format(name, data.kind.name))
		else:
			print('other: {}'.format(f[1]))
