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
		barcode = ''

		continue_looping = True

		while continue_looping:
		    report = self.input.read(8)
		    for i in report:
		        j = ord(i)
		        if j == 0:
		            continue

		        if j == 0x1E:
		            barcode += '1'
		            continue
		        elif j == 0x1F:
		            barcode += '2'
		            continue
		        elif j == 0x20:
		            barcode += '3'
		            continue
		        elif j == 0x21:
		            barcode += '4'
		            continue
		        elif j == 0x22:
		            barcode += '5'
		            continue
		        elif j == 0x23:
		            barcode += '6'
		            continue
		        elif j == 0x24:
		            barcode += '7'
		            continue
		        elif j == 0x25:
		            barcode += '8'
		            continue
		        elif j == 0x26:
		            barcode += '9'
		            continue
		        elif j == 0x27:
		            barcode += '0'
		            continue
		        elif j == 0x28:
		            continue_looping = False
		            break
		        else:
		            pass
		self.callback(barcode)
		self.quit = True
			