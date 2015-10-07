import io
import picamera
from PIL import Image
import zbar

class BarcodeScanner:
	def __init__(self):
		self.scanner = zbar.ImageScanner()
		self.scanner.parse_config('enable')
		self.stream = io.BytesIO()
		self.camera = picamera.PiCamera()
		self.camera.resolution = (800, 600)

	def scan(self):
		self.stream = io.BytesIO()
		self.camera.capture(self.stream, format='jpeg')
		# "Rewind" the stream to the beginning so we can read its content
		self.stream.seek(0)
		pil = Image.open(self.stream)
		# create a reader

		pil = pil.convert('L')
		width, height = pil.size
		raw = pil.tobytes()

		# wrap image data
		image = zbar.Image(width, height, 'Y800', raw)

		# scan the image for barcodes
		self.scanner.scan(image)

		# extract results
		symbols = image
				# clean up
		del(image)

		return symbols
	def stop(self):
		del(self.camera)
		del(self.stream)
		del(self.scanner)
