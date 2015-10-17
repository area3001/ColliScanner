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
		self.quit = False
		Thread.__init__(self)

	def setCallback(self, callback):
		self.callback = callback

	def run(self):
		self.quit = False
		self.scan()

	def terminate(self):
		self.quit = True
		if not self.camera.closed:
			self.camera.close()
			del(self.camera)
		
	def scan(self):
		while not self.quit:
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

			if any(True for _ in image):
				self.callback(image)
				self.quit = True

		