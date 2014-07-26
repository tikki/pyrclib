from time import sleep
from time import time as now
from .connection import SocketConnection
from .events import EventEmitter
from .timer import TimerManager
from .channel import Channel
from .message import MessageBase as Message
from .log import logException

## irc rfc: https://tools.ietf.org/html/rfc1459

class IRCConnectionError(Exception): pass

class IRCConnection(SocketConnection):
	EOL = b'\r\n'
	def __init__(self, host: str, port: int, delegate, useSsl: bool):
		super().__init__(host, port, useSsl)
		self.delegate = delegate
	def send(self, msgString: str):
		msgData = msgString.encode('utf-8')
		if msgData:
			msgData += self.EOL
		return super().send(msgData)
	def tick(self):
		if not self.isConnected():
			raise IRCConnectionError('Connection closed by remote.')
		super().tick()
		# parse received data into messages
		buf = self.peek()
		msgsLen = buf.rfind(self.EOL)
		if msgsLen >= 0:
			self.discard(msgsLen + len(self.EOL))
			msgs = buf[:msgsLen].split(self.EOL)
			# send messages to delegate
			for msgData in msgs:
				try:
					msg = Message(msgData)
				except Exception as e:
					logException(e)
				else:
					self.delegate.receivedMessage(msg)

class IRCBase(EventEmitter, TimerManager):
	"""Implements the very basic IRC functionality.
	You should not instantiate this class directly. Use the IRC class instead.

	If you sub-class IRCBase and overwrite `tick` be sure to call TimerManager.tick
	or IRCBase.tick (which is the same), otherwise the timers won't work!
	"""
	def __init__(self, nick: str, user: str, real: str):
		super().__init__()
		self.__ircConnection = None
		self.__nick = nick
		self.__user = user
		self.__real = real
		self.isRunning = False
	# IRCConnection delegate
	def receivedMessage(self, msg: Message):
		self.emitEvent('recv', self, msg)
	def sendRaw(self, msgString: str):
		self.emitEvent('send', self, Message(msgString))
		self.__ircConnection.send(msgString)
	def connect(self, host: str, port: int, useSsl: bool):
		self.__ircConnection = IRCConnection(host, port, self, useSsl)
		self.nick()
		self.sendRaw('USER %s * * :%s' % (self.__user, self.__real))
	# IRC commands
	def msg(self, receiver: str, text: str):
		self.sendRaw('PRIVMSG %s :%s' % (receiver, text))
	def ping(self):
		self.sendRaw('PING %i' % now())
	def join(self, channel: str, key: str = None) -> Channel:
		key = ' ' + key if key else ''
		self.sendRaw('JOIN ' + channel + key)
		return Channel(self, channel)
	def nick(self, nick: str = None):
		if nick is None:
			nick = self.__nick
		else:
			self.__nick = nick
		self.sendRaw('NICK ' + nick)
	def quit(self, message: str = None):
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
	def __init__(self, nick: str, user: str, real: str):
		super().__init__(nick, user, real)
		self.addEventHandler('recv', IRC.__pingHandler)
		self.__dataReceivedTime = 0 # timestamp of the last time we received some data
		self.__pingSentTime = 0 # timestamp of the last time a ping was sent
	# 'built-in'/default handlers
	@staticmethod
	def __pingHandler(irc, msg: Message):
		if msg.command == 'PING':
			irc.sendRaw(msg.raw.replace('PING', 'PONG'))
			# return True
	# IRCConnection delegate
	def receivedMessage(self, msg: Message):
		super().receivedMessage(msg)
		self.__dataReceivedTime = now()
	def connect(self, host: str, port: int, useSsl: bool):
		super().connect(host, port, useSsl)
		self.__dataReceivedTime = now()
	# IRC commands
	def ping(self):
		super().ping()
		self.__pingSentTime = now()
	#
	def tick(self):
		super().tick() # will call IRCBase.tick which is TimerManager.tick
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
