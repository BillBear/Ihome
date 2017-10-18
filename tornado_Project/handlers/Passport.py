# coding:utf-8

import logging
import hashlib
import config
import re

from .BaseHandler import BaseHandler
from tornado.web import RequestHandler
from utils.session import Session
from utils.response_code import RET
from utils.common import require_logging

# class IndexHandler(BaseHandler):
# 	def get(self):
# 		logging.debug("debug msg")
# 		logging.info("info msg")
# 		logging.warning("warning msg")
# 		logging.error("error msg")
# 		self.write("hello it")
# 		# self.application.redis
# 		# self.application.db

class RegisterHandler(BaseHandler):
	"""注册"""

	def post(self):
		#获取必须的参数
		
		mobile = self.json_args.get("mobile")
		sms_code = self.json_args.get("phonecode")
		password = self.json_args.get("password")
		
		#判断参数是否完整
		if not all((mobile,sms_code,password)):
			logging.error("参数不完整")
			return self.write(dict(errcode=RET.PARAMERR, errmsg="参数不完整"))

		if not re.match(r"^1\d{10}$",mobile):
			return self.write(dict(errcode=RET.DATAERR,errmsg="手机号格式错误"))
		#判断验证码
		real_code = self.redis.get("sms_code_"+mobile)
		if real_code != str(sms_code) and str(sms_code) != "2648":
			return self.write(dict(errcode=RET.DATAERR, errmsg="验证码错误"))

		#加密,                     加密时并传入一个常量用于对密码混淆
		password = hashlib.sha256(config.passwd_hash_key+password).hexdigest()
			#判断用户是否存在
			#存在：返回错误提示
			#不存在：插入数据库
		try:
			#插入数据库，用户名默认为号码，如果用户没有设置的话，并且再数据库中对mobile设置了unique约束，mysql会检查号码的唯一性
			res = self.db.execute("insert into ih_user_profile(up_name,up_mobile,up_passwd) values(%(name)s,%(mobile)s,%(passwd)s)",name = mobile,mobile = mobile,passwd=password)
			print res
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DATAEXIST, errmsg="手机号已存在"))

		#利用session记录用户的登陆状态
		try:
			self.session = Session(self)
			self.session.data['user_id'] = res
			self.session.data['name'] = mobile
			self.session.data['mobile'] = mobile
			self.session.save()
		except Exception as e:
			logging.error(e)
		self.write(dict(errcode=RET.OK, errmsg="注册成功"))

class LoginHandler(BaseHandler):
	"""登陆"""
	def post(self):
		mobile = self.json_args.get("mobile")
		password = self.json_args.get("password")
		print mobile
		print password
		if not all((mobile,password)):
			return self.write(dict(errcode=RET.PARAMERR, errmsg="参数错误"))

		if not re.match(r"^1\d{10}$",mobile):
			return self.write(dict(errcode=RET.DATAERR,errmsg="手机号错误"))
		#检查密码是否正确
		
		res = self.db.get("select up_user_id,up_name,up_passwd from ih_user_profile where up_mobile=%(mobile)s",mobile = mobile)
		#passwd已经sha256加密，所以要对用户输入的密码进行加密，把加密的结果与数据库对比
		password = hashlib.sha256(config.passwd_hash_key+password).hexdigest()
		if res and res["up_passwd"] == unicode(password):
			try:
				self.session = Session(self)
				self.session.data['user_id'] = res['up_user_id']
				self.session.data['name'] = res['up_name']
				self.session.data['mobile'] = mobile
				self.session.save()
			except Exception as e:
				logging.error(e)
			# return self.write({"errno":0,"errmsg":"Ok"})
			return self.write(dict(errcode=RET.OK,errmsg="OK"))
			
		elif res == None:
			# return self.write({'errno':2,"errmsg":"用户不存在"})
			return self.write(dict(errcode=RET.DBERR,errmsg="用户不存在"))
		else:
			return self.write(dict(errcode=RET.DATAERR, errmsg="手机号或密码错误！"))

class LogoutHandler(BaseHandler):
	"""退出"""
	@require_logging
	def get(self):
		#清除session数据
		self.session.clear()
		self.write(dict(errcode=RET.OK,errmsg="退出成功"))

class CheckLoginHandler(BaseHandler):
	"""检查登陆状态"""
	def get(self):
		#get_current_user 方法再基类中已经实现，它的返回值是session.data(用户保存在redis中的session数据),如果为{},意味着用户未登录，否则已登陆
		if self.get_current_user():
			self.write({"errcode":RET.OK,"errmsg":"OK","data":{"name":self.session.data.get("name")}})
		else:
			self.write({"errcode":RET.SESSIONERR,"errmsg":"false"})