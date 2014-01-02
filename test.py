from pyrclib.client import IRCClient
from pyrclib.logger import *
import sys

class AutoNamedIRCLogger(AutoFlushIRCLoggerMixin, AutoNamedLogger, RawIRCLogger):
	flushTime = 60

def main():
	# create a new client & set config
	client = IRCClient(username = 'pyrctest', realname = 'pyrctest')
	client.addNicks('pyrctest', 'pyrctest2')
	client.addChannel('#test')
	client.addServer('irc.example.com', 6667)
	# create and add loggers
	logToFile = AutoNamedIRCLogger('example', 2**7)
	logToStdout = PrettyIRCLogger(sys.stdout, 0)
	client.addLogger(logToFile)
	client.addLogger(logToStdout, send = False)
	# hand over control to the client
	client.run()

if __name__ == '__main__':
	main()
