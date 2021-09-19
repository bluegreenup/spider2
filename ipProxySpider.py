# coding:utf-8
import requests
import re
import random
import time
# import urllib2
# import cookielib
#import execjs
from proxyschdule import proxyschdule
import logging
import sys
from logging.handlers import RotatingFileHandler

LOG_FORMAT = '[%(levelname)s] %(asctime)s [name:%(name)s] [%(filename)s line:%(lineno)d] [func:%(funcName)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
#basicConfig会默认创建一个StreamHandler，并且这个handler不能在后续单独修改设置。basic里面的设置是对整个logging的设置，后续的其他logging会继承设置
# logging.basicConfig(level=logging.INFO,
#                     format=LOG_FORMAT,
#                     datefmt=DATE_FORMAT,
#                     stream=sys.stdout,
#                     )
ROOTLOOGER = logging.getLogger()
ROOTLOOGER.setLevel(logging.INFO)

ipProxySpiderLog = logging.getLogger(__name__)
IPPROXYSPIDER_STREAM_HANDLER = logging.StreamHandler(sys.stdout)
IPPROXYSPIDER_STREAM_HANDLER.setLevel(logging.INFO)
IPPROXYSPIDER_STREAM_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))
ipProxySpiderLog.addHandler(IPPROXYSPIDER_STREAM_HANDLER)
IPPROXYSPIDER_ROTATING_FILE_HANDLER = RotatingFileHandler('./log/info.log', maxBytes=100 * 1024 * 1024, backupCount=10)
IPPROXYSPIDER_ROTATING_FILE_HANDLER.setLevel(logging.INFO)
IPPROXYSPIDER_ROTATING_FILE_HANDLER_FORMAT = logging.Formatter(LOG_FORMAT)
IPPROXYSPIDER_ROTATING_FILE_HANDLER.setFormatter(IPPROXYSPIDER_ROTATING_FILE_HANDLER_FORMAT)
ipProxySpiderLog.addHandler(IPPROXYSPIDER_ROTATING_FILE_HANDLER)

class ipProxySpider:
    def __init__(self):
        self.user_agent_list = [
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
            "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
            "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
        ]
        self.spiderproxy = proxyschdule()
        self.proxylist = self.spiderproxy.getIpList()
        self.header = self.headersPrepare('')
        self.httpproxy = {}
        self.cookie = {}

    def headersPrepare(self, url):
        """
        从self.user_agent_list中随机取出一个字符串，用于构造一个header
        """
        useragent = random.choice(self.user_agent_list)
        headers = {
            "User-Agent": useragent,
            # "Host": url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            #"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "zh-CN,zh;q=0.8",
            #"Accept-Encoding": "gzip, deflate, br",
            # "Referer": url,
            "Connection": "keep-alive",
            # "Cache-Control":"max-age=0",
            "Upgrade-Insecure-Requests": "1"
        }
        return headers


    def postHtml(self, url, data):
        response = requests.post(url, data=data, headers=self.header)
        #print response.content
        #print response.status_code
        return response

    def get_html_with_cookie(self, url, cookie):
        response = requests.get(url, headers=self.header, cookies=cookie)
        #print response.status_code
        #print response.content
        return response

    def getHtml(self, url, timeout=10, retries=1, proxy=True):
        """逻辑为先使用代理抓取，多次失败后用本机直接抓取"""
        #proxy = {'http':ip}
        if not proxy:
            if self.header:
                pass
            else:
                self.header = self.headersPrepare(url)

            # request = urllib2.Request(url, headers=header)
            try:
                # response = urllib2.urlopen(request, timeout=timeout)
                # html = response.read().decode('utf-8')
                # return html
                response = requests.get(url, headers=self.header, timeout=timeout)
                #print response.status_code
                #print response.content
                if response.status_code >= 500:
                    ipProxySpiderLog.warn('web spider gets return code :'+str(response.status_code))
                    if url.find('kuaidaili.com') != -1:
                        self.cookie = self.kuaidailiJS(response)
                        if self.cookie != {}:
                            ipProxySpiderLog.info('get cookie from kuaidaili successfully.')
                            response = requests.get(url, headers=self.header, timeout=timeout,cookies=self.cookie)
                        else:
                            ipProxySpiderLog.error('get cookie from kuaidaili failed!')
                            return None

                    if url.find('66ip.cn') != -1:
                        # self.cookie = self.kuaidailiJS(response)
                        # if self.cookie != {}:
                        #     ipProxySpiderLog.info('get cookie from kuaidaili successfully.')
                        #     response = requests.get(url, headers=self.header, timeout=timeout,cookies=self.cookie)
                        # else:
                        #     ipProxySpiderLog.error('get cookie from kuaidaili failed!')
                        #     return None
                        first_html = response.content.decode('utf-8')
                        print first_html


                return response
            except:
                if retries > 0:
                    #print u'获取网页出错，10S后将获取倒数第：', retries, u'次'
                    ipProxySpiderLog.warn('can\'t spider web，try last：'+ str(retries) + ' times.')
                    time.sleep(self.getRandomInt(5,10))
                    return self.getHtml(url, retries=retries - 1, proxy=False)
                else:
                    #print u'使用代理ip抓取'
                    #ipProxySpiderLog.info('try to use proxy ip to spider again.')
                    #time.sleep(self.getRandomInt(5,10))
                    #由于换成代理爬，去除cookie
                    #if self.cookie:
                    #   self.cookie = {}
                    #return self.getHtml(url, retries=self.getRandomInt(), proxy=True)

                    #多次使用服务器ip尝试仍失败，放弃抓取该页面
                    #如果有绑定的cookie也要释放掉
                    if self.cookie:
                        self.cookie = {}
                    return None

        else:

            header = self.headersPrepare(url)

            if self.httpproxy:
                httpproxy = self.httpproxy
            else:
                if self.proxylist:
                    ip = ''.join(str(random.choice(self.proxylist)).strip())
                    # print ip
                    httpproxy = {
                        'http': ip
                    }
                    self.httpproxy = httpproxy
                else:
                    ipProxySpiderLog.warn('proxy ip list is empty,try to refresh it.')
                    self.spiderproxy.refreshIpList()
                    self.proxylist = self.spiderproxy.getIpList()
                    if self.proxylist:
                        ip = ''.join(str(random.choice(self.proxylist)).strip())
                        httpproxy = {
                            'http': ip
                        }
                        self.httpproxy = httpproxy
                    else:
                        ipProxySpiderLog.warn('refresh proxy ip list failed! use local ip to spider.')
                        return self.getHtml(url, retries=retries, proxy=False)

            try:
                #proxy_handler = urllib2.ProxyHandler({"http": proxy})
                #opener = urllib2.build_opener(proxy_handler)
                #urllib2.install_opener(opener)

                #request = urllib2.Request(url, headers=header)
                #request.set_proxy(proxy,'http')
                #response = urllib2.urlopen(request, timeout=timeout)
                #html = response.read().decode('utf-8')
                #return html
                response = requests.get(url, headers=header, proxies=httpproxy, timeout=timeout)
                if response.status_code >= 500:
                    ipProxySpiderLog.warn('web spider gets return code :'+str(response.status_code))
                    if url.find('kuaidaili.com') != -1:
                        self.cookie = self.kuaidailiJS(response)
                        if self.cookie != {}:
                            ipProxySpiderLog.info('get cookie from kuaidaili successfully.')
                            response = requests.get(url, headers=header, proxies=httpproxy, timeout=timeout,cookies=self.cookie)
                            #print response
                        else:
                            ipProxySpiderLog.error('get cookie from kuaidaili failed!')
                            return None

                # 由于400返回表明无法获取网页，但是并不会进入except段，因此需要在获得400后再次尝试
                if response.status_code >= 400:
                    if httpproxy['http'] in self.proxylist:
                        ipProxySpiderLog.info('remove useless proxy: ' + httpproxy['http'] + ' from proxy list.')
                        self.proxylist.remove(httpproxy['http'])
                        self.spiderproxy.deleteProxy(httpproxy['http'])
                    else:
                        ipProxySpiderLog.warn(httpproxy['http'] + ' is not in the proxy list.')

                    if self.cookie:
                        self.cookie = {}
                    if self.httpproxy:
                        self.httpproxy = {}

                    if retries > 0:
                        # print u'获取网页出错，10S后将换代理尝试倒数第：', retries, u'次'
                        ipProxySpiderLog.warn(
                            'can\'t spider web，using another proxy to try last：' + str(retries) + ' times')
                        # time.sleep(self.getRandomInt(5, 10))
                        return self.getHtml(url, retries=retries - 1, proxy=True)
                    else:
                        # print u'停止使用代理ip抓取'
                        ipProxySpiderLog.info('stop using proxy ip to spider.')
                        # time.sleep(self.getRandomInt(5,10))
                        return self.getHtml(url, retries=self.getRandomInt(3, 7), proxy=False)

                return response
            except :
                if httpproxy['http'] in self.proxylist:
                    ipProxySpiderLog.info('remove useless proxy: ' + httpproxy['http'] + ' from proxy list.')
                    self.proxylist.remove(httpproxy['http'])
                    self.spiderproxy.deleteProxy(httpproxy['http'])
                else:
                    ipProxySpiderLog.warn(httpproxy['http'] + ' is not in the proxy list.')
                # time.sleep(self.getRandomInt(5, 10))
                # 由于换代理爬，去除cookie
                if self.cookie:
                    self.cookie = {}
                # 由于换代理爬，去除老的代理
                if self.httpproxy:
                    self.httpproxy = {}

                if retries > 0:
                    #print u'获取网页出错，10S后将换代理尝试倒数第：', retries, u'次'
                    ipProxySpiderLog.warn('can\'t spider web，using another proxy to try last：' + str(retries) + ' times')
                    # time.sleep(self.getRandomInt(5, 10))
                    return self.getHtml(url, retries=retries - 1,proxy=True)
                else:
                    #print u'停止使用代理ip抓取'
                    ipProxySpiderLog.info('stop using proxy ip to spider.')
                    # time.sleep(self.getRandomInt(5,10))
                    return self.getHtml(url, retries=self.getRandomInt(3,7),proxy=False)

        return None

    def getRandomInt(self,start=10,end=20):
        return random.randint(start, end)

    def kuaidailiJS(self,response):
        #print 'js'
        ipProxySpiderLog.info('web is kuaidaili,try to get cookie.')
        first_html = response.content.decode('utf-8')
        #print first_html
        js_string = ''.join(re.findall(r'(function .*?)</script>', first_html))

        # 提取其中执行JS函数的参数
        js_func_arg = re.findall(r'setTimeout\(\"\D+\((\d+)\)\"', first_html)[0]
        js_func_name = re.findall(r'function (\w+)', js_string)[0]

        # 修改JS函数，使其返回Cookie内容
        js_string = js_string.replace('eval("qo=eval;qo(po);")', 'return po')

        func = execjs.compile(js_string)

        cookie_str = func.call(js_func_name, js_func_arg)

        #print cookie_str

        clearance = cookie_str.replace("document.cookie='", "").split(';')[0]
        #dicttype cookie
        cookie =  {clearance.split('=')[0]: clearance.split('=')[1]}

        print cookie
        return cookie

    def getCookie(self):
        cookie = self.cookie
        self.cookie = {}
        return cookie


if __name__ == '__main__':
    test = ipProxySpider()
    cookie = {'csrftoken': '1', 'urlgen': '"{222: 222}:555"'}
    #html = test.getHtml("https://www.instagram.com/kingjames", timeout=10, retries=1, proxy=True)
    html = test.get_html_with_cookie("https://www.instagram.com/p/B-kVcE6KKBN/?taken-by=anechkaannn", cookie=cookie)
    if html:
        print html.text
        print {c.name: c.value for c in html.cookies}
    else:
        print 'failed!!'