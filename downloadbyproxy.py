# coding:utf-8

import requests
import re
import random
import time


class downloadbyproxy:
    def __init__(self):
        """
        self.iplist = []
        html = requests.get("http://haoip.cc/tiqu.htm")
        ips = re.findall(r'r/>(.*?)<b', html.text, re.S)
        for ip in ips:
            i = re.sub(r'\n', '', ip).strip()
            self.iplist.append(i)
        """

        #"""
        self.iplist = []
        # 代理数据抓取
        # html = requests.get("http://11:9527/proxies")
        # ips = re.findall(r'(.*?)\n', html.text, re.S)
        # for ip in ips:
        #     i = ip.strip()
        #     self.iplist.append(i)
        #"""

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
            "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
        ]

    def get(self, url, timeout,proxy=None,retries=5):

        UA = random.choice(self.user_agent_list)
        """
        从self.user_agent_list中随机取出一个字符串，用于构造一个header

        headers = {
            "User-Agent": UA,
            "Host": url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Referer": url
        }
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            #"Host": "www.kuaidaili.com",
            #"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            #"Accept-Language": "zh-CN,zh;q=0.8",
            #"Accept-Encoding": "gzip, deflate, sdch",
            "Referer": url,
            #"Connection": "keep-alive",
            #"Cache-Control": "max-age=0",
            #"Upgrade - Insecure - Requests": "1",
        }

        if proxy == None:
            try:
                return requests.get(url, headers=headers,timeout=timeout)
            except:
                if retries > 0:
                    print u'获取网页出错，10S后将获取倒数第：', retries, u'次'
                    time.sleep(10)
                    return self.get(url, timeout, None,retries-1)
                else:
                    print u'使用代理ip抓取'
                    time.sleep(10)
                    ip = ''.join(str(random.choice(self.iplist)).strip())
                    proxy = {
                        'http': ip
                    }
                    return self.get(url, timeout, proxy,20)

        else:
            """
            ip = ''.join(str(random.choice(self.iplist)).strip())
            proxy = {
                'http': ip
            }
            """
            try:
                return requests.get(url, headers=headers, proxies=proxy,timeout=timeout)
            except:
                if retries > 0:
                    print u'获取网页出错，10S后将换代理尝试倒数第：', retries, u'次'
                    time.sleep(10)
                    ip = ''.join(str(random.choice(self.iplist)).strip())
                    proxy = {
                        'http': ip
                    }
                    return self.get(url, timeout, proxy,retries-1)
                else:
                    print u'停止使用代理ip抓取'
                    time.sleep(10)
                    return self.get(url, timeout)

request = downloadbyproxy()

if __name__ == '__main__':

    test = downloadbyproxy()
    print (test.get("http://www.baidu.com",10,proxy={'http': '1.1.1.1:11'}))

    """
    iplist = []
    html = requests.get("http://2:222/proxies")
    ips = re.findall(r'(.*?)\n', html.text, re.S)
    for ip in ips:
        i = ip.strip()
        iplist.append(i)
    print iplist
    """