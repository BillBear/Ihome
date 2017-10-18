#coding:utf-8

from CCPRestSDK import REST
import ConfigParser

_accountSid = "8a216da85e7e4bbd015e9e25b3040d7e";
#说明：主账号，登陆云通讯网站后，可在“控制台-应用”中看到开发者主账号ACCOUNT SID

_accountToken = "1acde4995b314baba4f9ea168d492de5";
#说明：主账号token，登陆云通讯网站后，可在控制台-应用看到

_appId = "8a216da85e7e4bbd015e9e25b33d0d82";
#说明：控制台

_serverIP = "app.cloopen.com";
#说明：请求地址，生产环境配置成app.cloopen.com

_serverPort = "8883";
#说明：请求端口，生产环境为8883

_softVersion = "2013-12-26"; #说明：REST API版本保持不变

class _CCP(object):
	def __init__(self):
		self.rest = REST(_serverIP,_serverPort,_softVersion)
		self.rest.setAccount(_accountSid,_accountToken)
		self.rest.setAppId(_appId)


	#单例模式：对一个类而言，只有一个全局唯一的实例
	@classmethod
	def instance(cls):
		#创建一个单例，如果没有生成
		if not hasattr(cls,"_instance"): #判断cls中是否存在_instance实例
			cls._instance = cls()   #创建一个实例
		return cls._instance

	# 发送模板短信
    # @param to  必选参数     短信接收彿手机号码集合,用英文逗号分开
    # @param datas 可选参数    内容数据 两个参数 验证码内容和时效
    # @param tempId 必选参数    模板Id
	def sendTemplateSMS(self,to,datas,tempID):
		return self.rest.sendTemplateSMS(to, datas, tempID)

ccp = _CCP.instance()

if __name__ == '__main__':
	ccp.sendTemplateSMS('15707958952',['1234',5],1)