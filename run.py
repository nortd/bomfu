#!/usr/bin/python

import time
import thread
import subprocess
import webbrowser

PORT = 8080

def open_browser():
	time.sleep(1.0)
	webbrowser.open_new_tab('http://localhost:'+str(PORT)+'/')

thread.start_new_thread(open_browser, ())
subprocess.call("~/bin/appengine/dev_appserver.py --high_replication ./", shell=True)