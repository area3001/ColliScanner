import sys
import time
import barcode
import display
import colruyt

if len(sys.argv) != 3:
	exit(0)

username = sys.argv[1]
password = sys.argv[2]

api = colruyt.ColruytAPI(username, password)
scanner = barcode.BarcodeScanner(800, 600)
display = display.Display()

while True:
	try:
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
				
				print "Product [%s] %s - %s" % (productId, productBrand, productDescription)

				# get product image and show on the screen
				image = api.get_product_image(productImagePath)
				if image is not None:
					display.show_product(image, productBrand, productDescription)
				
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


