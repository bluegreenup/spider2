# coding:utf-8
import logging
import xml.dom.minidom
import re
import os
import sys
import concurrent.futures
import random
import time
import json

from logging.handlers import RotatingFileHandler

from ipProxySpider import ipProxySpider
from fileclean import getDownloadedFileName
from fileclean import INSTAGRAMDOWNLOADDIR

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

IMGKOA_LOGGER = logging.getLogger(__name__)
IMGKOA_STREAM_HANDLER = logging.StreamHandler(sys.stdout)
IMGKOA_STREAM_HANDLER.setLevel(logging.WARN)
IMGKOA_STREAM_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))
IMGKOA_LOGGER.addHandler(IMGKOA_STREAM_HANDLER)
IMGKOA_ROTATING_FILE_HANDLER = RotatingFileHandler('./log/info.log', maxBytes=100 * 1024 * 1024, backupCount=10)
IMGKOA_ROTATING_FILE_HANDLER.setLevel(logging.INFO)
IMGKOA_ROTATING_FILE_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))
IMGKOA_LOGGER.addHandler(IMGKOA_ROTATING_FILE_HANDLER)

QUERY_HASH_LIST = ['e7e2f4da4b02303f74f0841279e52d76', 'c9100bf9110dd6361671f113dd02e7d6', '2c5d4d8b70cad329c4a6ebe3abb6eedd']

COOKIE = False

def get_prey_list():
    file = "./conf/instagram.xml"
    preylist = []
    try:
        domTree = xml.dom.minidom.parse(file)
    except:
        IMGKOA_LOGGER.error("Can't open Instagram xml file!")
        return preylist

    collection = domTree.documentElement
    nodes = collection.getElementsByTagName("html")
    for node in nodes:
        catalogue = node.getElementsByTagName("catalogue")[0].childNodes[0].data
        # print ("catalogue: %s" % catalogue)
        catalogue_reg = node.getElementsByTagName("cataloguereg")[0].childNodes[0].data
        # print ("catalogue_reg: %s" % catalogue_reg)
        page = node.getElementsByTagName("page")[0].childNodes[0].data
        # print ("page: %s" % page)
        next_page = node.getElementsByTagName("nextpage")[0].childNodes[0].data
        # print ("next_page: %s" % next_page)
        page_reg = node.getElementsByTagName("pagereg")[0].childNodes[0].data
        # print ("page_reg: %s" % page_reg)
        prey = SpiderPrey()
        prey.catalogue = catalogue
        prey.catalogue_reg = catalogue_reg
        prey.page = page
        prey.next_page = next_page
        prey.page_reg = page_reg
        preylist.append(prey)
    return preylist


def spider_mutile_cpu(func, preylist, next_curosr_num):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for prey in preylist:
            executor.submit(func, prey, next_curosr_num)


def use_mutile_cpu(func, preylist):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for prey in preylist:
            executor.submit(func, prey)


def spider_one_imgkoa_blogger(prey, next_curosr_num=0):
    spider = ipProxySpider()
    blogger = prey.page.split('/')[-1]
    url = 'https://www.imgkoa.com/zh-hant/profile/' + blogger
    html = get_html(url, spider)
    # self.batch_fetch_web()
    if html:
        IMGKOA_LOGGER.info(blogger + ': main page ' + url)
        # print html.content
        # re.S匹配换行符 可以多行匹配

        short_code_list = re.findall('<a href=\"/zh-hant/post/([^/]+?)/', html.content, re.S)
        #print list(set(short_code_list))

        detail_html_list = []

        video_path = "video" + os.path.sep + blogger
        mkdir(video_path)
        img_path = "img" + os.path.sep + blogger
        mkdir(img_path)

        for shortcode in list(set(short_code_list)):
            detail_html_list.append("https://www.imgkoa.com/zh-hant/post/" + shortcode)
        # print detail_html_list

        for detail_html in detail_html_list:
            # detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=False)
            # detail_html_content = spider.get_html_with_cookie(detail_html, cookie)
            detail_html_content = get_html(detail_html, spider)
            # print detail_html_content.content
            if detail_html_content:
                IMGKOA_LOGGER.info(blogger + ': detail page ' + detail_html)

                downs = re.findall('<a class=\"downbtn\" href=\"([^\"]+?)&dl=', detail_html_content.content, re.S)
                #print(downs)

                if not downs:
                    IMGKOA_LOGGER.warn(blogger + ': Fail to get down(s) on ' + detail_html)
                    continue

                videos = []
                imgs = []
                for down in downs:
                    if '_n.jpg?_nc' in down:
                        imgs.append(down)
                    if '_n.mp4?_nc' in down:
                        videos.append(down)

                if videos:
                    IMGKOA_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
                    save_video(video_path, videos)
                if imgs:
                    IMGKOA_LOGGER.info(blogger + ': images ' + ' '.join(imgs))
                    save_img(img_path, imgs)
            else:
                IMGKOA_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)

        userid = re.findall('<input type="hidden" name="userid" value="(\d+)\">', html.content, re.S)[0]
        # print userid
        next = re.findall('class="more_btn" data-next="([^\"]+?)\">', html.content, re.S)[0]
        # print(next)
        count = 0

        while count < next_curosr_num:
            count += 1
            # print "next cursor:" + str(count)
            IMGKOA_LOGGER.info(blogger + ': next cursor:' + str(count))

            # https://api.imgkoa.com/posts?userid=19410587&next=QVFDSTN3dkVXQnZ5eDNDZU1wblZOc3JrdWlNMTZJYkI2NExOM1JSa201anUxbWZyTEFlOF9PLVpnTUVvMTJzd2k2SUt5X3R1VkdHQTAwZUFSRXE3TFBHWQ%3D%3D&hl=zh-hant
            next_page = "https://api.imgkoa.com/posts?userid=" + str(userid) + "&next=" + str(next) + "&hl=zh-hant"
            # print next_page
            # nextHtml = spider.getHtml(next_page, timeout=10, retries=2, proxy=True)
            # nextHtml = spider.get_html_with_cookie(next_page, cookie)
            html = get_html(next_page, spider)
            #print(html.content)

            if html:
                IMGKOA_LOGGER.info(blogger + ': next cursor page ' + next_page)
                short_code_list = re.findall('\"shortcode\":\"(\d+?)\"', html.content, re.S)
                #print list(set(short_code_list))

                detail_html_list = []

                for shortcode in list(set(short_code_list)):
                    detail_html_list.append("https://www.imgkoa.com/zh-hant/post/" + shortcode)
                # print detail_html_list

                for detail_html in detail_html_list:
                    # detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=False)
                    # detail_html_content = spider.get_html_with_cookie(detail_html, cookie)
                    detail_html_content = get_html(detail_html, spider)
                    # print detail_html_content.content
                    if detail_html_content:
                        IMGKOA_LOGGER.info(blogger + ': detail page ' + detail_html)

                        downs = re.findall('<a class=\"downbtn\" href=\"([^\"]+?)&dl=', detail_html_content.content,
                                           re.S)
                        #print(downs)

                        if not downs:
                            IMGKOA_LOGGER.warn(blogger + ': Fail to get down(s) on ' + detail_html)
                            continue

                        videos = []
                        imgs = []
                        for down in downs:
                            if '_n.jpg?_nc' in down:
                                imgs.append(down)
                            if '_n.mp4?_nc' in down:
                                videos.append(down)

                        if videos:
                            IMGKOA_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
                            save_video(video_path, videos)
                        if imgs:
                            IMGKOA_LOGGER.info(blogger + ': images ' + ' '.join(imgs))
                            save_img(img_path, imgs)
                    else:
                        IMGKOA_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)

                if 'has_next":true' in html.content:
                    next = re.findall('\"next\":\"([^\"]+?)\"', html.content, re.S)[0]
                    #print(next)
                elif 'has_next":false' in html.content:
                    IMGKOA_LOGGER.info(blogger + ': End of next cursor.' + next_page)
                    break
                else:
                    IMGKOA_LOGGER.warn(blogger + ': Fail to get ' + str(count) + ' cursor\'s next cursor.' + next_page)
                    break
            else:
                # print 'Get ' + prey.page + ' next cursor ' + str(count) + ' failed!!'
                IMGKOA_LOGGER.warn(blogger + ': Fail to get ' + str(count) + ' cursor ' + next_page)
                break

    else:
        # print 'Get ' + prey.page + ' failed!!'
        IMGKOA_LOGGER.warn(blogger + ': Fail to get main page ' + url)


def spider_one_imgkoa_blogger_full(prey):
    spider = ipProxySpider()
    blogger = prey.page.split('/')[-1]
    url = 'https://www.imgkoa.com/zh-hant/profile/' + blogger
    html = get_html(url, spider)
    # self.batch_fetch_web()
    if html:
        IMGKOA_LOGGER.info(blogger + ': main page ' + url)
        # print html.content
        # re.S匹配换行符 可以多行匹配

        short_code_list = re.findall('<a href=\"/zh-hant/post/([^/]+?)/', html.content, re.S)
        # print list(set(short_code_list))

        detail_html_list = []

        video_path = "video" + os.path.sep + blogger
        mkdir(video_path)
        img_path = "img" + os.path.sep + blogger
        mkdir(img_path)

        for shortcode in list(set(short_code_list)):
            detail_html_list.append("https://www.imgkoa.com/zh-hant/post/" + shortcode)
        # print detail_html_list

        for detail_html in detail_html_list:
            # detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=False)
            # detail_html_content = spider.get_html_with_cookie(detail_html, cookie)
            detail_html_content = get_html(detail_html, spider)
            # print detail_html_content.content
            if detail_html_content:
                IMGKOA_LOGGER.info(blogger + ': detail page ' + detail_html)

                downs = re.findall('<a class=\"downbtn\" href=\"([^\"]+?)&dl=', detail_html_content.content, re.S)
                # print(downs)

                if not downs:
                    IMGKOA_LOGGER.warn(blogger + ': Fail to get down(s) on ' + detail_html)
                    continue

                videos = []
                imgs = []
                for down in downs:
                    if '_n.jpg?_nc' in down:
                        imgs.append(down)
                    if '_n.mp4?_nc' in down:
                        videos.append(down)

                if videos:
                    IMGKOA_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
                    save_video(video_path, videos)
                if imgs:
                    IMGKOA_LOGGER.info(blogger + ': images ' + ' '.join(imgs))
                    save_img(img_path, imgs)
            else:
                IMGKOA_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)

        userid = re.findall('<input type="hidden" name="userid" value="(\d+)\">', html.content, re.S)[0]
        # print userid
        next = re.findall('class="more_btn" data-next="([^\"]+?)\">', html.content, re.S)[0]
        # print(next)
        count = 0

        # 获取第一页的帖子数
        pageInfoCount = len(list(set(short_code_list)))
        # 获取这个ins总共有多个帖子
        pageInfoNum = re.findall('<div class="num" title="([^\"]+?)\">', html.content, re.S)[0]
        pageInfoNum = int(pageInfoNum.replace(',', ''))

        IMGKOA_LOGGER.info(blogger + ": Get " + str(pageInfoCount) + ' out of ' + str(pageInfoNum) + ' .')

        while pageInfoCount < pageInfoNum:
            count += 1
            IMGKOA_LOGGER.info(blogger + ': next cursor:' + str(count))

            # https://api.imgkoa.com/posts?userid=19410587&next=QVFDSTN3dkVXQnZ5eDNDZU1wblZOc3JrdWlNMTZJYkI2NExOM1JSa201anUxbWZyTEFlOF9PLVpnTUVvMTJzd2k2SUt5X3R1VkdHQTAwZUFSRXE3TFBHWQ%3D%3D&hl=zh-hant
            next_page = "https://api.imgkoa.com/posts?userid=" + str(userid) + "&next=" + str(next) + "&hl=zh-hant"
            # print next_page
            # nextHtml = spider.getHtml(next_page, timeout=10, retries=2, proxy=True)
            # nextHtml = spider.get_html_with_cookie(next_page, cookie)
            html = get_html(next_page, spider)
            # print(html.content)

            if html:
                IMGKOA_LOGGER.info(blogger + ': next cursor page ' + next_page)
                short_code_list = re.findall('\"shortcode\":\"(\d+?)\"', html.content, re.S)
                # print list(set(short_code_list))

                detail_html_list = []

                for shortcode in list(set(short_code_list)):
                    detail_html_list.append("https://www.imgkoa.com/zh-hant/post/" + shortcode)
                # print detail_html_list

                for detail_html in detail_html_list:
                    # detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=False)
                    # detail_html_content = spider.get_html_with_cookie(detail_html, cookie)
                    detail_html_content = get_html(detail_html, spider)
                    # print detail_html_content.content
                    if detail_html_content:
                        IMGKOA_LOGGER.info(blogger + ': detail page ' + detail_html)

                        downs = re.findall('<a class=\"downbtn\" href=\"([^\"]+?)&dl=', detail_html_content.content,
                                           re.S)
                        # print(downs)

                        if not downs:
                            IMGKOA_LOGGER.warn(blogger + ': Fail to get down(s) on ' + detail_html)
                            continue

                        videos = []
                        imgs = []
                        for down in downs:
                            if '_n.jpg?_nc' in down:
                                imgs.append(down)
                            if '_n.mp4?_nc' in down:
                                videos.append(down)

                        if videos:
                            IMGKOA_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
                            save_video(video_path, videos)
                        if imgs:
                            IMGKOA_LOGGER.info(blogger + ': images ' + ' '.join(imgs))
                            save_img(img_path, imgs)
                    else:
                        IMGKOA_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)

                pageInfoCount = pageInfoCount + len(list(set(short_code_list)))
                IMGKOA_LOGGER.info(blogger + ": Get " + str(pageInfoCount) + ' out of ' + str(pageInfoNum) + ' .')

                if 'has_next":true' in html.content:
                    next = re.findall('\"next\":\"([^\"]+?)\"', html.content, re.S)[0]
                    # print(next)
                elif 'has_next":false' in html.content:
                    IMGKOA_LOGGER.info(blogger + ': End of next cursor.' + next_page)
                    break
                else:
                    IMGKOA_LOGGER.warn(blogger + ': Fail to get ' + str(count) + ' cursor\'s next cursor.' + next_page)
                    break
            else:
                # print 'Get ' + prey.page + ' next cursor ' + str(count) + ' failed!!'
                IMGKOA_LOGGER.warn(blogger + ': Fail to get ' + str(count) + ' cursor ' + next_page)
                break

    else:
        # print 'Get ' + prey.page + ' failed!!'
        IMGKOA_LOGGER.warn(blogger + ': Fail to get main page ' + url)


def save_img(path, result):
    spider = ipProxySpider()
    # print "save_img"
    if result:
        total = 0
        down_load_count = 0
        downloadedfilelist = getDownloadedFileName(
            os.path.join(INSTAGRAMDOWNLOADDIR, path.split(os.path.sep)[-1] + '.txt'))

        for item in result:
            total += 1
            imgname = item.split('/')[-1].split('?')[0]
            img_file_name = path + os.path.sep + imgname
            # print img_file_name
            if os.path.exists(img_file_name):
                down_load_count += 1
                IMGKOA_LOGGER.info(path.split(os.path.sep)[-1] + ': already exists ' + item)
                pass
            elif imgname in downloadedfilelist:
                IMGKOA_LOGGER.info(
                    path.split(os.path.sep)[-1] + ': exists in INSTAGRAMDOWNLOADDIR conf file ' + item)
                pass
            else:
                # print img_file_name
                img = spider.getHtml(item, timeout=10, retries=2, proxy=False)
                if img:
                    f = open(img_file_name, 'ab')
                    f.write(img.content)
                    f.close()
                    down_load_count += 1
                    # print item + ' downloads successfully.'
                    IMGKOA_LOGGER.info(path.split(os.path.sep)[-1] + ': successfully downloads ' + item)
                else:
                    # print item + " downloads failed."
                    IMGKOA_LOGGER.warn(path.split(os.path.sep)[-1] + ': fail to downloads ' + item)

        # if down_load_count == total and down_load_count > 0:
        #     print "save all pics of this page."
        # else:
        #     print "save some of pics failed!"


def save_video(path, videos):
    spider = ipProxySpider()
    if videos:
        total = 0
        down_load_count = 0
        downloadedfilelist = getDownloadedFileName(os.path.join(INSTAGRAMDOWNLOADDIR, path.split(os.path.sep)[-1] + '.txt'))

        for item in videos:
            total += 1
            videoname = item.split('/')[-1].split('?')[0]
            video_file_name = path + os.path.sep + videoname
            # print img_file_name
            if os.path.exists(video_file_name):
                down_load_count += 1

                IMGKOA_LOGGER.info(path.split(os.path.sep)[-1] + ': already exists ' + item)
                pass
            elif videoname in downloadedfilelist:
                IMGKOA_LOGGER.info(path.split(os.path.sep)[-1] + ': exists in INSTAGRAMDOWNLOADDIR conf file ' + item)
                pass
            else:
                # print video_file_name

                video = spider.getHtml(item, timeout=10, retries=2, proxy=False)
                if video:
                    with open(video_file_name, 'wb') as f:
                        f.write(video.content)
                    down_load_count += 1
                    # print item + ' downloads successfully.'
                    IMGKOA_LOGGER.info(path.split(os.path.sep)[-1] + ': successfully downloads ' + item)
                else:
                    # print item + " downloads failed."
                    IMGKOA_LOGGER.warn(path.split(os.path.sep)[-1] + ': fail to downloads ' + item)

        # if down_load_count == total and down_load_count > 0:
        #     print "save all videos of this page."
        # else:
        #     print "save some of videos failed!"


def mkdir(path):
    path = path.strip()
    isExists = os.path.exists(path)
    if not isExists:
        # print u'建了一个名字叫做', path, u'的文件夹！'
        IMGKOA_LOGGER.info(u'建了一个名字叫做' + path + u'的文件夹！')
        # 递归创建文件夹
        os.makedirs(os.path.join(".", path))
        return True
    else:
        # print u'名字叫做', path, u'的文件夹已经存在了！'
        IMGKOA_LOGGER.debug(u'名字叫做' +  path + u'的文件夹已经存在了！')
        return False


def remove_tag(string_list):
    tag = '\u0026_nc_cat='
    for index, str in enumerate(string_list):
        # print(str.split(tag)[0])
        string_list[index] = str.split(tag)[0]
    # print string_list


def unicode_escape(strList):
    result = []
    for str in strList:
        result.append(str.decode('unicode_escape'))
    return result


def get_cookie():
    filename = './conf/instagramcookie.json'
    load_dict = {}
    with open(filename, 'r') as load_f:
        load_dict = json.load(load_f)
        # print(load_dict)
    return load_dict


def get_html(url, spider, cookie=''):
    if COOKIE:
        if not cookie:
            cookie = get_cookie()

        return spider.get_html_with_cookie(url, cookie)
    else:
        return spider.getHtml(url)


class SpiderPrey(object):
    def __init__(self):
        self._catalogue = ""
        self._catalogue_reg = ""
        self._page = ""
        self._next_page = ""
        self._page_reg = ""

    @property
    def catalogue(self):
        return self._catalogue

    @catalogue.setter
    def catalogue(self, value):
        if not isinstance(value, basestring):
            raise ValueError('catalogue must be a string!')
        self._catalogue = value

    @property
    def catalogue_reg(self):
        return self._catalogue_reg

    @catalogue_reg.setter
    def catalogue_reg(self, value):
        if not isinstance(value, basestring):
            raise ValueError('catalogue_reg must be a string!')
        self._catalogue_reg = value

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        if not isinstance(value, basestring):
            raise ValueError('page must be a string!')
        self._page = value

    @property
    def next_page(self):
        return self._next_page

    @next_page.setter
    def next_page(self, value):
        if not isinstance(value, basestring):
            raise ValueError('next_page must be a string!')
        self._next_page = value

    @property
    def page_reg(self):
        return self._page_reg

    @page_reg.setter
    def page_reg(self, value):
        if not isinstance(value, basestring):
            raise ValueError('page_reg must be a string!')
        self._page_reg = value


if __name__ == "__main__":
    web = 'https://www.imgkoa.com/zh-hant/'
    prey_list = []
    # for blogger in ['kingjames']:
    #     prey = SpiderPrey()
    #     page = "https://www.instagram.com/" + blogger
    #     reg = "\"display_[a-z]+\": *\"([^\"]+?)\", *\""
    #     prey.catalogue = "null"
    #     prey.catalogue_reg = "null"
    #     prey.page = page
    #     prey.next_page = "null"
    #     prey.page_reg = reg
    #     prey_list.append(prey)

    prey_list = get_prey_list()

    # 用来截取，从某一个网页（包含该网页）之后的页面数据
    # start = 0
    # for prey in prey_list:
    #     if prey.page == 'https://www.instagram.com/leannabartlett':
    #         break
    #     start += 1
    # prey_list = prey_list[start:start+1]

    prey_list = prey_list[0:62] #450
    #prey_list = prey_list[-1:]

    # 按照获取的list，爬取数字指定的页码的数据
    spider_mutile_cpu(spider_one_imgkoa_blogger, prey_list, 1)
    # 按照获取的list，爬取网页的全部数据

    #use_mutile_cpu(spider_one_imgkoa_blogger_full, prey_list)
    # 只爬一个ins的全部数据
    #spider_one_imgkoa_blogger_full(prey_list[0])