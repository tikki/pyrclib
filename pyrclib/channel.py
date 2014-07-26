from .events import EventEmitter

class Channel(EventEmitter):
	def __init__(self, irc, channel: str):
		super().__init__()
		self.irc = irc
		self.name = channel
		irc.addEventHandler('recv', self.__onJoin)
		# self.users = []
		self.__joined = False
	def __onJoin(self, irc, msg):
		if msg.command == '366' or msg.command == 'RPL_ENDOFNAMES': # on successful join, a server sends a list of names.
			self.__joined = True
			self.emitEvent('join', self)
	def msg(self, text: str):
		if self.__joined:
			self.irc.msg(self.name, text)
