# -*- coding: utf-8 -*-
import requests
import random
import logging
from logging.handlers import RotatingFileHandler
from lxml import etree
import os
import threading

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    )
ALISAVERNER_LOGGER = logging.getLogger(__name__)

ALISAVERNER_ROTATING_FILE_HANDLER = RotatingFileHandler('./log/info.log', maxBytes=100 * 1024 * 1024, backupCount=10)
ALISAVERNER_ROTATING_FILE_HANDLER.setLevel(logging.DEBUG)
ALISAVERNER_ROTATING_FILE_HANDLER.setFormatter(logging.Formatter(
    '[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s'))
ALISAVERNER_LOGGER.addHandler(ALISAVERNER_ROTATING_FILE_HANDLER)

user_agent_list = [
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
useragent = random.choice(user_agent_list)
header = {
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

def mkdir(path):
    path = path.strip()
    isExists = os.path.exists(path)
    if not isExists:
        ALISAVERNER_LOGGER.info(u'建了一个名字叫做' + path + u'的文件夹！')
        os.makedirs(os.path.join(".", path))
        return True
    else:
        ALISAVERNER_LOGGER.debug(u'名字叫做' +  path + u'的文件夹已经存在了！')
        return False

def web(url):
    try:
        res = requests.get(url, headers=header, timeout=10)
    except requests.Timeout:
        ALISAVERNER_LOGGER.warn('Get %s failed by Timeout.' % (url))
        return None
    except requests.HTTPError:
        ALISAVERNER_LOGGER.warn('Get %s failed by HTTPError %d.' % (url, res.status_code))
        return None
    except requests.ConnectionError:
        ALISAVERNER_LOGGER.warn('Get %s failed by ConnectionError.' % (url))
        return None
    return res

def download(imgurl, imgdir):
    ALISAVERNER_LOGGER.info('Start to access to img %s.' % (imgurl))
    img_file_name = imgdir + os.path.sep + imgurl.split('/')[-1]
    if os.path.exists(img_file_name):
        ALISAVERNER_LOGGER.info('%s exists.' % (imgurl))
        return None
    img = web(imgurl)
    if img:
        save_img(img, imgdir)
    else:
        ALISAVERNER_LOGGER.warn('Access to %s failed.' % (imgurl))

def save_img(img, img_file_name):
    with open(img_file_name, 'ab') as f:
        f.write(img.content)
        ALISAVERNER_LOGGER.info('save img %s successfully.' % (img.url))



if __name__ == '__main__':
    mainpage = 'http://en.alisaverner.com'
    img_dir = "img" + os.path.sep + "new" + os.path.sep + "alisaverner"
    mkdir(img_dir)
    ALISAVERNER_LOGGER.info('Start to access to %s.' % (mainpage))
    res = web(mainpage)
    if res:
        html = etree.HTML(res.text)
        hrefs = html.xpath('//div[@class="content"]//div[@class="pic"]//@href')
        for href in hrefs:
            url = mainpage + href
            ALISAVERNER_LOGGER.info('Start to access to %s.' % (url))
            res = web(url)
            if res:
                img_html = etree.HTML(res.text)
                imgurls = img_html.xpath('//div[@class="content"]//div[@class="pic"]//@href')
                threads = []
                for imgurl in imgurls:
                    imgsource = mainpage + imgurl
                    t = threading.Thread(target=download, args=(imgsource, img_dir))
                    threads.append(t)
                    t.start()
                for thread in threads:
                    thread.join()
            else:
                ALISAVERNER_LOGGER.warn('Access to %s failed.' % (url))
    else:
        ALISAVERNER_LOGGER.warn('Access to %s failed.' % (mainpage))

