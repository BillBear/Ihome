#coding:utf-8

import uuid
import logging
import json
import config

class Session(object):

	def  __init__(self,requset_handler):
		# self.requset_handler = requset_handler
		self._requset_handler = requset_handler
		# self.session_id = self.requset_handler.get_secure_cookie("session_id")
		self.session_id = requset_handler.get_secure_cookie("session_id")
		if not self.session_id:
			#用户第一次访问，生成一个session_id，全局唯一
			self.session_id = uuid.uuid4().get_hex()
			self.data = {}
			requset_handler.set_secure_cookie("session_id",self.session_id)
		else:
			#拿到了session
			try:
				json_data = requset_handler.redis.get("sess_%s"%self.session_id)
			except Exception as e:
				logging.error(e)
				raise e
				#若获取出现错误则返回一个空字典
				self.data = {}

			#如果不存在data,则为空
			if not json_data:
				self.data = {}
			else:
				#对数据进行反序列化
				self.data = json.loads(json_data)

	def save(self):
		#对数据进行序列化
		json_data = json.dumps(self.data)
		try:
			# self.redis.setex("sess_%s"%self.session_id,config.session_expires,
			#                  json_data)
			self._requset_handler.redis.setex("sess_%s"%self.session_id,config.session_expires,
			                 json_data)
		except Exception as e:
			logging.error(e)
			raise Exception("save session failed")
		# else:
		# 	self.requset_handler.set_secure_cookie("session_id",
		# 	                                       self.session_id)


	def clear(self):
		"""当用户退出登陆时"""
		#先讲cookie中的数据删除
		self._requset_handler.clear_cookie("session_id")
		try:
			self.redis.delete("sess_%s"%self.session_id)
		except Exception as e:
			logging.error(e)


