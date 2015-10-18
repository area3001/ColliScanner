from kivy.network.urlrequest import UrlRequest
import json

class ColruytAPI:
	def __init__(self, username = None, password = None):
		self.token = ""
		self.uri = "https://cogomw.colruyt.be"
		self.basePath = "/cogomw/rest/nl/4"
		self.method = "POST"
		self.headers = {
			"Host": "cogomw.colruyt.be",
			"Proxy-Connection": "keep-alive",
			"Accept-Encoding": "gzip, deflate",
			"Content-Type": "application/x-www-form-urlencoded",
			"Accept-Language": "nl-nl",
			"Accept": "*/*",
			"Connection": "keep-alive",
			"User-Agent": "Collect&Go/3.3.1.11218 CFNetwork/758.1.3 Darwin/15.0.0"
		}
		if username is not None and password is not None:
			self.login(username, password, self.login_success, self.login_failed)
	
	def login_success(self, req, content):
		response = json.loads(content)
		if self.responseIsSuccess(response):
			self.token = response["data"]["oAuth"]
		else:
			self.login_failed("Login failed: %s" % (response["status"]["meaning"]))

	def login_failed(self, err):
		raise ValueError(err)

	def loggedIn(self):
		return self.token

	def request(self, path, body, successCallback, failureCallback):
		target = urlparse(self.uri+self.basePath+path)
		req = UrlRequest(target.geturl(), on_success=successCallback, on_failure=failureCallback, on_error=failureCallback, req_body = body, req_headers = self.headers, method=self.method, debug=True)

	def responseIsSuccess(self, response):
		if response["status"]["code"] == 0:
			return True
		return False

	def login(self, username, password, callback_success, callback_failure):
		path = "/users/authenticate.json"
		body = "logon_id=%s&password=%s" % (username, password)
		self.request(path, body, callback_success, callback_failure)

	def logout(self, callback_success, callback_failure):
		path = "/log_off.json"
		body = "oAuth=%s" % (self.token)
		self.request(path, body, callback_success, callback_failure)
		self.token = ""

	def search(self, barcode, callback_success, callback_failure):
		path = "/articles/search.json"
		body = "oAuth=%s&barcode=%s" % (self.token, barcode)
		self.request(path, body, callback_success, callback_failure)

	def add(self, id, quantity, weigtCode, callback_success, callback_failure):
		path = "/basket/articles/add.json"
		body = "id=%s&weightCode=%s&comment=&quantity=%s&oAuth=%s" % (id, weigtCode, quantity, self.token)
		self.request(path, body, callback_success, callback_failure)

	def show_basket(self, callback_success, callback_failure):
		path = "/basket/show.json"
		body = "oAuth=%s" % (self.token)
		self.request(path, body, callback_success, callback_failure)

	def get_product_image(self, path):
		path = path.replace("200x200", "500x500")
		uri = "https://colruyt.collectandgo.be/cogo"
		return uri + path
