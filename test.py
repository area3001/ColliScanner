import sys
import time
import colruyt
import display
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
display = display.Display()
ip = get_ip_address("eth0")

while True:
	try:
		display.show_message("your ip is %s" % (ip))
		barcode = sys.stdin.readline()
		barcode = barcode.strip()
		try:
			response = api.search(barcode)
			print "zoeken van product met barcode %s: %s" % (barcode, response["status"]["meaning"])

			productId = response["data"]["searchResults"][0]["list"][0]["id"]
			productBrand = response["data"]["searchResults"][0]["list"][0]["brand"]
			productDescription = response["data"]["searchResults"][0]["list"][0]["description"]
			productImagePath = response["data"]["searchResults"][0]["list"][0]["overviewImage"]

			image = api.get_product_image(productImagePath)
			if image is not None:
				display.show_product(image, productBrand, productDescription)

			print "Product [%s] %s - %s" % (productId, productBrand, productDescription)

			response = api.add(productId, 1, "S")
			print "toevoegen aan de winkelmand: %s" % (response["status"]["meaning"])

			time.sleep(5)

			basket = api.show_basket()

			basket_content = ""
			for category in basket["data"]["articles"]:
				basket_content += category["colruyt.cogomw.bo.RestTreeBranch"]["description"] + "\n"
				for article in category["list"]:
					basket_content += "  %s - %s : %s stuks\n" % (article["brand"], article["description"], article["quantity"])
			basket_content += "----------------------\n"
			basket_content += "subtotal: €%s\n" % basket["data"]["subTotal"]
			basket_content += "service cost: €%s\n" % basket["data"]["serviceCost"]
			basket_content += "total: €%s\n" % basket["data"]["total"]
			basket_content += "-----------------------\n"
			display.show_message(basket_content)
			print basket_content

			time.sleep(5)
		except ValueError as e:
			print "something went wrong: %s" % (e)
		except:
			break
	except (KeyboardInterrupt, SystemExit):
		print "catched keyboardinterrupt"
		break

display.close()
api.logout()
del(display)
del(api)