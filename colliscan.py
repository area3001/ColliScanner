import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.properties import BoundedNumericProperty
from kivy.clock import Clock
from kivy.factory import Factory
from colruyt import ColruytAPI
from barcode import BarcodeScanner
import socket
import fcntl
import struct
import io
import json

class RootScreen(ScreenManager):
	api = None
	app = None
	scanned = None
	scanner = None

	def go_next(self, screenName):
		self.transition.direction = "left"
		self.current = screenName

	def go_back(self, screenName):
		self.transition.direction = "right"
		self.current = screenName

class ColliAsyncImage(AsyncImage):
	headers = {
		"Host": "colruyt.collectandgo.be",
		"Proxy-Connection": "keep-alive",
		"Accept-Encoding": "gzip, deflate",
		"Accept-Language": "nl-nl",
		"Accept": "*/*",
		"Connection": "keep-alive",
		"User-Agent": "Collect&Go/3.3.1.11218 CFNetwork/758.1.3 Darwin/15.0.0"
	}

class LoginView(Screen):
	def on_leave(self):
		self.ids.txtUsername.text = ""
		self.ids.txtPassword.text = ""

	def login(self):
		username = self.ids.txtUsername.text
		password = self.ids.txtPassword.text

		if not username or not password:
			popup = Popup(title="Error", content=Label(text="please fill in username and password"), size_hint=(None, None), size=(800, 300))
			popup.open()
			return

		self.manager.api.login(username, password, self.login_succes, self.login_failed)

	def login_succes(self, req, content):
		response = json.loads(content)
		if self.manager.api.responseIsSuccess(response):
			username = self.ids.txtUsername.text
			password = self.ids.txtPassword.text
			self.manager.api.token = response["data"]["oAuth"]
			self.manager.app.config.set("credentials", "username", username)
			self.manager.app.config.set("credentials", "password", password)
			self.manager.app.config.write()
			self.manager.go_next("ScannerView")
		else:
			self.login_failure_callback("Login failed: %s" % (response["status"]["meaning"]))
		
	def login_failed(self, err):
		popup = Popup(title="Error", content=Label(text="%s" % (err)), size_hint=(None, None), size=(600, 300))
		popup.open()

class ProductView(Screen):
	id = None
	amount = BoundedNumericProperty(1, min=1, max=100, errorvalue=1)
	progress = BoundedNumericProperty(0, min=0, max=100, errorvalue=1)

	def on_leave(self):
		self.stop_timer()
		self.ids.product_image.source = ""

	def getProduct(self):
		api = self.manager.api
		barcode = self.manager.scanned
		response = api.search(barcode, self.search_succes, self.search_failed)
	
	def search_failed(self, err):
		popup = Popup(title="Error", content=Label(text="%s" % (err)), size_hint=(None, None), size=(800, 300))
		popup.open()
		self.manager.go_back("ScannerView")

	def search_succes(self, req, content):
		response = json.loads(content)
		api = self.manager.api
		if api.responseIsSuccess(response):		
			barcode = self.manager.scanned
			print "zoeken van product met barcode %s: %s" % (barcode, response["status"]["meaning"])

			self.amount = 1
			self.id = productId = response["data"]["searchResults"][0]["list"][0]["id"]
			productBrand = response["data"]["searchResults"][0]["list"][0]["brand"]
			productDescription = response["data"]["searchResults"][0]["list"][0]["description"]
			productImagePath = response["data"]["searchResults"][0]["list"][0]["overviewImage"]
			price = response["data"]["searchResults"][0]["list"][0]["price"]
			image = api.get_product_image(productImagePath)

			self.ids.product_image.source = image
			self.ids.product_description.text = "%s - %s : %s euro" % (productBrand, productDescription, price)

			print "Product [%s] %s - %s : %s euro" % (productId, productBrand, productDescription, price)

			self.progress = 0
			Clock.schedule_interval(self.progress_callback, float(App.get_running_app().config.getdefaultint("ColliScanner", "wait_time", 10))/100)
		else:
			self.search_failed("Search failed: %s" % (response["status"]["meaning"]))

	def progress_callback(self, dt):
		self.progress += 1
		self.ids.pbProgress.value = self.progress
		if self.progress == 100:
			self.add_product()
			return False
		return True

	def increase(self):
		self.amount += 1
		self.stop_timer()

	def decrease(self):
		self.amount -= 1
		self.stop_timer()

	def stop_timer(self):
		Clock.unschedule(self.progress_callback)
		self.progress = 0
		self.ids.pbProgress.value = self.progress

	def confirm(self):
		self.add_product()

	def add_product(self):
		self.manager.api.add(self.id, self.amount, "S", self.add_success, self.add_failed)

	def add_success(self, req, content):
		response = json.loads(content)
		if self.manager.api.responseIsSuccess(response):
			print "%s stuks toevoegen aan de winkelmand: %s" % (self.amount, response["status"]["meaning"])
			self.manager.go_back("ScannerView")
		else:
			self.add_failed("Fout bij toevoegen: %s" % (response["status"]["meaning"]))


	def add_failed(self, err):
		popup = Popup(title="Error", content=Label(text="%s" % (err)), size_hint=(None, None), size=(800, 300))
		popup.open()

class ScannerView(Screen):
	def on_leave(self):
		self.manager.scanner.terminate()
		self.ids.txtBarcode.text = ""

	def search(self):
		self.manager.scanner.terminate()
		self.manager.scanned = self.ids.txtBarcode.text
		self.manager.go_next("ProductView")

	def logout(self):
		self.manager.scanner.terminate()
		self.manager.api.logout(self.logout_success, self.logout_failed)

	def logout_success(self, req, content):
		response = json.loads(content)
		if self.manager.api.responseIsSuccess(response):
			self.manager.app.config.set("credentials", "username", "")
			self.manager.app.config.set("credentials", "password", "")
			self.manager.app.config.write()
			self.manager.go_back("LoginView")
		else:
			self.logout_failed("Login failed: %s" % (response["status"]["meaning"]))

	def logout_failed(self, err):
		popup = Popup(title="Error", content=Label(text="%s" % (err)), size_hint=(None, None), size=(800, 300))
		popup.open()	

	def scan_callback(self, barcode):
		print "decoded %s" % (barcode)
		self.manager.scanned = barcode
		self.manager.go_next("ProductView")
		self.manager.scanner.terminate()

	def setCallback(self):
		self.manager.scanner = BarcodeScanner()
		self.manager.scanner.setCallback(self.scan_callback)
		self.manager.scanner.start()

class IpView(Screen):
	def on_pre_enter(self):
		self.ids.lblIp.text = "Your IP is %s" % (self.get_ip_address("eth0"))

	def get_ip_address(self, ifname):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		return socket.inet_ntoa(fcntl.ioctl(
			s.fileno(),
			0x8915, # SIOCGIFADDR
			struct.pack("256s", ifname[:15])
		)[20:24])

class BasketView(Screen):
	def on_pre_enter(self):
		self.ids.articles.clear_widgets()

	def on_enter(self):
		self.manager.api.show_basket(self.basket_success, self.basket_failed)

	def basket_success(self, req, content):
		response = json.loads(content)
		if self.manager.api.responseIsSuccess(response):
			for category in response["data"]["articles"]:
				#category["colruyt.cogomw.bo.RestTreeBranch"]["description"]
				for article in category["list"]:
					self.add_article(article) 
			self.ids.txtSubtotal.text = response["data"]["subTotal"]
			self.ids.txtServiceCost.text = response["data"]["serviceCost"]
			self.ids.txtTotal.text = response["data"]["total"]
		else:
			self.basket_failed("Get basket failed: %s" % (response["status"]["meaning"]))

	def basket_failed(self, err):
		popup = Popup(title="Error", content=Label(text="%s" % (err)), size_hint=(None, None), size=(800, 300))
		popup.open()

	def add_article(self, article):
		#overviewImage
		#unitPrice
		#lineTotalPrice
		productimage = self.manager.api.get_product_image(article["overviewImage"])
		article_inst = Factory.BasketLine()
		article_inst.imgProduct = productimage
		article_inst.txtBrand = article["brand"]
		article_inst.txtDescription = article["description"]
		article_inst.txtQuantity = article["quantity"]
		article_inst.txtTotal = article["lineTotalPrice"]
		self.ids.articles.add_widget(article_inst)

class ColliScanApp(App):
	scanner = None 
	manager = None

	def build_config(self, config):
		config.setdefaults("credentials", {
			"username": "",
			"password": ""
		})

	def on_stop(self):
		if self.manager:
			if self.manager.api.loggedIn():
				self.manager.api.logout(None, None)

	def build(self):
		config = self.config
		username = config.get("credentials", "username")
		password = config.get("credentials", "password")

		self.manager = RootScreen()
		self.manager.app = self

		if username and password:
			self.manager.api = ColruytAPI(username, password)
			self.manager.current = "ScannerView"
		else:
			self.manager.api = ColruytAPI()
			self.manager.current = "LoginView"
		return self.manager

if __name__ == "__main__":
	ColliScanApp().run()