#coding:utf-8

import logging
import constants
import json
import config
import math

from .BaseHandler import BaseHandler
from utils.response_code import RET
from utils.common import require_logging
from utils.session import Session
from utils.image_storage import storage

class AreaInfoHandler(BaseHandler):
	"""区域信息缓存"""

	def get(self):
		"""先从redis中取数据"""

		try:
			res = self.redis.get("area_info")

		except Exception as e:
			logging.error(e)
			res = None
		if res:
			logging.debug(res)
			logging.info("hit rdis cache")
			#json 本身的输出格式 是一种字符串
			# return self.write('{"errcode":%s,"errmsg":"OK","data":%s}'%(RET.OK,res))

			resp = '{"errcode":"0","errmsg":"OK","data":%s}'%res
			return self.write(resp)

		#未从redis中拿到数据，去数据库查询
		try:
			res = self.db.query("select ai_area_id,ai_name from ih_area_info")
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="数据查询错误"))
		if not res:
			return self.write(dict(errcode=RET.NODATA,errmsg="地区数据不存在"))

		data = []
		for l in res:
			 d = {
				"area_id":l.get("ai_area_id",""),
				"name":l.get("ai_name","")
			 }
			 data.append(d)

			#将数据缓存到redis中
		json_data = json.dumps(data)
		try:
			self.redis.setex("area_info",constants.AREA_INFO_REDIS_EXPIRES_SECONDS,json_data)
		except Exception as e:
			logging.error(e)
		self.write(dict(errcode=RET.OK,errmsg="OK",data=data))

class MyHousesHandler(BaseHandler):

	"""用户查看自己的房源"""

	#必须对用户进行认证，只有用户才能看到自己的房屋资源
	@require_logging
	def get(self):
		user_id = self.session.data["user_id"]
		try:

			# res = self.db.query("select a.hi_house_id,a.hi_title,a.hi_price,a.hi_ctime,b.ai_name,a.hi_index_image_url from ih_house_info a left join ih_area_info b on a.hi_area_id=b.ai_area_id where a.hi_user_id = %s" user_id)
			sql = "select a.hi_house_id,a.hi_title,a.hi_price,a.hi_ctime,b.ai_name,a.hi_index_image_url from ih_house_info a inner join ih_area_info b on a.hi_area_id=b.ai_area_id where a.hi_user_id=%s;"
			res = self.db.query(sql,user_id)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="查询错误"))
		houses = []
		if res:
			for l in res:
				house = {
					"house_id":l["hi_house_id"],
					"title":l["hi_title"],
					"price":l["hi_price"],
					"ctime":l["hi_ctime"].strftime("%Y-%m-%d"),#对datetime
					"area_name":l["ai_name"],
					"img_url":config.image_url_prefix + l["hi_index_image_url"] if l["hi_index_image_url"] else ""

				}
				houses.append(house)
		self.write(dict(errcode=RET.OK,errms="OK",houses=houses))

class HouseInfoHandler(BaseHandler):


	"""房屋信息"""
	@require_logging
	def post(self):

		#获取参数

		user_id = self.session.data.get("user_id")
		# user_id = self.get_argument("user_id") #用于测试
		title = self.json_args.get("title")
		price = self.json_args.get("price")
		area_id = self.json_args.get("area_id")
		address = self.json_args.get("address")
		room_count = self.json_args.get("room_count")
		acreage = self.json_args.get("acreage")
		unit = self.json_args.get("unit")
		capacity = self.json_args.get("capacity")
		beds = self.json_args.get("beds")
		deposit = self.json_args.get("deposit")
		min_days = self.json_args.get("min_days")
		max_days = self.json_args.get("max_days")
		facility = self.json_args.get("facility") # 对一个房屋的设施，是列表类型

		if not all((title, price, area_id, address,room_count,acreage,unit,capacity,beds,deposit,min_days,max_days)):

			return self.write(dict(errcode=RET.PARAMERR,errmsg="缺少参数"))

		try:
			#因为价格单位是分，所以要×100
			price = int(price)*100
			deposit = int(deposit)*100
		except Exception as e:

			return self.write(dict(errcode=RET.PARAMERR,errmsg="参数错误"))

		#数据
		try:
			sql="insert into ih_house_info(hi_user_id,hi_title,hi_price,hi_area_id,hi_address,hi_room_count,hi_acreage,hi_house_unit,hi_capacity,hi_beds,hi_deposit,hi_min_days,hi_max_days) values(%(user_id)s,%(title)s,%(price)s,%(area_id)s,%(address)s,%(room_count)s,%(acreage)s,%(house_unit)s,%(capacity)s,%(beds)s,%(deposit)s,%(min_days)s,%(max_days)s)"

			#对于insert语句，execute方法会返回最后一个自增id
			house_id = self.db.execute(sql,user_id=user_id,title=title,price=price,area_id=area_id,address=address,room_count=room_count,acreage=acreage,house_unit=unit,capacity=capacity,beds=beds,deposit=deposit,min_days=min_days,max_days=max_days)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="保存数据出错"))

		try:
			#对于try要尽量少使用，尤其要用再捕捉一些不可预知的异常（联网失败，端口出现问题等）,因为比较耗资源
			sql = "insert into ih_house_facility(hf_house_id,hf_facility_id) values"
			sql_val = [] #用来保存条目的(%s,%s)部分，最终的形式["(%S,%s)","(%s,%s)"]
			vals = [] #用来保存具体的绑定变量值
			for facility_id in facility:
				#sql +="(%s,%s)，"采用此种方式，sql语句末尾会多出一个逗号
				sql_val.append("(%s,%s)")
				vals.append(house_id)
				vals.append(facility_id)

			sql += ",".join(sql_val)
			vals = tuple(vals)
			logging.debug(sql)
			logging.debug(vals)
			self.db.execute(sql,*vals)
		except Exception as e:
			logging.error(e)
			try:
				self.db.execute("delete from ih_house_info where hi_house_id=%s",house_id)
			except Exception as e:
				logging.error(e)
				return self.write(dict(errcode=RET.DBERR,errmsg="删除失败"))
			else:
				return self.write(dict(errcode=RET.DBERR,errmsg="未保存数据"))

		#返回
		self.write(dict(errcode=RET.OK,errmsg="Ok",house_id=house_id))

	def get(self):
		"""获取房屋信息"""
		session = Session(self)
		user_id = session.data.get("user_id","-1")
		house_id = self.get_argument("house_id")
		# self.set_header('Content-Type','application/json;charset=UTF-8')
		#校验参数
		if not house_id:
			return self.write(dict(errcode=RET.PARAMERR,errmsg="缺少参数"))

		#先从redis缓存中获取信息
		try:
			#此处可能报错
			res = self.redis.get("house_info_%s"%house_id)
		except Exception as e:
			logging.error(e)
			res = None
		if res:
			res = json.loads(res)
			#此时从redis中取到的缓存json 格式数据
			resp = {'errcode':'0','errmsg':'OK','data':res,'user_id':user_id}
			return self.write(resp)
	
		#查询数据库

		#查询房屋基本信息
		sql = "select hi_title,hi_price,hi_address,hi_room_count,hi_acreage,hi_house_unit,hi_capacity,hi_beds,hi_deposit,hi_min_days,hi_max_days,up_name,up_avatar,hi_user_id from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id where hi_house_id=%s"

		try:
			ret = self.db.get(sql,house_id)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="查询错误"))

		#用户查询的可能是不存在的房屋id,此时res为None
		if not ret:
			return self.write(dict(errcode=RET.NODATA,errmsg="查无此房"))

		data = {
			"hid":house_id,
			"user_id":ret["hi_user_id"],
			"title":ret["hi_title"],
			"price":ret["hi_price"],
			"address":ret["hi_address"],
			"room_count":ret["hi_room_count"],
			"acreage":ret["hi_acreage"],
			"unit":ret["hi_house_unit"],
			"capacity":ret["hi_capacity"],
			"beds":ret["hi_beds"],
			"deposit":ret["hi_deposit"],
			"min_days":ret["hi_min_days"],
			"max_days":ret["hi_max_days"],
			"user_name":ret["up_name"],
			"user_avatar":config.image_url_prefix + ret["up_avatar"] if ret.get("up_avatar") else ""
		}

		#查询房屋的图片信息
		sql = "select hi_url from ih_house_image where hi_house_id=%s"
		try:
			res = self.db.query(sql,house_id)
		except Exception as e:
			logging.error(e)
			res = None

		#如果查询到图片
		images = []
		if res:
			for image in res:
				images.append(config.image_url_prefix+image["hi_url"])
		data["images"] = images

		#查询房屋的基本设施
		sql = "select hf_facility_id from ih_house_facility where hf_house_id = %s"
		try:
			res = self.db.query(sql,house_id)
		except Exception as e:
			logging.error(e)
			res = None

		#如果查到设施
		facilities = []
		if res:
			for facility in res:
				facilities.append(facility["hf_facility_id"])
		data["facilities"] = facilities

		#查询评论信息
		sql = "select oi_comment,up_name,oi_utime,up_mobile from ih_order_info inner join ih_user_profile on oi_user_id=up_user_id where oi_house_id=%s and oi_status=4 and oi_comment is not null"

		try:
			res = self.db.query(sql,house_id)
		except Exception as e:
			logging.error(e)
			res = None

		comments = []
		if res:
			for comment in res:
				comments.append(dict(
					user_name = comment["up_name"] if comment["up_name"] != comment["up_mobile"] else "匿名用户",
					content = comment["oi_comment"],
					ctime = comment["oi_utime"].strftime("%Y-%m-%d %H:%M:%S")
									 ))
		data["comments"] = comments

		#存入到redis中
		json_data = json.dumps(data)
		try:
			self.redis.setex("house_info_%s"%house_id,constants.REDIS_HOUSE_INFO_EXPIRES_SECONDES,json_data)
		except Exception as e:
			logging.error(e)

		resp = '{"errcode":"0","errmsg":"OK","data":%s,"user_id":%s}'%(json_data,user_id)
		#self.write(dict(errcode=RET.OK,errmsg="Ok",data=data))
		self.write(resp)


class HouseImageHandler(BaseHandler):
	"""房屋照片"""
	@require_logging
	def post(self):
		user_id = self.session.data["user_id"]
		# user_id = self.get_argument("user_id")  用于测试
		house_id = self.get_argument("house_id")
		house_image = self.request.files["house_image"][0]["body"]

		#调用七牛接口上传图片
		img_name = storage(house_image)

		if not img_name:
			return self.write({"errcode":RET.THIRDERR,"errmsg":"qiniu error"})

		try:
			#保存图片路径到数据库ih_house_image表，并且设置房屋的主图片（ih_house_info中的hi_index_image_url）
			#将用户上传的第一张图片作为该房屋的主图片
			sql = "insert into ih_house_image(hi_house_id,hi_url) values(%s,%s);"\
				"update ih_house_info set hi_index_image_url=%s where hi_house_id=%s and hi_index_image_url is null "
			self.db.execute(sql,house_id,img_name,img_name,house_id)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="上传失败"))
		img_url = config.image_url_prefix+img_name
		self.write(dict(errcode=RET.OK,errmsg="OK",url=img_url))

class IndexHandler(BaseHandler):
	"""主页信息"""
	def get(self):
		try:
			res = self.redis.get("home_page_data")
		except Exception as e:
			logging.error(e)
			res = None
		if res:
			json_houses = json.loads(res)
		else:
			try:
				#查询数据库，返回房屋订单数目最多的5条数据（房屋订单通过hi_order_count来表示）
				house_res = self.db.query("select hi_house_id,hi_title,hi_order_count,hi_index_image_url from ih_house_info order by hi_order_count desc limit %s"%constants.HOME_PAGE_MAX_HOUSES)
			except Exception as e:
				logging.error(e)
				return self.write({"errcode":RET.DBERR,"errmsg":"未查询到相关数据"})
			if not house_res:
				return self.write({"errcode":RET.NODATA,"errmsg":"相关数据不存在"})
			houses = []
			for l in house_res:
				if not l["hi_index_image_url"]:
					continue
				house = {
					"house_id":l["hi_house_id"],
					"title":l["hi_title"],
					"img_url":config.image_url_prefix + l["hi_index_image_url"]
				}
				houses.append(house)
			json_houses = json.dumps(houses)
			
			try:
				self.redis.setex("home_page_data",constants.HOME_PAGE_DATA_REDIS_EXPIRES_SECONDS,json_houses)
			except Exception as e:
				logging.error(e)

		#返回首页城区数据
		try:
			res = self.redis.get("area_info")
		except Exception as e:
			logging.error(e)
			res = None
		if res:
			json_areas = json.loads(res)
		else:
			try:
				area_res = self.db.query("select ai_area_id,ai_name from ih_area_info")
				
			except Exception as e:
				logging.error(e)
				area_res = None
			areas = []
			
			if area_res:
				for area in area_res:
					areas.append(dict(area_id=area["ai_area_id"],name=area["ai_name"]))
			json_areas = json.dumps(areas)
			try:
				self.redis.setex("area_info",constants.REDIS_AREA_INFO_EXPIRES_SECONDS,json_areas)
			except Exception as e:
				logging.error(e)
		# resp = '{"errcode":"0","errmsg":"OK","houses":%s,"areas":%s}'%(json_houses,json_areas)
		resp = dict(errcode=RET.OK,errmsg="OK",houses=json_houses,areas=json_areas)
		self.write(resp)

class HouseListHandler(BaseHandler):
	"""房屋列表"""
	def get(self):
		#获取参数

		start_date = self.get_argument("sd","")
		end_date = self.get_argument("ed","")
		area_id = self.get_argument("aid","")
		sort_key = self.get_argument("sk","new")
		page = self.get_argument("p","1")
		
		#检查参数
		#判断日期格式，sort_key字段的值，page的整数

		#数据查询
		#涉及到表：ih_house_info房屋的基本信息，ih_user_profile房东的用户信息  ih_order_info 房屋订单数据

		sql = "self distinct hi_title,hi_house_id,hi_price,hi_room_count,hi_address,hi_order_count,up_avatar,hi_index_image_url,hi_ctime "\
			  "from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id left join ih_order_info"\
			  "on hi_house_id=oi_house_id"

		sql_total_count = "select count(distinct hi_house_id) count from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id"\
						  "left join ih_order_info on hi_house_id=oi_house_id"

		sql_where = [] #用来保存sql语句的where条件
		sql_params = {} #用来保存sql查询所需的动态数据

		if start_date and end_date:
			sql_part = "((oi_begin_date>=%(end_date)s or oi_end_date<=%(start_date)s)"\
					   "or (oi_begin_date is null and oi_end_date is null))"
			sql_where.append(sql_part)
			sql_params["start_date"] = start_date
			sql_params["end_date"] = end_date
		elif start_date:
			sql_part = "(oi_end_date<%(start_date)s or (oi_begin_date is null and oi_end_date is null))"
			sql_where.append(sql_part)
			sql_params["start_date"] = start_date
		elif end_date:
			sql_part = "(oi_begin_date>%(end_date)s or (oi_begin_date is null and oi_end_date is null))"
			sql_where.append(sql_part)
			sql_params["end_date"] = end_date

		if area_id:
			sql_part = "hi_area_id=%(area_id)s"
			sql_where.append(sql_part)
			sql_params["area_id"] = area_id

		if sql_where:
			sql += "where"
			sql += "and".join(sql_where)

		#有了where条件，先查询总条目数
		try:
			res = self.db.get(sql_total_count,**sql_params)
		except Exception as e:
			logging.error(e)
			total_page = -1
		else:
			total_page = int(math.ceil(res["count"] / float(constants.HOME_LIST_PAGE_CAPACITY)))
			page = int(page)
			if page>total_page:
				return self.write(dict(errcode=RET.OK,errmsg="OK",data=[],total_page=total_page))

		#排序
		if "new" == sort_key: #按最新上传时间排序
			sql += "order by hi_ctime desc"
		elif "booking" == sort_key:
			#最受欢迎
			sql += "order by hi_order_count desc"
		elif "price-inc" == sort_key:
			#按价格由低到高
			sql += "order by hi_price asc"
		elif "price-des" == sort_key:
			#价格由低到高
			sql += "order by hi_price desc"

		#分页
		#Limit 10 返回前十条
		#limit 20,3 20条开始，返回三条数据
		if 1 == page:
			sql += "limit %s"%constants.HOUSE_LIST_PAGE_CAPACITY
		else:
			sql += "limit %s,%s"%((page-1)*constants.HOUSE_LIST_PAGE_CAPACITY.constants.HOUSE_LIST_PAGE_CAPACITY)
 
		logging.debug(sql)
		try:
			res = self.db.query(sql,**sql_params)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR,errmsg="查询出错"))
		data = []
		if res:
			for l in res:
				house = dict(
					house_id = l["hi_house_id"],
					title = l["hi_title"],
					price = l["hi_price"],
					room_count = l["hi_room_count"],
					address = l["hi_address"],
					order_count = l["hi_order_count"],
					avatar = config.image_url_prefix+l["up_avatar"] if l.get("up_avatar") else "",
					image_url = config.image_url_prefix+l["hi_index_image_url"] if l.get("hi_index_image_url") else ""

							 )
				data.append(house)
		self.write(dict(errcode=RET.OK,errmsg="OK",data=data,total_page=total_page))

class HouseListRedisHandler(BaseHandler):
	"""使用了缓存的房源列表页面"""
	
	def get(self):

		"""get方式用来获取数据库数据，本身的逻辑不会对数据库数据产生影响"""
		"""
		传入参数说明
		start_date 用户查询的起始时间 sd     非必传   ""          "2017-02-28"
		end_date    用户查询的终止时间 ed    非必传   ""
		area_id     用户查询的区域条件   aid 非必传   ""
		sort_key    排序的关键词     sk     非必传   "new"      "new" "booking" "price-inc"  "price-des"
		page        返回的数据页数     p     非必传   1
		"""
		
		start_date = self.get_argument("sd","")
		end_date = self.get_argument("ed","")
		area_id = self.get_argument("aid","")
		sort_key = self.get_argument("sk","new")
		page = self.get_argument("p","1")
		try:
			redis_key = "houses_%s_%s_%s_%s"%(start_date,end_date,area_id,sort_key)
			res = self.redis.hget(redis_key,page)
			
		except Exception as e:
			logging.error(e)
			res = None
		if res:
			# logging.info("hit redis")
			return self.write(res)


		#数据查询

		sql = "select distinct hi_title,hi_house_id,hi_price,hi_room_count,hi_address,hi_order_count,up_avatar,hi_index_image_url,hi_ctime from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id left join ih_order_info on hi_house_id=oi_house_id"

		sql_total_count = "select count(distinct hi_house_id) count from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id left join ih_order_info on hi_house_id=oi_house_id"

		sql_where = [] #用来保存sql语句的where条件
		sql_params = {} #用来保存sql查询所需的动态数据

		if start_date and end_date:
			sql_part = "((oi_begin_date>%(end_date)s or oi_end_date<%(start_date)s) " \
					   "or (oi_begin_date is null and oi_end_date is null))"
			sql_where.append(sql_part)
			sql_params["start_date"] = start_date
			sql_params["end_date"] = end_date
		elif start_date:
			sql_part = "(oi_end_date<%(start_date)s or (oi_begin_date is null and oi_end_date is null))"
			sql_where.append(sql_part)
			sql_params["start_date"] = start_date
		elif end_date:
			sql_part = "(oi_begin_date>%(end_date)s or (oi_begin_date is null and oi_end_date is null))"
			sql_where.append(sql_part)
			sql_params["end_date"] = end_date

		if area_id:
			sql_part = "hi_area_id=%(area_id)s"
			sql_where.append(sql_part)
			sql_params["area_id"] = area_id

		if sql_where:
			sql += " where "
			sql += " and ".join(sql_where)

		 # 有了where条件，先查询总条目数
		try:
			ret = self.db.get(sql_total_count, **sql_params)
		except Exception as e:
			logging.error(e)
			total_page = -1
		else:
			total_page = int(math.ceil(ret["count"] / float(constants.HOME_LIST_PAGE_CAPACITY)))
			page = int(page)
			if page>total_page:
				return self.write(dict(errcode=RET.OK, errmsg="OK", data=[], total_page=total_page))

		# 排序
		if "new" == sort_key: # 按最新上传时间排序
			sql += " order by hi_ctime desc"
		elif "booking" == sort_key: # 最受欢迎
			sql += " order by hi_order_count desc"
		elif "price-inc" == sort_key: # 价格由低到高
			sql += " order by hi_price asc"
		elif "price-des" == sort_key: # 价格由高到低
			sql += " order by hi_price desc"

		# 分页
		# limit 10 返回前10条
		# limit 20,3 从20条开始，返回3条数据
		if 1 == page:
			sql += " limit %s" % (constants.HOME_LIST_PAGE_CAPACITY * constants.HOUSE_LIST_PAGE_CACHE_NUM)
		else:
			sql += " limit %s,%s" % ((page-1)*constants.HOME_LIST_PAGE_CAPACITY, constants.HOME_LIST_PAGE_CAPACITY * constants.HOUSE_LIST_PAGE_CACHE_NUM)

		logging.debug(sql)
		try:
			ret = self.db.query(sql, **sql_params)
		except Exception as e:
			logging.error(e)
			return self.write(dict(errcode=RET.DBERR, errmsg="查询出错"))
		data = []
		if ret:
			for l in ret:
				house = dict(
					house_id=l["hi_house_id"],
					title=l["hi_title"],
					price=l["hi_price"],
					room_count=l["hi_room_count"],
					address=l["hi_address"],
					order_count=l["hi_order_count"],
					avatar=config.image_url_prefix+l["up_avatar"] if l.get("up_avatar") else "",
					image_url=config.image_url_prefix+l["hi_index_image_url"] if l.get("hi_index_image_url") else ""
				)
				data.append(house)
		
		#对返回的多页面数据进行分页处理
		#首先取出用户想要获取的page页的数据
		current_page_data = data[:constants.HOME_LIST_PAGE_CAPACITY]
		house_data = {}
		house_data[page] = json.dumps(dict(errcode=RET.OK,errmsg="OK",data=current_page_data,total_page=total_page))

		#将多取出来的数据分页
		i = 1
		while 1:
			page_data = data[i*constants.HOME_LIST_PAGE_CAPACITY:(i+1)*constants.HOME_LIST_PAGE_CAPACITY]
			if not page_data:
				break
			house_data[page+i] = json.dumps(dict(errcode = RET.OK,errmsg="OK",data = page_data,total_page=total_page))
			i += 1
		try:
			redis_key = "houses_%s_%s_%s_%s"%(start_date,end_date,area_id,sort_key)
			self.redis.hmset(redis_key,house_data)
			self.redis.expire(redis_key,constants.REDIS_HOUSE_LIST_EXPIRES_SECONDS)
		except Exception as e:
			logging.error(e)

		self.write(house_data[page])
