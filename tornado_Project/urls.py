#coding:utf-8

import os

from handlers import Passport,VerifyCode,Profile,House,Order
from handlers.BaseHandler import StaticFileHandler

handlers = [
	
	(r"/api/imagecode",VerifyCode.ImageCodeHandler),
	(r"/api/smscode",VerifyCode.SMSCodeHandler),
	(r'^/api/login$',Passport.LoginHandler),
	(r'^/api/register',Passport.RegisterHandler),
	(r'^/api/check_login$',Passport.CheckLoginHandler),
	(r'^/api/logout$',Passport.LogoutHandler),
	(r'^/api/profile/avatar$',Profile.AvatarHandler),
	(r'^/api/profile$',Profile.ProfileHandler),
	(r'^/api/profile/name$',Profile.NameHandler),
	(r'^/api/profile/auth$',Profile.AuthHandler),
	(r'^/api/house/area$',House.AreaInfoHandler), #城区信息
	(r'^/api/house/my$',House.MyHousesHandler),
	(r'^/api/house/info$',House.HouseInfoHandler),#上传房屋基本信息
	(r'^/api/house/image$',House.HouseImageHandler),
	(r'^/api/house/index$',House.IndexHandler),
	(r'^/api/house/list$',House.HouseListHandler),
	(r'^/api/house/list2$',House.HouseListRedisHandler),
	(r'^/api/order',Order.OrderHandler), #下单
	(r'^/api/order/my',Order.MyOrderHandler), #我的订单，作为房客和房东同时适用
	(r'^/api/order/accept',Order.AcceptOrderHandler), #接单
	(r'^/api/order/reject$', Order.RejectOrderHandler), # 拒单
	(r'^/api/order/comment$', Order.OrderCommentHandler),
	(r"/(.*)",StaticFileHandler,dict(path=os.path.join(os.path.dirname(__file__),"html"),default_filename="index.html"))
]
