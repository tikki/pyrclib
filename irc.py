from time import sleep
from time import time as now
from connection import SocketConnection
from events import EventEmitter
from timer import TimerManager

## irc rfc: https://tools.ietf.org/html/rfc1459

class IRCConnectionError(Exception): pass

class IRCConnection(SocketConnection):
	EOL = '\r\n'
	def __init__(self, host, port, delegate):
		super(IRCConnection, self).__init__(host, port)
		self.delegate = delegate
	def send(self, msgString):
		if msgString:
			msgString += self.EOL
		return super(IRCConnection, self).send(msgString)
	def tick(self):
		if not self.isConnected():
			raise IRCConnectionError('Connection closed by remote.')
		super(IRCConnection, self).tick()
		# parse received data into messages
		buf = self.peek()
		msgsLen = buf.rfind(self.EOL)
		if msgsLen >= 0:
			self.discard(msgsLen + len(self.EOL))
			msgs = buf[:msgsLen].split(self.EOL)
			# send messages to delegate
			for msg in msgs:
				self.delegate.receivedMessage(Message(msg))

class IRCBase(EventEmitter, TimerManager):
	"""Implements the very basic IRC functionality.
	You should not instantiate this class directly. Use the IRC class instead.

	If you sub-class IRCBase and overwrite `tick` be sure to call TimerManager.tick
	or IRCBase.tick (which is the same), otherwise the timers won't work!
	"""
	def __init__(self, nick, user, real):
		super(IRCBase, self).__init__()
		self.__ircConnection = None
		self.__nick = nick
		self.__user = user
		self.__real = real
		self.isRunning = False
	# IRCConnection delegate
	def receivedMessage(self, msg):
		self.emitEvent('recv', self, msg)
	def sendRaw(self, msgString):
		self.emitEvent('send', self, Message(msgString))
		self.__ircConnection.send(msgString)
	def connect(self, host, port):
		self.__ircConnection = IRCConnection(host, port, self)
		self.nick()
		self.sendRaw('USER %s * * :%s' % (self.__user, self.__real))
	# IRC commands
	def msg(self, receiver, text):
		self.sendRaw('PRIVMSG %s :%s' % (receiver, text))
	def ping(self):
		self.sendRaw('PING %i' % now())
	def join(self, channel, key = None):
		key = ' ' + key if key else ''
		self.sendRaw('JOIN ' + channel + key)
		return Channel(self, channel)
	def nick(self, nick = None):
		if nick is None:
			nick = self.__nick
		else:
			self.__nick = nick
		self.sendRaw('NICK ' + nick)
	def quit(self, message = None):
		if message is not None:
			self.sendRaw('QUIT :' + message)
		else:
			self.sendRaw('QUIT')
		def kill():
			self.isRunning = False
			self.__ircConnection.disconnect()
		self.callIn(500, kill)
	#
	def run(self):
		self.isRunning = True
		con = self.__ircConnection
		while self.isRunning:
			self.tick()
			con.tick()
			sleep(0.125)

class IRC(IRCBase):
	"""IRC is the main pyrclib class. It adds some essential automation to the IRCBase class."""
	def __init__(self, nick, user, real):
		super(IRC, self).__init__(nick, user, real)
		self.addEventHandler('recv', IRC.__pingHandler)
		self.__dataReceivedTime = 0 # timestamp of the last time we received some data
		self.__pingSentTime = 0 # timestamp of the last time a ping was sent
	# 'built-in'/default handlers
	@staticmethod
	def __pingHandler(irc, msg):
		if msg.command == 'PING':
			irc.sendRaw(msg.raw.replace('PING', 'PONG'))
			# return True
	# IRCConnection delegate
	def receivedMessage(self, msg):
		super(IRC, self).receivedMessage(msg)
		self.__dataReceivedTime = now()
	def connect(self, host, port):
		super(IRC, self).connect(host, port)
		self.__dataReceivedTime = now()
	# IRC commands
	def ping(self):
		super(IRC, self).ping()
		self.__pingSentTime = now()
	#
	def tick(self):
		super(IRC, self).tick() # will call IRCBase.tick which is TimerManager.tick
		# check if the connection is still alive
		_now = now()
		lastReceivedDelta = _now - self.__dataReceivedTime
		if lastReceivedDelta >= 20:
			if self.__pingSentTime < self.__dataReceivedTime:
				self.ping()
			else:
				lastPingDelta = _now - self.__pingSentTime
				if lastPingDelta >= 120:
					raise IRCConnectionError('Connection timed out.')

class Message(object):
	__slots__ = 'prefix', 'command', 'params', 'raw'
	def __init__(self, msgString = None):
		self.prefix = ''
		self.command = ''
		self.params = []
		self.raw = ''
		if msgString:
			self.parse(msgString)
	def __str__(self):
		return self.raw
	def parse(self, msgString):
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
				pass
			if middle:
				params = middle.split(' ')
			if trailing is not None:
				params.append(trailing)
		# done.
		self.prefix, self.command, self.params, self.raw = prefix, command, params, raw

class Channel(EventEmitter):
	def __init__(self, irc, channel):
		super(Channel, self).__init__()
		self.irc = irc
		self.name = channel
		irc.addEventHandler('recv', self.__onJoin)
		# self.users = []
		self.__joined = False
	def __onJoin(self, irc, msg):
		if msg.command == '366' or msg.command == 'RPL_ENDOFNAMES': # on successful join, a server sends a list of names.
			self.__joined = True
			self.emitEvent('join', self)
	def msg(self, text):
		if self.__joined:
			self.irc.msg(self.name, text)
