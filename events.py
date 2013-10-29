
class EventEmitter(object):
	__slots__ = '__handlers'
	def __init__(self):
		super(EventEmitter, self).__init__()
		self.__handlers = {}
	def addEventHandler(self, name, func):
		if name not in self.__handlers:
			self.__handlers[name] = []
		self.__handlers[name].append(func)
	def emitEvent(self, name, *args, **kwargs):
		if name not in self.__handlers:
			return
		for handler in self.__handlers[name]:
			if handler(*args, **kwargs) is True:
				break
