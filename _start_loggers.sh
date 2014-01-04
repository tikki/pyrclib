#!/bin/sh
for name in network1 network2; do (
	CONF_FILE=configs/$name.conf
	PID_FILE=$name.pid
	ERROR_LOG_FILE=logs/$name-error-log.txt
	start_logger() {
		echo $name is not running. starting...
		nohup python logger.py $CONF_FILE >> $ERROR_LOG_FILE 2>&1&
		echo $! > $PID_FILE
	}
	if [ -f $CONF_FILE ]; then
		if [ ! -f $PID_FILE ]; then
			start_logger
		else
			if ! ps -p `cat $PID_FILE` > /dev/null 2>&1; then
				start_logger
			else
				echo $name is already running.
			fi
		fi
	fi
); done
