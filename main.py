import sys
import time
import barcode
import colruyt

if len(sys.argv) != 3:
	exit(0)

username = sys.argv[1]
password = sys.argv[2]

api = colruyt.ColruytAPI()
scanner = barcode.BarcodeScanner()
api.login(username, password)

while True:
	try:
		image = scanner.scan()
		for symbol in image:
			print 'decoded', symbol.type, 'symbol', '"%s"' % symbol.data
			try:
				response = api.search(symbol.data)

				print "zoeken van product met barcode %s: %s" % (symbol.data, response['status']['meaning'])

				productId = response['data']['searchResults'][0]['list'][0]['id']
				productBrand = response['data']['searchResults'][0]['list'][0]['brand']
				productDescription = response['data']['searchResults'][0]['list'][0]['description']
				productImagePath = response['data']['searchResults'][0]['list'][0]['overviewImage']
				
				#image = api.get_product_image(productImagePath)

				print 'Product [%s] %s - %s' % (productId, productBrand, productDescription)


				response = api.add(productId, 1, 'S')
				print "toevoegen aan de winkelmand: %s" % (response['status']['meaning'])

				time.sleep(3)
			except ValueError:
				print 'something went wrong'
				break
	except (KeyboardInterrupt, SystemExit):
		print "catched keyboardinterrupt"
		break

scanner.stop()
api.logout()

del(scanner)
del(api)


