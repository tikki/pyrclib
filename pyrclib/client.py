from irc import IRC
from time import sleep

class IRCClient(object):
	def __init__(self, nicknames = None, username = None, realname = None, servers = None, channels = None):
		super(IRCClient, self).__init__()
		# config
		self.nicknames = list(nicknames) if nicknames is not None else []
		self.username = username
		self.realname = realname
		self.servers = list(servers) if servers is not None else []
		self.channels = list(channels) if channels is not None else []
		self.loggers = []
		self.nickIndex = 0
		self.serverIndex = -1
		# state
		self.isRunning = False
		self.isConnected = False
		self.joinedChannels = []
	# accessors
	def addNicks(self, *names):
		for name in names:
			self.nicknames.append(name)
	def addServer(self, host, port):
		self.servers.append((host, port))
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
			self.nickIndex = (self.nickIndex + 1) % len(self.nicknames)
			irc.nick(self.nicknames[self.nickIndex])
			return True
	# 
	def run(self):
		irc = IRC(self.nicknames[0], self.username, self.realname)
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
			self.serverIndex = (self.serverIndex + 1) % len(self.servers)
			server, port = self.servers[self.serverIndex]
			# reset connected state
			self.isConnected = False
			try:
				irc.connect(server, port)
				irc.run() # hand over control to the irc library
			except KeyboardInterrupt:
				raise
			except Exception as err:
				print(err, 'Reconnecting in 5 seconds.')
				sleep(5)
