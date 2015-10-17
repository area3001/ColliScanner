import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import BoundedNumericProperty
from kivy.clock import Clock
from kivy.factory import Factory
from colruyt import ColruytAPI
from barcode import BarcodeScanner
import socket
import fcntl
import struct
import io

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

        try:
            self.manager.api.login(username, password)
        except ValueError as err:
            popup = Popup(title="Error", content=Label(text="%s" % (err)), size_hint=(None, None), size=(600, 300))
            popup.open()
            return    

        self.manager.app.config.set("credentials", "username", username)
        self.manager.app.config.set("credentials", "password", password)
        self.manager.app.config.write()
        self.manager.go_next("ScannerView")

class ProductView(Screen):
    id = None
    amount = BoundedNumericProperty(1, min=1, max=100, errorvalue=1)
    progress = BoundedNumericProperty(0, min=0, max=100, errorvalue=1)

    def on_leave(self):
        self.stop_timer()

    def getProduct(self):
        api = self.manager.api
        barcode = self.manager.scanned
        try:
            response = api.search(barcode)
        except ValueError as err:
            popup = Popup(title="Error", content=Label(text="%s" % (err)), size_hint=(None, None), size=(800, 300))
            popup.open()
            self.manager.go_back("ScannerView")
            return

        print "zoeken van product met barcode %s: %s" % (barcode, response["status"]["meaning"])

        self.amount = 1
        self.id = productId = response["data"]["searchResults"][0]["list"][0]["id"]
        productBrand = response["data"]["searchResults"][0]["list"][0]["brand"]
        productDescription = response["data"]["searchResults"][0]["list"][0]["description"]
        productImagePath = response["data"]["searchResults"][0]["list"][0]["overviewImage"]
        price = response["data"]["searchResults"][0]["list"][0]["price"]

        image = api.get_product_image(productImagePath)

        self.ids.product_image.data = image
        self.ids.product_description.text = "%s - %s : %s euro" % (productBrand, productDescription, price)

        print "Product [%s] %s - %s : %s euro" % (productId, productBrand, productDescription, price)

        self.progress = 0
        Clock.schedule_interval(self.progress_callback, float(App.get_running_app().config.getdefaultint("ColliScanner", "wait_time", 10))/100)

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
        response = self.manager.api.add(self.id, self.amount, "S")
        print "%s stuks toevoegen aan de winkelmand: %s" % (self.amount, response["status"]["meaning"])
        self.manager.go_back("ScannerView")

class ScannerView(Screen):
    def on_leave(self):
        Clock.unschedule(self.scan_callback)
        self.ids.txtBarcode.text = ""

    def search(self):
        self.manager.scanned = self.ids.txtBarcode.text
        self.manager.go_next("ProductView")

    def logout(self):
        Clock.unschedule(self.scan_callback)
        self.manager.api.logout()
        self.manager.app.config.set("credentials", "username", "")
        self.manager.app.config.set("credentials", "password", "")
        self.manager.app.config.write()
        self.manager.go_back("LoginView")

    def scan_callback(self, image):
        for symbol in image:
            # barcodes found
            print "decoded %s symbol, %s" % (symbol.type, symbol.data)
            self.manager.scanned = symbol.data
            self.manager.go_next("ProductView")
            self.manager.scanner.stop()

    def setCallback(self):
        self.manager.scanner.setCallback(scan_callback)
        self.manager.scanner.start()

class IpView(Screen):
    def on_pre_enter(self):
        self.ids.lblIp.text = "Your IP is %s" % (self.get_ip_address("eth0"))

    def get_ip_address(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack("256s", ifname[:15])
        )[20:24])

class BasketView(Screen):
    def on_pre_enter(self):
        self.ids.articles.clear_widgets()
        basket = self.manager.api.show_basket()
        for category in basket["data"]["articles"]:
            #category["colruyt.cogomw.bo.RestTreeBranch"]["description"]
            for article in category["list"]:
                self.add_article(article) 
        self.ids.txtSubtotal.text = basket["data"]["subTotal"]
        self.ids.txtServiceCost.text = basket["data"]["serviceCost"]
        self.ids.txtTotal.text = basket["data"]["total"]

    def add_article(self, article):
        #overviewImage
        #unitPrice
        #lineTotalPrice
        article_inst = Factory.BasketLine()
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
                self.manager.api.logout()

    def build(self):
        config = self.config
        username = config.get("credentials", "username")
        password = config.get("credentials", "password")

        self.manager = RootScreen()
        self.manager.app = self
        self.manager.scanner = BarcodeScanner(800, 600)


        if username and password:
            self.manager.api = ColruytAPI(username, password)
            self.manager.current = "ScannerView"
        else:
            self.manager.api = ColruytAPI()
            self.manager.current = "LoginView"
        return self.manager

if __name__ == "__main__":
    ColliScanApp().run()