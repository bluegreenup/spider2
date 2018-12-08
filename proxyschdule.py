# coding:utf-8
import requests
import re
import random
import time
#import urllib2
#import MySQLdb

#from gevent import monkey
#monkey.patch_all()
#from gevent.pool import Pool

import logging
import sys
from logging.handlers import RotatingFileHandler

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    )

proxyschduleLog = logging.getLogger(__name__)
proxyschduleRthandler = RotatingFileHandler('./log/info.log', maxBytes=100 * 1024 * 1024, backupCount=10)
proxyschduleRthandler.setLevel(logging.INFO)
proxyschduleRotatingFileHandlerFormat = logging.Formatter(
    '[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s')
proxyschduleRthandler.setFormatter(proxyschduleRotatingFileHandlerFormat)
proxyschduleLog.addHandler(proxyschduleRthandler)


class proxyschdule:
    def __init__(self):
        self.iplist = []
        self._host = "localhost"
        self._port = 11002
        self._user = "xxx"
        self._passwd = "xxx"
        self._db = "test"
        self._table = "IpProxy"
        self._charset = "gbk"
        self._timeout = 15

        # self.refreshIpList()

    def getIpList(self):
        #return self.iplist
        return ['127.0.0.1:9666']

    """删除数据库中无效的代理ip"""
    def deleteProxy(self,proxy):
        #proxy = 'xxx:xxx'
        try:
            conn = MySQLdb.connect(host=self._host, port=self._port, user=self._user, passwd=self._passwd, db=self._db,
                                   charset=self._charset,
                                   connect_timeout=self._timeout)
            cursor = conn.cursor()

            sql = """
            delete from %s where proxy = '%s';
            """ % (self._table, proxy)

            proxyschduleLog.info("operation sql: %s" % sql)
            cursor.execute(sql)
            proxyschduleLog.info("affected row num: %d" % cursor.rowcount)

            if cursor.rowcount != 0:
                commitFlag = 1
                conn.commit()

            commitFlag = 0
            cursor.close()
            conn.close()

        except:
            proxyschduleLog.error(
                'sql operation in ' + self._host + ' ' + self._db + '.' + self._table + ' has error in proxyschdule.')
            alarm = 'sql operation in ' + self._host + ' ' + self._db + '.' + self._table + ' has error in proxyschdule.'
            # os.system('bash ./rsyncSmsAlarm.sh ' + alarm)
            if commitFlag == 1:
                conn.rollback()


    """从数据库获取代理ip"""
    def refreshIpList(self):
        self.iplist = []
        try:
            conn = MySQLdb.connect(host=self._host, port=self._port, user=self._user, passwd=self._passwd, db=self._db,
                                   charset=self._charset,
                                   connect_timeout=self._timeout)
            cursor = conn.cursor()

            sql = """select * from %s limit 300;""" % (self._table)

            proxyschduleLog.info("operation sql: %s" % sql)
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()
            conn.close()

        except:
            proxyschduleLog.error(
                'sql operation in ' + self._host + ' ' + self._db + '.' + self._table + ' has error in proxyschdule.')
            alarm = 'sql operation in ' + self._host + ' ' + self._db + '.' + self._table + ' has error in proxyschdule.'
            # os.system('bash ./rsyncSmsAlarm.sh ' + alarm)
            self.iplist = []
            return

        for row in data:
            self.iplist.append(row[0])



    """
    def deleteProxy(self,proxy):
        #proxy = 'xxx:xxx'
        if proxy in self.iplist:
            proxyschduleLog.info('Remove '+ proxy +' from proxy list.')
            self.iplist.remove(proxy)
        else:
            proxyschduleLog.warn(proxy+' is not in the proxy list.')

    def refreshIpList(self):
        self.iplist = []
        try:
            html = requests.get("http://22:9527/proxies")
            ips = re.findall(r'(.*?)\n', html.text, re.S)
            #request = urllib2.Request("http://126:22/proxies")
            #response = urllib2.urlopen(request)
            #html = response.read().decode('utf-8')
            #ips = re.findall(r'(.*?)\n', html, re.S)
            for ip in ips:
                i = ip.strip()
                self.iplist.append(i)
        except:
            proxyschduleLog.error('Get proxies from xxx failed!')
    """

    def testProxyValid(self,proxy,url):
        #proxy = {'http':ip}
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Referer": url,
            "Connection": "keep-alive"
            #"Cache-Control": "max-age=0",
            #"Upgrade - Insecure - Requests": "1",
        }
        """
        request = urllib2.Request(url, headers=header)
        request.set_proxy(proxy, 'http')
        try:
            html = urllib2.urlopen(request, timeout=15)
            # print html.read()
            if html:
                #print 'success'
                return True
            else:
                #print 'failed'
                return False
        except Exception as e:
            #print 'error'
            return False
        """
        try:
            result = requests.get(url, headers=header, proxies=proxy,timeout=10)
        except:
            #print proxy,"failed"
            return False
        #print proxy,"success"
        #print type(result.status_code)
        if (result.status_code >= 200 and result.status_code <= 399):
            #print '200-399'
            return True
        else:
            #print '>=400'
            return False
        #print result.status_code
        #return True




"""
class IsActivePorxyIP(object):

    def __init__(self, url):
        self.testurl = url
        self.is_active_proxy_ip = []

    def probe_proxy_ip(self, proxy_ip):

        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Referer": self.testurl,
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Upgrade - Insecure - Requests": "1",
        }
        request = urllib2.Request(url, headers=header)
        request.set_proxy(proxy_ip, 'http')
        print 'test proxy:',proxy_ip
        try:
            html = urllib2.urlopen(request,timeout=15)
            # print html.read()
            if html:
                self.is_active_proxy_ip.append(proxy_ip)
                print 'success'
                return True
            else:
                print 'failed'
                return False
        except Exception as e:
            print 'error'
            return False


if __name__ == '__main__':
    url = 'http://www.kuaidaili.com/free/inha'

    p_isactive = IsActivePorxyIP(url)
    proxy_ip_lst = proxyGetter().getIpList()
    print len(proxy_ip_lst)

    # 异步并发
    pool = Pool(20)
    pool.map(p_isactive.probe_proxy_ip, proxy_ip_lst)
    print len(p_isactive.is_active_proxy_ip)
    print p_isactive.is_active_proxy_ip
"""
if __name__ == '__main__':
    test = proxyschdule()
    print test.getIpList()
    test.refreshIpList()
    print test.getIpList()
    test.testProxyValid({'http': '149.56.89.109:3128'},'http://www.kuaidaili.com/free/inha/2')
    print len([])
    test.deleteProxy("103.63.159.133:8080")
    """
    for item in test.getIpList():
        ip = ''.join(str(item).strip())
        proxy = {
            'http': ip
        }
        test.testProxyValid(proxy, "http://www.kuaidaili.com/free/inha/2")
    """