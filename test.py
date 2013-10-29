from irc import IRC

def main():
	irc = IRC('pyrctest', 'pyrctest', 'pyrctest')
	def logger(irc, msg):
		print(msg)
	irc.addEventHandler('send', logger)
	irc.addEventHandler('recv', logger)
	irc.connect('irc.freenode.org', 6667)
	def sayHiAndQuit(channel):
		channel.msg('Hi!')
		channel.irc.callIn(500, channel.irc.quit, 'Bye!')
	chan = irc.join('#test')
	chan.addEventHandler('join', sayHiAndQuit)
	irc.run()

if __name__ == '__main__':
	main()
