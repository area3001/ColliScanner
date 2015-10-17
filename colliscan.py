from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.properties import BoundedNumericProperty
from kivy.config import Config
from kivy.clock import Clock
from colruyt import ColruytAPI
#from barcode import BarcodeScanner
import socket
import fcntl
import struct
import io

class RootScreen(ScreenManager):
    pass

class LoginView(Screen):
    def on_leave(self):
        self.ids.txtUsername.text = ""
        self.ids.txtPassword.text = ""

    def login(self):
        username = self.ids.txtUsername.text
        password = self.ids.txtPassword.text
        print "username: %s, password: %s" % (username, password)
        App.get_running_app().api.login(username, password)
        App.get_running_app().config.set("credentials", "username", username)
        App.get_running_app().config.set("credentials", "password", password)
        App.get_running_app().config.write()
        self.manager.transition.direction = "left"
        self.manager.current = "ScannerView"

class ProductView(Screen):
    id = None
    amount = BoundedNumericProperty(1, min=1, max=100, errorvalue=1)
    progress = BoundedNumericProperty(1, min=0, max=100, errorvalue=1)

    def on_leave(self):
        Clock.unschedule(self.progress_callback)

    def getProduct(self):

        api = App.get_running_app().api
        barcode = App.get_running_app().scanned
        response = api.search(barcode)
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

        #Clock.schedule_once(self.timeout_callback, 10)
        self.progress = 1
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

    def timeout_callback(self, dt):
        self.add_product()

    def add_product(self):
        api = App.get_running_app().api
        print "%s stuks toevoegen" % (self.amount)
        response = api.add(self.id, self.amount, "S")
        print "toevoegen aan de winkelmand: %s" % (response["status"]["meaning"])
        self.manager.transition.direction = "right"
        self.manager.current = "ScannerView"

class ScannerView(Screen):
    def on_leave(self):
        Clock.unschedule(self.scan_callback)

    def logout(self):
        Clock.unschedule(self.scan_callback)
        App.get_running_app().api.logout()
        App.get_running_app().config.set("credentials", "username", "")
        App.get_running_app().config.set("credentials", "password", "")
        App.get_running_app().config.write()
        self.manager.transition.direction = "right"
        self.manager.current = "LoginView"

    def scan_callback(self, dt):
        #image = App.get_running_app().scanner.scan()
        image = "5449000011527"
        if image is not None:
            App.get_running_app().scanned = image
            self.manager.transition.direction = "left"
            self.manager.current = "ProductView"
            return False # stop the clock callback
        return True # continue the clock callback

    def setCallback(self):
        Clock.schedule_interval(self.scan_callback, 3) # scan every 2 seconds
        #self.ids.product_description.text = "Your IP is %s" % (self.get_ip_address("en0"))

class IpView(Screen):
    ip = "192.xxx.xxx.xxx"

    def on_pre_enter(self):
        #self.ip = self.get_ip_address("en0")
        self.ip = "test"

    def get_ip_address(self, ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack("256s", ifname[:15])
        )[20:24])

class BasketView(Screen):
    pass

class ColliScanApp(App):
    api = None
    scanned = None
    #scanner = None 
    def build_config(self, config):
        config.setdefaults("credentials", {
            "username": "",
            "password": ""
        })

    def on_stop(self):
        if self.api.loggedIn():
            self.api.logout()

    def build(self):
        config = self.config
        username = config.get("credentials", "username")
        password = config.get("credentials", "password")

        rootScreen = RootScreen()
        #self.scanner = BarcodeScanner(800, 600)

        if username and password:
            print "Credentials found in config: %s %s" % (username, password)
            self.api = ColruytAPI(username, password)
            rootScreen.current = "ScannerView"
        else:
            self.api = ColruytAPI()
            rootScreen.current = "LoginView"
        return rootScreen

if __name__ == "__main__":
    ColliScanApp().run()