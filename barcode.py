import io
from threading import Thread
import picamera
from PIL import Image
import zbar

class BarcodeScanner(Thread):
	def __init__(self, resolutionX=800, resolutionY=600, callback=None):
		self.callback = callback
		self.scanner = zbar.ImageScanner()
		self.scanner.parse_config("enable")
		self.stream = io.BytesIO()
		self.camera = picamera.PiCamera()
		self.camera.resolution = (resolutionX, resolutionY)
		Thread.__init__(self)

	def setCallback(self, callback):
		self.callback = callback

    def run(self):
        self.scan()

    def terminate(self):
        if not self.camera.closed:
			self.camera.close()

	def scan(self):
		symbols = []
		while len(symbols) == 0:
			self.stream = io.BytesIO()
			self.camera.capture(self.stream, format="jpeg")

			# "Rewind" the stream to the beginning so we can read its content
			self.stream.seek(0)
			pil = Image.open(self.stream)
			# create a reader

			pil = pil.convert("L")
			width, height = pil.size
			raw = pil.tobytes()

			# wrap image data
			image = zbar.Image(width, height, "Y800", raw)

			# scan the image for barcodes
			self.scanner.scan(image)

			# extract results
			symbols = image

			# clean up
			del(image)

		self.callback(symbols)
