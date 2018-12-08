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
# import sys
from logging.handlers import RotatingFileHandler

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    )

ipProxySpiderLog = logging.getLogger(__name__)
ipProxySpiderRthandler = RotatingFileHandler('./log/info.log', maxBytes=100 * 1024 * 1024, backupCount=10)
ipProxySpiderRthandler.setLevel(logging.INFO)
ipProxySpiderRotatingFileHandlerFormat = logging.Formatter(
    '[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s')
ipProxySpiderRthandler.setFormatter(ipProxySpiderRotatingFileHandlerFormat)
ipProxySpiderLog.addHandler(ipProxySpiderRthandler)

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
        self.header = {}
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
            #"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
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
                    # if url.find('kuaidaili.com') != -1:
                    #     self.cookie = self.kuaidailiJS(response)
                    #     if self.cookie != {}:
                    #         ipProxySpiderLog.info('get cookie from kuaidaili successfully.')
                    #         response = requests.get(url, headers=self.header, timeout=timeout,cookies=self.cookie)
                    #     else:
                    #         ipProxySpiderLog.error('get cookie from kuaidaili failed!')
                    #         return None

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
                    #self.spiderproxy.refreshIpList()
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
                    # if url.find('kuaidaili.com') != -1:
                    #     self.cookie = self.kuaidailiJS(response)
                    #     if self.cookie != {}:
                    #         ipProxySpiderLog.info('get cookie from kuaidaili successfully.')
                    #         response = requests.get(url, headers=header, proxies=httpproxy, timeout=timeout,cookies=self.cookie)
                    #         #print response
                    #     else:
                    #         ipProxySpiderLog.error('get cookie from kuaidaili failed!')
                    #         return None

                # 由于400返回表明无法获取网页，但是并不会进入except段，因此需要在获得400后再次尝试
                if response.status_code >= 400:
                    if httpproxy['http'] in self.proxylist:
                        ipProxySpiderLog.info('remove useless proxy: ' + httpproxy['http'] + ' from proxy list.')
                        self.proxylist.remove(httpproxy['http'])
                        #self.spiderproxy.deleteProxy(httpproxy['http'])
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
                        # 使用代理的环境下抓举，使用本地ip一定无法抓取，顾不用本地的ip进行多余的尝试
                        # return self.getHtml(url, retries=self.getRandomInt(3, 7), proxy=False)

                return response
            except :
                if httpproxy['http'] in self.proxylist:
                    # print('except')
                    ipProxySpiderLog.info('remove useless proxy: ' + httpproxy['http'] + ' from proxy list.')
                    self.proxylist.remove(httpproxy['http'])
                    #self.spiderproxy.deleteProxy(httpproxy['http'])
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
                    # 使用代理的环境下抓举，使用本地ip一定无法抓取，顾不用本地的ip进行多余的尝试
                    # return self.getHtml(url, retries=self.getRandomInt(3, 7), proxy=False)

        return None

    def getRandomInt(self,start=10,end=20):
        return random.randint(start, end)

    # def kuaidailiJS(self,response):
    #     #print 'js'
    #     ipProxySpiderLog.info('web is kuaidaili,try to get cookie.')
    #     first_html = response.content.decode('utf-8')
    #     #print first_html
    #     js_string = ''.join(re.findall(r'(function .*?)</script>', first_html))
    #
    #     # 提取其中执行JS函数的参数
    #     js_func_arg = re.findall(r'setTimeout\(\"\D+\((\d+)\)\"', first_html)[0]
    #     js_func_name = re.findall(r'function (\w+)', js_string)[0]
    #
    #     # 修改JS函数，使其返回Cookie内容
    #     js_string = js_string.replace('eval("qo=eval;qo(po);")', 'return po')
    #
    #     func = execjs.compile(js_string)
    #
    #     cookie_str = func.call(js_func_name, js_func_arg)
    #
    #     #print cookie_str
    #
    #     clearance = cookie_str.replace("document.cookie='", "").split(';')[0]
    #     #dicttype cookie
    #     cookie =  {clearance.split('=')[0]: clearance.split('=')[1]}
    #
    #     print cookie
    #     return cookie

    def getCookie(self):
        cookie = self.cookie
        self.cookie = {}
        return cookie


if __name__ == '__main__':
    test = ipProxySpider()

    html = test.getHtml("http://www.baidu.com", timeout=10, retries=1, proxy=True)
    if html:
        print html.text
    else:
        print 'failed!!'