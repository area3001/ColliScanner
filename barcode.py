import io
from threading import Thread
import sys

class BarcodeScanner(Thread):
	def __init__(self, callback=None):
		self.callback = callback
		self.quit = False
		Thread.__init__(self)

	def setCallback(self, callback):
		self.callback = callback

	def run(self):
		self.quit = False
		self.scan()

	def terminate(self):
		self.quit = True
		
	def scan(self):
	    try:
	        line = sys.stdin.readline()
	    except KeyboardInterrupt:
	    	self.quit = True
	    if not line:
	    	self.quit = True

	    self.callback(line)
	    self.quit = True


		