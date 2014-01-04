"""Parser for config files.

Config file format:
Commentary lines start with #. All other non-empty lines will be interpretet.
A line can contain only a key (will be assigned a boolean value of True),
or a key and value. Key and value are separated by :.
A value can also be a list of values; values are separated by spaces or tabs.
Multiple values can also be supplied in multiple lines with the same key.

Key only entries will have a value type of bool (value: True).
All other entry types will have a value type of (possibly empty) list of strings.
"""

def dictFromLines(iterable):
	conf = {}
	for line in iterable:
		line = line.strip()
		if not line or line.startswith('#'): # skip empty lines or lines starting with #
			continue
		kv = line.split(':', 1)
		key = kv[0].strip()
		if len(kv) == 1:
			conf[key] = True
		else:
			# load & extend existing value list
			val = conf[key] if key in conf else []
			if not isinstance(val, list): val = [] # overwrite previous key only entries
			val.extend(e.strip() for e in kv[1].split() if e)
			# store value list
			conf[key] = val
	return conf

def main():
	import sys
	fn = sys.argv[1]
	with open(fn) as fo:
		print(dictFromLines(fo))

if __name__ == '__main__':
	main()
