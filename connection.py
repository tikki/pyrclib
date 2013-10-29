import socket
from select import select

class SocketConnection(object):
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.__sendbuf = ''
		self.__recvbuf = ''
		self.__socket = self._getSocket()
	def _getSocket(self):
		s = None
		for af, socktype, proto, canonname, sa in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC, socket.SOCK_STREAM):
			try:
				s = socket.socket(af, socktype, proto)
			except socket.error as msg:
				s = None
				continue
			try:
				s.connect(sa)
			except socket.error as msg:
				s.close()
				s = None
				continue
			break
		return s
	# data handling
	def send(self, data):
		if not self.isConnected():
			return False
		self.__sendbuf += data
		return True
	def receive(self, amount = None):
		ret = self.peek(amount)
		self.discard(len(ret))
		return ret
	def peek(self, amount = None):
		return self.__recvbuf if amount is None else self.__recvbuf[:amount]
	def discard(self, amount):
		if amount:
			self.__recvbuf = self.__recvbuf[amount:]
	# connection handling
	def isConnected(self):
		return self.__socket is not None
	def disconnect(self):
		if self.__socket is not None:
			self.__socket.close()
			self.__socket = None
	# upkeep
	def tick(self):
		if not self.isConnected():
			return
		# send & receive socket data
		sock = self.__socket
		sockList = [sock]
		readable, writable, error = select(sockList, sockList, [], 5)
		if sock in writable:
			sent = sock.send(self.__sendbuf)
			self.__sendbuf = self.__sendbuf[sent:]
		if sock in readable:
			chunk = sock.recv(4096)
			self.__recvbuf += chunk
