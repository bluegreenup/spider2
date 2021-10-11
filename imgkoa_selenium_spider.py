# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import selenium

import json
import requests
import time
import xml.dom.minidom
import concurrent.futures
import re
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from ipProxySpider import ipProxySpider
from fileclean import getDownloadedFileName
from fileclean import INSTAGRAMDOWNLOADDIR

LOG_FORMAT = '[%(levelname)s] %(asctime)s [name:%(name)s] [%(filename)s line:%(lineno)d] [func:%(funcName)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

ROOTLOOGER = logging.getLogger()
ROOTLOOGER.setLevel(logging.INFO)

IMGKOA_SELENIUM_LOGGER = logging.getLogger(__name__)
IMGKOA_SELENIUM_STREAM_HANDLER = logging.StreamHandler(sys.stdout)
IMGKOA_SELENIUM_STREAM_HANDLER.setLevel(logging.WARN)
IMGKOA_SELENIUM_STREAM_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))
IMGKOA_SELENIUM_LOGGER.addHandler(IMGKOA_SELENIUM_STREAM_HANDLER)
IMGKOA_SELENIUM_ROTATING_FILE_HANDLER = RotatingFileHandler('./log/info.log', maxBytes=100 * 1024 * 1024, backupCount=10)
IMGKOA_SELENIUM_ROTATING_FILE_HANDLER.setLevel(logging.INFO)
IMGKOA_SELENIUM_ROTATING_FILE_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))
IMGKOA_SELENIUM_LOGGER.addHandler(IMGKOA_SELENIUM_ROTATING_FILE_HANDLER)

COOKIE = False
SAVETOFILE = False


def get_prey_list():
    file = "./conf/instagram.xml"
    preylist = []
    try:
        domTree = xml.dom.minidom.parse(file)
    except:
        IMGKOA_SELENIUM_LOGGER.error("Can't open Instagram xml file!")
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
    blogger = prey.page.split('/')[-1]
    url = 'https://www.pixwox.com/profile/' + blogger

    IMGKOA_SELENIUM_LOGGER.info(blogger + ': main page ' + url)

    try:
        driver = webdriver.Chrome()
    except selenium.common.exceptions.SessionNotCreatedException:
        IMGKOA_SELENIUM_LOGGER.warn('Chromedriver needs to be updated!!')
        return

    while (True):
        try:
            driver.get(url)
            break
        except selenium.common.exceptions.TimeoutException:
            IMGKOA_SELENIUM_LOGGER.warn(blogger + ': Get main page timeout!! Try again.')
    # driver.maximize_window()
    # 等cloudfare校验浏览器
    time.sleep(8)

    source = driver.page_source

    short_code_list = re.findall('<a href="/[^0-9]+/([^/\{]+?)/" *class="cover_link" *target="_blank">', source, re.S)
    # print(short_code_list)
    if not short_code_list:
        IMGKOA_SELENIUM_LOGGER.warn(
            blogger + ": Get main page short code list failed!!!Owner may change the web.")
        driver.quit()
        return

    video_path = "video" + os.path.sep + blogger
    mkdir(video_path)
    img_path = "img" + os.path.sep + blogger
    mkdir(img_path)

    new_window = 'window.open()'
    driver.execute_script(new_window)
    tabs = driver.window_handles
    driver.switch_to.window(tabs[1])

    for shortcode in short_code_list:
        while (True):
            try:
                driver.get("https://www.pixwox.com/post/" + shortcode)
                break
            except selenium.common.exceptions.TimeoutException:
                IMGKOA_SELENIUM_LOGGER.warn(blogger + ": Get https://www.pixwox.com/post/" + shortcode + ' timeout!! Try again.')
        IMGKOA_SELENIUM_LOGGER.info(blogger + ': detail page ' + "https://www.pixwox.com/post/" + shortcode)

        tab_source = driver.page_source
        # print(tab_source)

        download_list = re.findall('<a class="downbtn" href="([^"]+?)">', tab_source, re.S)
        # print(download_list)

        for i in range(len(download_list)):
            download_list[i] = download_list[i].replace('amp;', '')
            download_list[i] = download_list[i][:-5]
        # print(download_list)

        videos = []
        imgs = []
        for down in download_list:
            if '_n.jpg?' in down:
                imgs.append(down)
            if '_n.mp4?' in down:
                videos.append(down)

        # print(videos)
        # print(imgs)

        if videos:
            IMGKOA_SELENIUM_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
            save_video(video_path, videos)
        if imgs:
            IMGKOA_SELENIUM_LOGGER.info(blogger + ': images ' + ' '.join(imgs))
            save_img(img_path, imgs)

    driver.switch_to.window(tabs[0])

    userid = re.findall('<input type="hidden" name="userid" value="([^"]+?)">', source, re.S)[0]
    data_next = re.findall('<a href="javascript:void\(0\);" class="more_btn" data-next="([^"]+?)">', source, re.S)
    # print(userid)
    # print(data_next)

    if data_next:
        data_next = data_next[0]
    else:
        IMGKOA_SELENIUM_LOGGER.info(blogger + ': No next cursor.')
        driver.quit()
        return

    count = 0
    videofulldownload = False
    imgfulldownload = False
    lastimgfulldownload = False
    lastvideofulldownload = False
    while count < next_curosr_num:
        count += 1
        IMGKOA_SELENIUM_LOGGER.info(blogger + ': next cursor:' + str(count))

        nextcursor = 'https://api.pixwox.com/posts?userid=' + userid + '&next=' + data_next
        IMGKOA_SELENIUM_LOGGER.info(blogger + ': next cursor page ' + nextcursor)

        driver.get(nextcursor)
        # print(driver.page_source)
        time.sleep(2)

        piclist = re.findall('down_pic":"([^"]+?)"', driver.page_source, re.S)
        videolist = re.findall('down_video":"([^"]+?)"', driver.page_source, re.S)

        # pic一定有，如果获取不到说明页面改变，video未必有，暂不包含video获取不到的逻辑
        # if not piclist:
        #     IMGKOA_SELENIUM_LOGGER.warn(
        #         blogger + ": Get next cursor piclist failed!!!Owner may change the web.")
        #     driver.quit()
        #     return

        piclist = list(set(piclist))
        videolist = list(set(videolist))

        # print(len(piclist))
        # print(piclist)
        # print(len(videolist))
        # print(videolist)

        for i in range(len(piclist)):
            piclist[i] = piclist[i].replace('\\u0026', '&')
            piclist[i] = piclist[i].replace('\\', '')
            piclist[i] = piclist[i][:-5]

        for i in range(len(videolist)):
            videolist[i] = videolist[i].replace('\\u0026', '&')
            videolist[i] = videolist[i].replace('\\', '')
            videolist[i] = videolist[i][:-5]

        # print(len(piclist))
        # print(piclist)
        # print(len(videolist))
        # print(videolist)

        videofulldownload = False
        imgfulldownload = False
        if videolist:
            IMGKOA_SELENIUM_LOGGER.info(blogger + ': video(s) ' + ' '.join(videolist))
            videofulldownload = save_video(video_path, videolist)
        else:
            # 该cursor没有video，默认算成该cursor的video都下载了
            videofulldownload = True
        if piclist:
            IMGKOA_SELENIUM_LOGGER.info(blogger + ': images ' + ' '.join(piclist))
            imgfulldownload = save_img(img_path, piclist)
        else:
            # 该cursor没有pic，默认算成该cursor的pic都下载了
            imgfulldownload = True

        # 根据同一个cursor内的video和img是否都下载完毕来判断后续是否都下载完毕了
        # if videofulldownload and imgfulldownload:
        #     IMGKOA_SELENIUM_LOGGER.info(blogger + ': has already downloaded all of the ' + str(count) + ' cursor\'s imgs and videos.')
        #     break

        # 根据前后两个cursor的图是否都下载来判断后续的是否都已经下载完毕
        if imgfulldownload:
            IMGKOA_SELENIUM_LOGGER.info(
                blogger + ': has already downloaded all of the ' + str(count) + ' cursor\'s imgs.')
            if lastimgfulldownload:
                # 上一次也是下载过的，就直接退出循环
                IMGKOA_SELENIUM_LOGGER.info(blogger + ': ends this download.')
                break
            else:
                lastimgfulldownload = True
        else:
            lastimgfulldownload = False

        if 'has_next":true' in driver.page_source:
            data_next = re.findall('next":"([^"]+?)"', driver.page_source, re.S)[0]
            # print(data_next)
        elif 'has_next":false' in driver.page_source:
            IMGKOA_SELENIUM_LOGGER.info(blogger + ': End of next cursor.' + nextcursor)
            break

    driver.quit()


def spider_one_imgkoa_blogger_full(prey):
    blogger = prey.page.split('/')[-1]
    url = 'https://www.pixwox.com/profile/' + blogger

    IMGKOA_SELENIUM_LOGGER.info(blogger + ': main page ' + url)

    try:
        driver = webdriver.Chrome()
    except selenium.common.exceptions.SessionNotCreatedException:
        IMGKOA_SELENIUM_LOGGER.warn('Chromedriver needs to be updated!!')
        return

    while(True):
        try:
            driver.get(url)
            break
        except selenium.common.exceptions.TimeoutException:
            IMGKOA_SELENIUM_LOGGER.warn(blogger + ': Get main page timeout!! Try again.')
    # driver.maximize_window()
    # 等cloudfare校验浏览器
    time.sleep(5)

    source = driver.page_source
    # print(source)

    short_code_list = re.findall('<a href="/[^0-9]+/([^/\{]+?)/" *class="cover_link" *target="_blank">', source, re.S)
    # print(short_code_list)
    if not short_code_list:
        IMGKOA_SELENIUM_LOGGER.warn(
            blogger + ": Get main page short code list failed!!!Owner may change the web.")
        driver.quit()
        return

    video_path = "video" + os.path.sep + blogger
    mkdir(video_path)
    img_path = "img" + os.path.sep + blogger
    mkdir(img_path)

    new_window = 'window.open()'
    driver.execute_script(new_window)
    tabs = driver.window_handles
    driver.switch_to.window(tabs[1])

    for shortcode in short_code_list:
        while (True):
            try:
                driver.get("https://www.pixwox.com/post/" + shortcode)
                break
            except selenium.common.exceptions.TimeoutException:
                IMGKOA_SELENIUM_LOGGER.warn(blogger + ": Get https://www.pixwox.com/post/" + shortcode + ' timeout!! Try again.')
        IMGKOA_SELENIUM_LOGGER.info(blogger + ': detail page ' + "https://www.pixwox.com/post/" + shortcode)

        tab_source = driver.page_source
        # print(tab_source)

        download_list = re.findall('<a class="downbtn" href="([^"]+?)">', tab_source, re.S)
        # print(download_list)

        for i in range(len(download_list)):
            download_list[i] = download_list[i].replace('amp;', '')
            download_list[i] = download_list[i][:-5]
        # print(download_list)

        videos = []
        imgs = []
        for down in download_list:
            if '_n.jpg?' in down:
                imgs.append(down)
            if '_n.mp4?' in down:
                videos.append(down)

        # print(videos)
        # print(imgs)

        if videos:
            IMGKOA_SELENIUM_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
            save_video(video_path, videos)
        if imgs:
            IMGKOA_SELENIUM_LOGGER.info(blogger + ': images ' + ' '.join(imgs))
            save_img(img_path, imgs)

    driver.switch_to.window(tabs[0])

    userid = re.findall('<input type="hidden" name="userid" value="([^"]+?)">', source, re.S)
    data_next = re.findall('<a href="javascript:void\(0\);" class="more_btn" data-next="([^"]+?)">', source, re.S)
    # print(userid)
    # print(data_next)
    if userid:
        userid = userid[0]
    else:
        IMGKOA_SELENIUM_LOGGER.info(blogger + ': No user id.')
        driver.quit()
        return

    if data_next:
        data_next = data_next[0]
    else:
        IMGKOA_SELENIUM_LOGGER.info(blogger + ': No next cursor.')
        driver.quit()
        return

    count = 0
    videofulldownload = False
    imgfulldownload = False
    lastimgfulldownload = False
    lastvideofulldownload = False
    while True:
        count += 1
        IMGKOA_SELENIUM_LOGGER.info(blogger + ': next cursor:' + str(count))

        nextcursor = 'https://api.pixwox.com/posts?userid=' + userid + '&next=' + data_next
        IMGKOA_SELENIUM_LOGGER.info(blogger + ': next cursor page ' + nextcursor)

        driver.get(nextcursor)
        # print(driver.page_source)
        time.sleep(2)

        piclist = re.findall('down_pic":"([^"]+?)"', driver.page_source, re.S)
        videolist = re.findall('down_video":"([^"]+?)"', driver.page_source, re.S)

        # pic一定有，如果获取不到说明页面改变，video未必有，暂不包含video获取不到的逻辑
        # if not piclist:
        #     IMGKOA_SELENIUM_LOGGER.warn(
        #         blogger + ": Get next cursor piclist failed!!!Owner may change the web.")
        #     driver.quit()
        #     return

        piclist = list(set(piclist))
        videolist = list(set(videolist))

        # print(len(piclist))
        # print(piclist)
        # print(len(videolist))
        # print(videolist)

        for i in range(len(piclist)):
            piclist[i] = piclist[i].replace('\\u0026', '&')
            piclist[i] = piclist[i].replace('\\', '')
            piclist[i] = piclist[i][:-5]

        for i in range(len(videolist)):
            videolist[i] = videolist[i].replace('\\u0026', '&')
            videolist[i] = videolist[i].replace('\\', '')
            videolist[i] = videolist[i][:-5]

        # print(len(piclist))
        # print(piclist)
        # print(len(videolist))
        # print(videolist)

        videofulldownload = False
        imgfulldownload = False
        if videolist:
            IMGKOA_SELENIUM_LOGGER.info(blogger + ': video(s) ' + ' '.join(videolist))
            videofulldownload = save_video(video_path, videolist)
        else:
            # 该cursor没有video，默认算成该cursor的video都下载了
            videofulldownload = True
        if piclist:
            IMGKOA_SELENIUM_LOGGER.info(blogger + ': images ' + ' '.join(piclist))
            imgfulldownload = save_img(img_path, piclist)
        else:
            # 该cursor没有pic，默认算成该cursor的pic都下载了
            imgfulldownload = True

        # 根据同一个cursor内的video和img是否都下载完毕来判断后续是否都下载完毕了
        # if videofulldownload and imgfulldownload:
        #     IMGKOA_SELENIUM_LOGGER.info(blogger + ': has already downloaded all of the ' + str(count) + ' cursor\'s imgs and videos.')
        #     break

        # 根据前后两个cursor的图是否都下载来判断后续的是否都已经下载完毕
        if imgfulldownload:
            IMGKOA_SELENIUM_LOGGER.info(
                blogger + ': has already downloaded all of the ' + str(count) + ' cursor\'s imgs.')
            if lastimgfulldownload:
                # 上一次也是下载过的，就直接退出循环
                IMGKOA_SELENIUM_LOGGER.info(blogger + ': ends this download.')
                break
            else:
                lastimgfulldownload = True
        else:
            lastimgfulldownload = False

        if 'has_next":true' in driver.page_source:
            data_next = re.findall('next":"([^"]+?)"', driver.page_source, re.S)[0]
            # print(data_next)
        elif 'has_next":false' in driver.page_source:
            IMGKOA_SELENIUM_LOGGER.info(blogger + ': End of next cursor.' + nextcursor)
            break

    driver.quit()


def save_img(path, result):
    spider = ipProxySpider()
    # print "save_img"
    if result:
        has_in_dir = 0
        has_in_file = 0
        down_load_count = 0
        downloadedfilelist = getDownloadedFileName(
            os.path.join(INSTAGRAMDOWNLOADDIR, path.split(os.path.sep)[-1] + '.txt'))

        for item in result:
            imgname = item.split('/')[-1].split('?')[0]
            img_file_name = path + os.path.sep + imgname
            # print img_file_name
            if os.path.exists(img_file_name):
                has_in_dir += 1
                IMGKOA_SELENIUM_LOGGER.info(path.split(os.path.sep)[-1] + ': already exists ' + item)
                pass
            elif imgname in downloadedfilelist:
                has_in_file += 1
                IMGKOA_SELENIUM_LOGGER.info(
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
                    IMGKOA_SELENIUM_LOGGER.info(path.split(os.path.sep)[-1] + ': successfully downloads ' + item)
                else:
                    # print item + " downloads failed."
                    IMGKOA_SELENIUM_LOGGER.warn(path.split(os.path.sep)[-1] + ': fail to downloads ' + item)

        if len(result) == has_in_file:
            IMGKOA_SELENIUM_LOGGER.info(path.split(os.path.sep)[-1] + ': has already downloaded all of the cursor\'s imgs.')
            # 返回true表示这页的数据都已经下载过了
            return True
        else:
            return False


def save_video(path, videos):
    spider = ipProxySpider()
    if videos:
        has_in_dir = 0
        has_in_file = 0
        down_load_count = 0
        downloadedfilelist = getDownloadedFileName(os.path.join(INSTAGRAMDOWNLOADDIR, path.split(os.path.sep)[-1] + '.txt'))

        for item in videos:
            videoname = item.split('/')[-1].split('?')[0]
            video_file_name = path + os.path.sep + videoname
            # print img_file_name
            if os.path.exists(video_file_name):
                has_in_dir += 1
                IMGKOA_SELENIUM_LOGGER.info(path.split(os.path.sep)[-1] + ': already exists ' + item)
                pass
            elif videoname in downloadedfilelist:
                has_in_file += 1
                IMGKOA_SELENIUM_LOGGER.info(path.split(os.path.sep)[-1] + ': exists in INSTAGRAMDOWNLOADDIR conf file ' + item)
                pass
            else:
                # print video_file_name
                # 默认用request去下载，除非配置保存到文件，用下载器手动下载
                if SAVETOFILE:
                    videotodownload = path + os.path.sep + 'download.txt'
                    with open(videotodownload, 'a') as f:
                        f.write(item)
                        f.write('\n')

                    down_load_count += 1
                    IMGKOA_SELENIUM_LOGGER.info(path.split(os.path.sep)[-1] + ': successfully saves to file: ' + item)
                    # 后续要手动去把download.txt里的url用别的下载工具下载
                else:
                    video = spider.getHtml(item, timeout=10, retries=2, proxy=False)
                    if video:
                        with open(video_file_name, 'wb') as f:
                            f.write(video.content)
                        down_load_count += 1
                        # print item + ' downloads successfully.'
                        IMGKOA_SELENIUM_LOGGER.info(path.split(os.path.sep)[-1] + ': successfully downloads ' + item)
                    else:
                        # print item + " downloads failed."
                        IMGKOA_SELENIUM_LOGGER.warn(path.split(os.path.sep)[-1] + ': fail to downloads ' + item)

        if len(videos) == has_in_file:
            IMGKOA_SELENIUM_LOGGER.info(path.split(os.path.sep)[-1] + ': has already downloaded all of the cursor\'s videos.')
            # 返回true表示这页的数据都已经下载过了
            return True
        else:
            return False


def mkdir(path):
    path = path.strip()
    isExists = os.path.exists(path)
    if not isExists:
        # print u'建了一个名字叫做', path, u'的文件夹！'
        IMGKOA_SELENIUM_LOGGER.info(u'建了一个名字叫做' + path + u'的文件夹！')
        # 递归创建文件夹
        os.makedirs(os.path.join(".", path))
        return True
    else:
        # print u'名字叫做', path, u'的文件夹已经存在了！'
        IMGKOA_SELENIUM_LOGGER.debug(u'名字叫做' +  path + u'的文件夹已经存在了！')
        return False


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


if __name__ == '__main__':
    web = "https://www.pixwox.com/zh-hant/"
    # 'https://www.imgkoa.com/zh-hant/'

    COOKIE = False
    SAVETOFILE = True

    prey_list = []

    # 自行测试用
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
    print len(prey_list)
    prey_list = prey_list[-1:]
    # prey_list = prey_list[-1:]

    # 用来截取，从某一个blogger之后的页面数据
    # start = 0
    # for prey in prey_list:
    #     if prey.page == 'https://www.instagram.com/dinonoz':
    #         break
    #     start += 1
    # prey_list = prey_list[start:]

    # 用多进程，爬取获取的list的指定页码的数据
    #spider_mutile_cpu(spider_one_imgkoa_blogger, prey_list, 3)

    # 用多进程，爬取获取的list的全部数据
    # use_mutile_cpu(spider_one_imgkoa_blogger_full, prey_list)

    # 只爬一个ins的全部数据
    # spider_one_imgkoa_blogger_full(prey_list[0])

    # 用普通方式爬取获取的list的指定页数的数据
    # for prey in prey_list:
    #     spider_one_imgkoa_blogger(prey, 3)

    # 顺序爬取的list全部数据
    for prey in prey_list:
        spider_one_imgkoa_blogger_full(prey)

    # 2021.1.8 最后全爬

    # 2021.9.8 开始重新下载