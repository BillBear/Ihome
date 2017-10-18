#coding:utf-8

import functools

from utils.session import Session
from utils.response_code import RET
#这是一个装饰器
def require_logging(fun):
	@functools.wraps(fun)
	def wrapper(request_handler_obj,*args,**kwargs):
		#根据get_current_user方法判断，如果返回的不是一个空字典，证明用户已经登陆，保存了用户的session数据
		if not request_handler_obj.get_current_user():
			
			request_handler_obj.write(dict(errcode=RET.SESSIONERR,errmsg="用户未登陆"))

		#返回的是空字典，代表用户未登录。没有保存session数据
		else:
			fun(request_handler_obj,*args,**kwargs)
	return wrapper