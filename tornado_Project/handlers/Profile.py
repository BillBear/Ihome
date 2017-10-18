#coding:utf-8

import logging
import config

from utils.response_code import RET
from .BaseHandler import BaseHandler
from utils.image_storage import storage
from utils.common import require_logging

class AvatarHandler(BaseHandler):
	"""上传头像"""

	@require_logging
	def post(self):
		#获取图片文件参数
		try:
			image_data = self.request.files["avatar"][0]["body"]
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.NODATA,errmsg="未传图片"))
		print image_data
		#调用七牛上传图片
		try:
			#调用storage返回一个图片唯一识别码key
			key = storage(image_data)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.THIRDERR,errmsg="保存失败"))

		#从session中取出user_id
		user_id = self.session.data["user_id"]
		#保存图片名称到数据库
		try:
			res = self.db.execute("update ih_user_profile set up_avatar=%(avatar)s where up_user_id=%(user_id)s",avatar=key,user_id=user_id)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="数据库保存失败"))
		self.write(dict(errcode=RET.OK,errmsg="保存成功",data="%s%s"%(config.image_url_prefix,key)))

class ProfileHandler(BaseHandler):
	"""获取个人信息"""
	@require_logging
	def get(self):
		user_id = self.session.data["user_id"]
		#查询用户信息
		try:
			res = self.db.get("select up_name,up_mobile,up_avatar from ih_user_profile where up_user_id=%s",user_id)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="查询出错"))
		if res["up_avatar"]:
			image_url = config.image_url_prefix+res["up_avatar"]
		else:
			image_url = None
		self.write({"errcode":RET.OK,"errmsg":"OK","data":{"user_id":user_id,"name":res["up_name"],"mobile":res["up_mobile"],"avatar":image_url}})

class NameHandler(BaseHandler):

	"""修改用户名"""
	@require_logging
	def post(self):
		#获取用户id
		user_id = self.session.data["user_id"]
		#获取用户要修改的用户名参数
		user_name = self.json_args.get("name")
		#判断参数是否完整且不能为空字符串
		# if name == None or "" == name
		if user_name in (None,""):
			return self.write(dict(errcode=RET.PARAMERR,errmsg="参数错误"))

		#更新在数据库中，同时判断用户名是否唯一，
		try:
			self.db.execute_rowcount("update ih_user_profile set up_name =%(name)s where up_user_id=%(user_id)s",name=user_name,user_id=user_id)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="用户名已存在"))

		#修改session 中的name字符串并且保存到redis中
		self.session.data['name'] = user_name

		try:
			self.session.save()
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="缓存失败"))
		self.write(dict(errcode=RET.OK,errmsg="OK"))


class AuthHandler(BaseHandler):
	"""用户实名认证"""

	@require_logging
	def get(self):
	#查询用户数据并返回
		#在session中获取用户id
		user_id = self.session.data["user_id"]

		#在数据库中查询信息
		try:
			res = self.db.get("select up_real_name,up_id_card from ih_user_profile where up_user_id=%s",user_id)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="查询数据失败"))
		logging.debug(res)
		if not res:
			return self.write(dict(errcode=RET.NODATA,errmsg="认证数据不存在"))
		self.write({"errcode":RET.OK,"errmsg":"OK","data":{"real_name":res.get("up_real_name"),"id_card":res.get("up_id_card","")}})

	@require_logging
	def post(self):
		#查询id并获取用户输入的数据
		user_id = self.session.data["user_id"]
		real_name = self.json_args.get("real_name")
		id_card = self.json_args.get("id_card")
		#判断用户和身份证号是否为空或者空字符串
		if real_name in (None,"") or id_card in (None,""):
			return self.write(dict(errcode=RET.PARAMERR,errmsg="用户输入参数错误"))
		#查询数据库的用户数据
		try:
			res = self.db.execute_rowcount("update ih_user_profile set up_real_name=%s,up_id_card=%s where up_user_id=%s",real_name,id_card,user_id)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="修改失败"))
		self.write({"errcode":RET.OK,"errmsg":"OK"})