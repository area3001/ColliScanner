import httplib2 as http
import json

try:
	from urlparse import urlparse
except ImportError:
	from urllib.parse import urlparse

class ColruytAPI:
	def __init__(self, username = None, password = None):
		self.h = http.Http()
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
			self.login(username, password)


	def request(self, path, body):
		target = urlparse(self.uri+self.basePath+path)
		# If you need authentication some example:
		# if auth:
		#     h.add_credentials(auth.user, auth.password)

		response, content = self.h.request(
				target.geturl(),
				self.method,
				body,
				self.headers)
		return json.loads(content)

	def responseIsSuccess(self, response):
		if response["status"]["code"] == 0:
			return True
		return False

	def login(self, username, password):
		path = "/users/authenticate.json"
		body = "logon_id=%s&password=%s" % (username, password)
		response = self.request(path, body)

		if self.responseIsSuccess(response):
			self.token = response["data"]["oAuth"]
			return
		raise ValueError("Login failed: %s" % (response["status"]["meaning"]))

	def logout(self):
		path = "/log_off.json"
		body = "oAuth=%s" % (self.token)
		response = self.request(path, body)
		if not self.responseIsSuccess(response):
			raise ValueError("Logout failed")

	def search(self, barcode):
		path = "/articles/search.json"
		body = "oAuth=%s&barcode=%s" % (self.token, barcode)
		response = self.request(path, body)
		if self.responseIsSuccess(response):
			return response
		raise ValueError("search of barcode %s failed: %s" % (barcode, response["status"]["meaning"]))

	def add(self, id, quantity, weigtCode="G"):
		path = "/basket/articles/add.json"
		body = "id=%s&weightCode=%s&comment=&quantity=%s&oAuth=%s" % (id, weigtCode, quantity, self.token)
		return self.request(path, body)

	def get_product_image(self, path):
		path = path.replace("200x200", "500x500")
		uri = "https://colruyt.collectandgo.be/cogo"
		headers = {
			"Host": "colruyt.collectandgo.be",
			"Proxy-Connection": "keep-alive",
			"Accept-Encoding": "gzip, deflate",
			"Accept-Language": "nl-nl",
			"Accept": "*/*",
			"Connection": "keep-alive",
			"User-Agent": "Collect&Go/3.3.1.11218 CFNetwork/758.1.3 Darwin/15.0.0"
		}
		target = urlparse(uri+path)
		response, content = self.h.request(
				target.geturl(),
				"GET",
				headers=headers)
		if response.status == 200:
			return content
		return None
