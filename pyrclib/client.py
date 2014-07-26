from .irc import IRC
from time import sleep
import traceback

class IRCClient:
	def __init__(self, nicknames = None, username = None, realname = None, servers = None, channels = None):
		super().__init__()
		# config
		self.nicknames = list(nicknames) if nicknames is not None else []
		self.username = username
		self.realname = realname
		self.servers = list(servers) if servers is not None else []
		self.channels = list(channels) if channels is not None else []
		self.loggers = []
		# state
		self.isRunning = False
		self.isConnected = False
		self.joinedChannels = []
		self.irc = None # reference to the IRC instance
		# private state
		self.__nickIndex = 0
		self.__serverIndex = -1
	# accessors
	def addNicks(self, *names):
		for name in names:
			self.nicknames.append(name)
	def addServer(self, host, port, useSsl):
		self.servers.append((host, port, useSsl))
	def addChannel(self, name, passwd = None):
		self.channels.append((name, passwd))
	def addLogger(self, logger, send = True, recv = True):
		self.loggers.append((logger, send, recv))
	# irc msg handlers
	def successfullyConnectedHandler(self, irc, msg):
		# check if we just successfully connected (a welcome or motd message = connected)
		if not self.isConnected and msg.command in ('001', 'RPL_WELCOME', '376', 'RPL_ENDOFMOTD'):
			self.isConnected = True
			# join channels
			for channel in self.channels:
				if isinstance(channel, str):
					irc.join(channel)
				else:
					irc.join(*channel)
	def nickAlreadyInUseHandler(self, irc, msg):
		"""`nickname already in use` error handler"""
		if msg.command in ('433', 'ERR_NICKNAMEINUSE'):
			self.__nickIndex = (self.__nickIndex + 1) % len(self.nicknames)
			irc.nick(self.nicknames[self.__nickIndex])
			return True
	# 
	def run(self):
		self.irc = irc = IRC(self.nicknames[0], self.username, self.realname)
		# add own handlers first
		irc.addEventHandler('recv', self.nickAlreadyInUseHandler)
		irc.addEventHandler('recv', self.successfullyConnectedHandler)
		# add external handlers (loggers)
		for logger, send, recv in self.loggers:
			if send: irc.addEventHandler('send', logger)
			if recv: irc.addEventHandler('recv', logger)
		#
		self.isRunning = True
		while self.isRunning:
			# get next server & port
			self.__serverIndex = (self.__serverIndex + 1) % len(self.servers)
			server, port, useSsl = self.servers[self.__serverIndex]
			# reset connected state
			self.isConnected = False
			try:
				irc.connect(server, port, useSsl)
				irc.run() # hand over control to the irc library
			except KeyboardInterrupt:
				for logger, send, recv in self.loggers:
					logger.flush()
				raise
			except Exception as err:
				traceback.print_exc()
				print('Reconnecting in 5 seconds.')
				sleep(5)
