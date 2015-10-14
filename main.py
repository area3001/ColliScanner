import sys
import time
import barcode
import display
import colruyt
import socket
import fcntl
import struct

def get_ip_address(ifname):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	return socket.inet_ntoa(fcntl.ioctl(
		s.fileno(),
		0x8915,  # SIOCGIFADDR
		struct.pack('256s', ifname[:15])
	)[20:24])


if len(sys.argv) != 3:
	exit(0)

username = sys.argv[1]
password = sys.argv[2]

api = colruyt.ColruytAPI(username, password)
scanner = barcode.BarcodeScanner(800, 600)
display = display.Display()

ip = get_ip_address("eth0")

while True:
	try:
		display.show_message("your ip is %s" % (ip))
		# scan for a barcode
		image = scanner.scan()
		for symbol in image:
			# barcodes found
			print "decoded %s symbol, %s" % (symbol.type, symbol.data)
			try:
				# look up the product using its barcode
				response = api.search(symbol.data)

				print "Looking up product with %s barcode %s: %s" % (symbol.type, symbol.data, response["status"]["meaning"])

				productId = response["data"]["searchResults"][0]["list"][0]["id"]
				productBrand = response["data"]["searchResults"][0]["list"][0]["brand"]
				productDescription = response["data"]["searchResults"][0]["list"][0]["description"]
				productImagePath = response["data"]["searchResults"][0]["list"][0]["overviewImage"]
				price = response["data"]["searchResults"][0]["list"][0]["price"]

				print "Product [%s] %s - %s : %s euro" % (productId, productBrand, productDescription, price)

				# get product image and show on the screen
				image = api.get_product_image(productImagePath)
				if image is not None:
					display.show_product(image, productBrand, productDescription, price)
				
				# add product to cart
				response = api.add(productId, 1, "S")
				print "Adding product to shopping cart: %s" % (response["status"]["meaning"])

				# wait some time
				time.sleep(3)
			except ValueError as e:
				print "something went wrong: %s" % (e)
	except (KeyboardInterrupt, SystemExit):
		print "catched keyboardinterrupt"
		break

display.close()
scanner.stop()
api.logout()
del(scanner)
del(api)


