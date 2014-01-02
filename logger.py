import time

# Basic Loggers

class Logger(object):
	"""A buffered logger"""
	def __init__(self, pathOrWritable, maxBufferLines = 2**10):
		"""
		pathOrWritable: path to a file to append to or a writable file-like object (like sys.stdout)
		maxBufferLines: number of lines the buffer can hold before automatically flushing, set to 0 for immediate flushing
		"""
		super(Logger, self).__init__()
		self._out = pathOrWritable
		self._isWritable = hasattr(pathOrWritable, 'write')
		self._buf = []
		self._maxBufferLines = maxBufferLines
	def flush(self):
		fo = self._out if self._isWritable else open(self._out, 'a')
		try:
			for line in self._buf:
				fo.write(line + '\n')
			self._buf = []
		finally:
			# if we opened it, we have to close it.
			if not self._isWritable:
				fo.close()
	def log(self, s):
		"""log a string"""
		self._buf.append(s)
		# automatically flush every X lines
		if len(self._buf) > self._maxBufferLines:
			self.flush()

class AutoNamedLogger(Logger):
	"""A logger that logs to file, automatically named using the supplied basename and current date."""
	def __init__(self, basename, maxBufferLines = None):
		if maxBufferLines is None:
			super(AutoNamedLogger, self).__init__(None)
		else:
			super(AutoNamedLogger, self).__init__(None, maxBufferLines)
		self.basename = basename
	def flush(self):
		self._out = '%s-%s.txt' % (self.basename, time.strftime('%Y-%m-%d'))
		super(AutoNamedLogger, self).flush()

# IRC Loggers

class IRCLoggerBase(Logger):
	"""IRC lib compatible logger base.

	You shouldn't instantiate this class directly. Use derived classes instead."""
	def log(self, irc, msg):
		super(IRCLogger, self).log(msg.raw)
	def __call__(self, irc, msg):
		self.log(irc, msg)

class AutoFlushIRCLoggerMixin(IRCLoggerBase):
	"""A base class mixin that flushes an IRC logger every 30 seconds.
	
	You shouldn't instantiate this class directly. Use it together with another IRCLogger derived class as sub-class.
	When used with another class as sub-class, put this one first.

	Overwrite `flushTime` in your class to change the default flush time period."""
	_loggers = set()
	flushTime = 60 # this logger will automatically flush every X seconds
	@staticmethod
	def autoFlush(irc):
		for logger in AutoFlushIRCLoggerMixin._loggers:
			logger.flush()
		irc.callIn(AutoFlushIRCLoggerMixin.flushTime * 1000, AutoFlushIRCLoggerMixin.autoFlush, irc)
	def log(self, irc, msg):
		# add to auto-flush list and check if we need to start the auto-flush callback loop
		isFirstLogger = not bool(self._loggers)
		self._loggers.add(self)
		if isFirstLogger:
			self.autoFlush(irc)
		super(AutoFlushIRCLoggerMixin, self).log(irc, msg)

class RawIRCLogger(IRCLoggerBase):
	"""Log all IRC messages in their raw form with prepended unix timestamp."""
	def log(self, irc, msg):
		formattedMsg = '%.3f %s' % (time.time(), msg.raw)
		super(IRCLoggerBase, self).log(formattedMsg) # skip IRCLoggerBase.log

class PrettyIRCLogger(IRCLoggerBase):
	"""Log IRC messages in a prettified fashion.

	Logs messages, join, part, and quit."""
	@staticmethod
	def _clean(s):
		"""decode a string and remove control characters"""
		for codec in 'utf-8', 'iso-8859-15', 'shift_jis', 'latin-1':
			try:
				s = s.decode(codec)
				break
			except:
				pass
		else:
			raise Exception('Could not decode message text.')
		return ''.join(c for c in s if ord(c) >= 32)
	@staticmethod
	def _parseSender(sender):
		"""return the segments of a sender of format nick!user@host"""
		nick, user = sender.split('!', 1)
		user, host = user.split('@', 1)
		return nick, user, host
	def log(self, irc, msg):
		formattedMsg = None
		try: # message parsing should never throw
			if msg.command == 'PRIVMSG':
				nick, user, host = (self._clean(e) for e in self._parseSender(msg.prefix))
				receiver = self._clean(msg.params[0])
				text = self._clean(msg.params[1])
				formattedMsg = '<%s:%s> %s' % (nick, receiver, text)
			elif msg.command in ('JOIN', 'PART', 'QUIT'):
				nick, user, host = (self._clean(e) for e in self._parseSender(msg.prefix))
				channel = self._clean(msg.params[0])
				if msg.command == 'JOIN':
					formattedMsg = '%s (%s@%s) joined %s.' % (nick, user, host, channel)
				elif msg.command == 'PART':
					formattedMsg = '%s (%s@%s) left %s.' % (nick, user, host, channel)
				elif msg.command == 'QUIT':
					formattedMsg = '%s (%s@%s) quit. (%s)' % (nick, user, host, channel) # channel is the quit message
		except Exception as err:
			print('Message parsing error. `%s`, %s'.encode('unicode-escape') % (msg.raw, err))
		if formattedMsg:
			# add timestamp
			timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
			formattedMsg = '[%s] %s' % (timestamp, formattedMsg)
			super(IRCLoggerBase, self).log(formattedMsg.encode('unicode-escape')) # skip IRCLoggerBase.log
