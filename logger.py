from pyrclib.client import IRCClient
from pyrclib.logger import *
from confparser import dictFromLines as parseConf
import sys

class AutoNamedIRCLogger(AutoFlushIRCLoggerMixin, AutoNamedLogger, RawIRCLogger):
	flushTime = 60

def main():
	try:
		confname = sys.argv[1]
	except:
		print('Usage: %s path-to-config-file' % sys.argv[0])
		return
	# load config file
	with open(confname) as fo:
		conf = parseConf(fo)
	try:
		username, realname = conf['username'][0], conf['realname'][0]
		nicks, channels, servers = conf['nick'], conf['channel'], conf['server']
		useSsl = 'use ssl' in conf
		logPath = conf['log path'][0]
		isSilenced = 'silenced' in conf or 'quiet' in conf
	except KeyError as err:
		print('Missing config key: %s' % err.message)
	else:
		# create a new client & set config
		client = IRCClient(username = username, realname = realname)
		client.addNicks(*nicks)
		for channel in channels:
			if ':' in channel:
				client.addChannel(*channel.rsplit(':', 1)) # split channel string into name and password
			else:
				client.addChannel(channel)
		for server in servers:
			host, port = server.split(':')
			client.addServer(host, port, useSsl) # split server string into host and port
		# create and add loggers
		logToFile = AutoNamedIRCLogger(logPath, 2**7)
		client.addLogger(logToFile)
		if not isSilenced:
			logToStdout = PrettyIRCLogger(sys.stdout, 0)
			client.addLogger(logToStdout, send = False)
		# hand over control to the client
		client.run()

if __name__ == '__main__':
	main()
