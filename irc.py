from time import sleep
from connection import SocketConnection
from events import EventEmitter
from timer import TimerManager

## irc rfc: https://tools.ietf.org/html/rfc1459

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
			return
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

class IRC(EventEmitter, TimerManager):
	def __init__(self, nick, user, real):
		super(IRC, self).__init__()
		self.__ircConnection = None
		self.__nick = nick
		self.__user = user
		self.__real = real
		self.isRunning = False
		self.addEventHandler('recv', IRC.__pingHandler)
	# 'built-in'/default handlers
	@staticmethod
	def __pingHandler(irc, msg):
		if msg.command == 'PING':
			irc.sendRaw(msg.raw.replace('PING', 'PONG'))
			return True
	# IRCConnection delegate
	def receivedMessage(self, msg):
		self.emitEvent('recv', self, msg)
	def sendRaw(self, msgString):
		self.emitEvent('send', self, msgString)
		self.__ircConnection.send(msgString)
	def connect(self, host, port):
		self.__ircConnection = IRCConnection(host, port, self)
		self.nick()
		self.sendRaw('USER %s * * :%s' % (self.__user, self.__real))
	# IRC commands
	def msg(self, receiver, text):
		self.sendRaw('PRIVMSG %s :%s' % (receiver, text))
	def join(self, channel, key = ''):
		if key:
			key = ' ' + key
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
			self.tick() # TimerManager
			con.tick()
			sleep(0.125)

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
