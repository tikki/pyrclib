
class EventEmitter:
	__slots__ = '__handlers'
	def __init__(self):
		super().__init__()
		self.__handlers = {}
	def addEventHandler(self, name: str, func: callable):
		if name not in self.__handlers:
			self.__handlers[name] = []
		self.__handlers[name].append(func)
	def emitEvent(self, name: str, *args, **kwargs):
		if name not in self.__handlers:
			return
		for handler in self.__handlers[name]:
			if handler(*args, **kwargs) is True:
				break
