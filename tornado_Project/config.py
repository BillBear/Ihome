#coding:utf-8

import os

#Application 配置参数
settings = {
	"static_path":os.path.join(os.path.dirname(__file__),"static"),
	"template_path":os.path.join(os.path.dirname(__file__),"template"),
	"cookie_secret":"BGi1V7ZTSVuqYGHq2p2qtP98+wO86EketvhH4zZn5Pg=",
	"xsrf_cookies":True,
	"debug":True,

}

passwd_hash_key = "ihome@$^*"
session_expires = 86400 #session有效期 24小时 单位秒

#mysql
mysql_options = dict(
    host = "127.0.0.1",
	database = "ihome",
	user = "root",
	password = "root"
                     )
	


#redis
redis_options = dict(
	host = "127.0.0.1",
	port = 6379
                     )

#logs文件地址参数配置

log_file = os.path.join(os.path.dirname(__file__),"logs/log")
log_level = "debug"

image_url_prefix = "http://owqo0zsg7.bkt.clouddn.com/" #七牛图片域名 

