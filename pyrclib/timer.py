import time

class TimerManager(object):
	def __init__(self):
		super(TimerManager, self).__init__()
		self.__timers = []
		self.__lastCalled = None
	@staticmethod
	def __now():
		return int(time.time() * 1000)
	def callIn(self, ms, func, *args, **kwargs):
		self.__timers.append((self.__now() + ms, func, args, kwargs))
		self.__timers.sort()
	def tick(self):
		# filter active timers
		now = self.__now()
		active = []
		timers = self.__timers
		for timer in timers:
			if timer[0] <= now:
				active.append(timer[1:])
			else:
				break
		self.__timers = timers[len(active):]
		# call active timer callbacks
		for func, args, kwargs in active:
			func(*args, **kwargs)
