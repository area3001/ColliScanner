from threading import Thread

class BarcodeScanner(Thread):
	def __init__(self, callback=None, device='/dev/hidraw0'):
		self.input = open(device, 'rb')
		self.callback = callback
		self.quit = False
		Thread.__init__(self)

	def setCallback(self, callback):
		self.callback = callback

	def run(self):
		self.quit = False
		self.scan()

	def terminate(self):
		self.input.close()
		self.quit = True
		
	def scan(self):
	    try:
	        line = self.input.readline()
	    except KeyboardInterrupt:
	    	self.quit = True
	    if not line:
	    	self.quit = True
	    print line
	    self.callback(line)
	    self.quit = True


		