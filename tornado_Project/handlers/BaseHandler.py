#coding:utf-8

import json
import tornado.web

from tornado.web import RequestHandler
from utils.session import Session


class BaseHandler(RequestHandler):
	"""handler基类"""
	@property
	def db(self):
		return self.application.db

	@property
	def redis(self):
		return self.application.redis

	def prepare(self):
		#手调用第一个接口时就触发
		self.xsrf_token
		if self.request.headers.get("Content-Type","").startswith("application/json"):
			self.json_args = json.loads(self.request.body)
		else:
			self.json_args = None
			# self.json_args = {}

	def write_error(self,status_code,**kwargs):
		pass

	def set_default_headers(self):
		self.set_header("Conten-Type","application/json;charset=UTF-8")

	def initialize(self):
		pass

	def on_finish(self):
		pass

	def get_current_user(self):
		"""判断用户是否登陆 xsrf"""
		self.session = Session(self)
		# print "ss:%s"%self.session.data
		return self.session.data

class StaticFileHandler(tornado.web.StaticFileHandler):
	"""用户第一次进入页面时没有任何请求，这样就不会有xsrf_tiken，所以将这个触发放在页面加载中。自动帮触发"""

	def __init__(self,*args,**kwargs):
		super(StaticFileHandler,self).__init__(*args,**kwargs)
		self.xsrf_token

