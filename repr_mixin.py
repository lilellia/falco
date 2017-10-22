class ReprMixin:
	def __repr__(self):
		variables = ', '.join(f'{k}={v}' for k, v in vars(self).items())
		return f'{self.__class__.__name__}({variables})'
