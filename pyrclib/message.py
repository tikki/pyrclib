import datetime

def _decode(s: bytes, codecs = ('utf-8', 'iso-8859-15', 'shift_jis', 'latin-1')):
	"""Try a bunch of codecs to decode the given string.

	Raise UnicodeError if unsuccessful."""
	for codec in codecs:
		try:
			return s.decode(codec)
		except UnicodeError:
			pass
	raise UnicodeError('Could not decode message text.')

class MessageBase:
	"""A basic RFC compliant IRC message parser."""
	__slots__ = 'prefix', 'command', 'params', 'raw'
	def __init__(self, msgString: 'str or bytes' = None):
		self.prefix = ''
		self.command = ''
		self.params = []
		self.raw = ''
		if msgString:
			self.parse(msgString)
	def __str__(self):
		return self.raw
	def parse(self, msgString: 'str or bytes'):
		"""Parse msgString into prefix, command, and params.

		Raise UnicodeError if msgString cannot be decoded.
		"""
		if isinstance(msgString, bytes):
			msgString = _decode(msgString)
		prefix, command, params, raw = '', '', [], msgString
		# check for prefix
		if msgString.startswith(':'):
			try:
				prefix, msgString = msgString.split(' ', 1)
			except ValueError as error:
				prefix, msgString = msgString, ''
			prefix = prefix[1:] # remove leading ':'
		# extract command
		try:
			command, msgString = msgString.split(' ', 1)
		except ValueError:
			command, msgString = msgString, ''
		# parse params
		if msgString.startswith(':'): # only one parameter (the trailing one)
			params = [msgString[1:]]
		else:
			middle, trailing = None, None
			try:
				middle, trailing = msgString.split(' :', 1)
			except ValueError:
				middle = msgString
			if middle:
				params = middle.split(' ')
			if trailing is not None:
				params.append(trailing)
		# done.
		self.prefix, self.command, self.params, self.raw = prefix, command, params, raw
