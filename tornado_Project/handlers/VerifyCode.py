# coding:utf-8

import logging
import constants
import random
import json
import re

from .BaseHandler import BaseHandler
from utils.captcha.captcha import captcha
from libs.yuntongxun.CCP import ccp
from utils.response_code import RET

class ImageCodeHandler(BaseHandler):
	""""""
	def get(self):
		code_id = self.get_argument("codeid")
		pre_code_id = self.get_argument("precodeid")
		try:
			if pre_code_id:
				self.redis.delete("image_code_%s"%pre_code_id)
		except Exception as e:
			logging.error(e)
		#name 图片验证码名称
		#text 图片验证码文本
		#image 图片验证码二进制
		name,text,image = captcha.generate_captcha()  #生成验证码
		try:
			# 将图片内容注入redis中："image_code_123“(在redis中会自动生成一个键值对)
			self.redis.setex("image_code_%s"%code_id,
			                 constants.IMAGE_CODE_EXPIRES_SECONDS,text)
		except Exception as e:
			logging.error(e)
			self.write("")  #验证码没有生成返回空
		self.set_header("Content-Type","image/jpg")
		self.write(image) #返回生成的图片

class SMSCodeHandler(BaseHandler):
	""""""
	def post(self):
		#获取参数(json)
		mobile = self.json_args.get("mobile")
		image_code_id = self.json_args.get("image_code_id")
		image_code_text = self.json_args.get("image_code_text")
		#判断参数是否完整
		if not all((mobile,image_code_id,image_code_text)):
			return self.write(dict(errcode=RET.PARAMERR,errmsg="参数错误"))
		#利用正则表达式判断号码输入是否正确
		if not re.match(r"1\d{10}",mobile):
			return self.write(dict(errcode=RET.PARAMERR,errmsg="手机号码输入错误"))
		#判断图片验证码 
		try:
			real_image_text = self.redis.get("image_code_%s"%image_code_id)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="查询出错"))
		#不成功   返回错误信息
		#如果没有这个验证码
		if not real_image_text:
			return self.write(dict(errcode=RET.NODATA,errmsg="验证码过期"))
		if real_image_text.lower() != image_code_text.lower():
			return self.write(dict(errcode=RET.DATAERR,errmsg="验证码错误"))
		#若成功 生成随机验证码
		sms_code = "%04d" %random.randint(0,9999)
		try:
			#把验证码写进redis key:mobile 并设置过期时间，value:sms_code
			self.redis.setex("sms_code_%s"%mobile,constants.SMS_CODE_EXPIRES_SECONDS,sms_code)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="生成验证码错误"))
		# 手机号是否存在检查
		sql = "select count(*) counts from ih_user_profile where up_mobile=%s"
		try:
			ret = self.db.get(sql, mobile)
		except Exception as e:
			logging.error(e)
		else:
			if 0 != ret["counts"]:
				return self.write(dict(errcode=RET.DATAEXIST, errmsg="手机号已注册"))
		#发送短信
		try:
			ccp.sendTemplateSMS(mobile,[sms_code,constants.SMS_CODE_EXPIRES_SECONDS/60],1)
			#需要判断返回值，待实现
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.THIRDERR,errmsg="发送失败"))
		self.write(dict(errcode=RET.OK,errmsg="OK"))