import sys
from time import time as now

__out = sys.stdout

def setOutput(out):
	__out = out

def getOutput():
	return __out

def logString(s):
	"""Log a string."""
	__out.write('%.3f %s\n' % (now(), s))

def logException(e):
	"""Log an exception."""
	logString('%s: %s' % (e.__class__.__name__, e.message))

def logError(s):
	"""Log a string as error."""
	logString('Error: %s' % e.message)

def logWarning(s):
	"""Log a string as warning."""
	logString('Warning: %s' % e.message)
