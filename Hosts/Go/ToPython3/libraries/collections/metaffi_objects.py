class metaffi_positional_args():
	t: tuple

	def __init__(self):
		self.t = tuple()

	def set_arg(self, val) -> None:
		self.t += (val,)


class metaffi_keyword_args(dict):
	def __init__(self):
		super().__init__()

	def set_arg(self, keyword, val) -> None:
		self[keyword] = val
