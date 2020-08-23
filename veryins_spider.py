# coding:utf-8
import logging
import xml.dom.minidom
import re
import os
import sys
from logging.handlers import RotatingFileHandler
from ipProxySpider import ipProxySpider
import concurrent.futures
import random
import time
import json
import chardet
import requests
import urllib2

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

VERYINS_LOGGER = logging.getLogger(__name__)
VERYINS_STREAM_HANDLER = logging.StreamHandler(sys.stdout)
VERYINS_STREAM_HANDLER.setLevel(logging.WARN)
VERYINS_STREAM_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))
VERYINS_LOGGER.addHandler(VERYINS_STREAM_HANDLER)
VERYINS_ROTATING_FILE_HANDLER = RotatingFileHandler('./log/info.log', maxBytes=100 * 1024 * 1024, backupCount=10)
VERYINS_ROTATING_FILE_HANDLER.setLevel(logging.INFO)
VERYINS_ROTATING_FILE_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))
VERYINS_LOGGER.addHandler(VERYINS_ROTATING_FILE_HANDLER)

COOKIE = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
}

LINKSREG = 'wrapper">(.+?)<div class="caption"'
VIDEOLINKSREG = '<source src="([^"]+?)" type="video'
IMGLINKSREG = '<img src="([^"]+?)">'
VIDEOIMGLINKSREG = 'poster="([^"]+?)">'
UIDREG = '<div id="username" data-fullname="[^"]+".+?="([^"]+?)" data-username='
NEXTCURSORREG = 'next-cursor="([^"]+?)" data-tag='
CODEREG = '"code":"([^"]+?)",'
DATACODEREG = 'data-code="([^"]+?)"'
ENDCURSORREG = '"end_cursor":"([^"]+?)"'

def get_prey_list():
    file = "./conf/instagram.xml"
    preylist = []
    try:
        domTree = xml.dom.minidom.parse(file)
    except:
        VERYINS_LOGGER.error("Can't open xml file!")
        return preylist

    collection = domTree.documentElement
    nodes = collection.getElementsByTagName("html")
    for node in nodes:
        page = node.getElementsByTagName("page")[0].childNodes[0].data
        # print ("page: %s" % page)

        #从instagram读取待爬取的blogger，替换为veryins的网址
        page = page.replace('.instagram.', '.veryins.')
        prey = SpiderPrey()
        prey.page = page
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


def spider_one_veryins_blogger(prey, next_curosr_num=0):
    blogger = prey.page.split('/')[-1]
    # html = spider.getHtml(prey.page, timeout=10, retries=2, proxy=False)
    # html = spider.get_html_with_cookie(prey.page, cookie)
    html = get_html(prey.page)
    if html:
        VERYINS_LOGGER.info(blogger + ': main page ' + prey.page)
        # print html.content
        # re.S匹配换行符 可以多行匹配

        short_code_list = re.findall(DATACODEREG, html.text, re.S)
        # short_code_list = re.findall('\"shortcode\": ?\"([^\"]+?)\", ?\"', html.content, re.S)

        detail_html_list = []

        video_path = "video" + os.path.sep + blogger
        mkdir(video_path)
        img_path = "img" + os.path.sep + blogger
        mkdir(img_path)

        for shortcode in list(set(short_code_list)):
            # 来拼接详情页面的网址 www.instagram.com / p / shortcode /?taken - by = xxx
            detail_html_list.append("https://www.veryins.com/p/" + shortcode)
            # detail_html_list.append("https://www.instagram.com/p/" + shortcode)
        # print detail_html_list
        for detail_html in detail_html_list:
            # detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=False)
            # detail_html_content = spider.get_html_with_cookie(detail_html, cookie)
            detail_html_content = get_html(detail_html)

            if detail_html_content:
                VERYINS_LOGGER.info(blogger + ': detail page ' + detail_html)

                linkstr = re.findall(LINKSREG, detail_html_content.content, re.S)[0]
                if '<source src=' in linkstr:
                    videos = re.findall(VIDEOLINKSREG, linkstr, re.S)
                    # print(videos)
                    if videos:
                        # videos = unicode_escape(videos)
                        VERYINS_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
                        save_video(video_path, videos)
                    else:
                        VERYINS_LOGGER.warn(blogger + ': Fail to get video(s) on ' + detail_html)

                img_list = re.findall(IMGLINKSREG, linkstr, re.S)
                img_list.extend(re.findall(VIDEOIMGLINKSREG, linkstr, re.S))
                # print(img_list)
                if img_list:
                    # img_list = unicode_escape(img_list)
                    VERYINS_LOGGER.info(blogger + ': images ' + ' '.join(img_list))

                    save_img(img_path, img_list)
                else:
                    VERYINS_LOGGER.warn(blogger + ': Fail to get image(s) on ' + detail_html)
            else:
                VERYINS_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)

        uid = re.findall(UIDREG, html.content, re.S)[0]
        # print blogger + uid
        nextcursor = re.findall(NEXTCURSORREG, html.content, re.S)[0]
        # print blogger + nextcursor
        count = 0
        # 有下拉页需要抓取
        while count < next_curosr_num:
            count += 1
            VERYINS_LOGGER.info(blogger + ': next cursor:' + str(count))

            next_page = "https://www.veryins.com/user/post?next=" + nextcursor + "&uid=" + uid + "&tag=1"
            # print next_page
            # nextHtml = spider.getHtml(next_page, timeout=10, retries=2, proxy=True)
            # nextHtml = spider.get_html_with_cookie(next_page, cookie)
            nextHtml = post_html(next_page)
            if nextHtml:
                VERYINS_LOGGER.info(blogger + ': next cursor page ' + next_page)
                # print nextHtml.content
                # 先抓取shortcode，来拼接详情页面的网址
                short_code_list_next_cursor = re.findall(CODEREG, nextHtml.content, re.S)
                # print short_code_list_next_cursor
                detail_html_list = []
                for shortcode in list(set(short_code_list_next_cursor)):
                    detail_html_list.append("https://www.veryins.com/p/" + shortcode)
                # print detail_html_list
                # print len(detail_html_list)
                for detail_html in detail_html_list:
                    # detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=True)
                    # detail_html_content = spider.get_html_with_cookie(detail_html, cookie)
                    detail_html_content = get_html(detail_html)
                    # print detail_html_content.content

                    if detail_html_content:
                        VERYINS_LOGGER.info(blogger + ': detail page ' + detail_html)
                        linkstr = re.findall(LINKSREG, detail_html_content.content, re.S)[0]

                        if '<source src=' in linkstr:
                            videos = re.findall(VIDEOLINKSREG, linkstr, re.S)
                            # print(videos)
                            if videos:
                                # videos = unicode_escape(videos)
                                VERYINS_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
                                save_video(video_path, videos)
                            else:
                                VERYINS_LOGGER.warn(blogger + ': Fail to get video(s) on ' + detail_html)

                        img_list = re.findall(IMGLINKSREG, linkstr, re.S)
                        img_list.extend(re.findall(VIDEOIMGLINKSREG, linkstr, re.S))
                        # print(img_list)
                        if img_list:
                            # img_list = unicode_escape(img_list)
                            VERYINS_LOGGER.info(blogger + ': images ' + ' '.join(img_list))

                            save_img(img_path, img_list)
                        else:
                            VERYINS_LOGGER.warn(blogger + ': Fail to get image(s) on ' + detail_html)
                    else:
                        VERYINS_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)

                nextcursor = re.findall(ENDCURSORREG, nextHtml.content, re.S)[0]
                if not nextcursor:
                    VERYINS_LOGGER.warn(blogger + ': Fail to get end_cursor on ' + str(count) + ' cursor page ' + next_page)
                    break

            else:
                VERYINS_LOGGER.warn(blogger + ': Fail to get ' + str(count) + ' cursor page ' + next_page)
                # 网页有时候会超时，无限重新访问这一页
                count = count - 1


    else:
        VERYINS_LOGGER.warn(blogger + ': Fail to get main page ' + prey.page)


# def spider_one_veryins_blogger_full(prey):
#     spider = ipProxySpider()
#     blogger = prey.page.split('/')[-1]
#     # html = spider.getHtml(prey.page, timeout=10, retries=2, proxy=False)
#     # html = spider.get_html_with_cookie(prey.page, cookie)
#     html = get_html(prey.page, spider)
#     # self.batch_fetch_web()
#     if html:
#         VERYINS_LOGGER.info(blogger + ': main page ' + prey.page)
#         # print html.content
#         # re.S匹配换行符 可以多行匹配
#
#         # 先抓取shortcode，这里需要特殊处理下，去掉多余shortcode
#         html_no_sidecar = re.sub('"edge_sidecar_to_children".+?}}]}}},', '', html.content)
#         short_code_list = re.findall('\"shortcode\": ?\"([^\"]+?)\", ?\"', html_no_sidecar, re.S)
#         # short_code_list = re.findall('\"shortcode\": ?\"([^\"]+?)\", ?\"', html.content, re.S)
#         # print short_code_list
#         detail_html_list = []
#
#         video_path = "video" + os.path.sep + blogger
#         mkdir(video_path)
#         img_path = "img" + os.path.sep + blogger
#         mkdir(img_path)
#         short_code_list = list(set(short_code_list))
#         for shortcode in short_code_list:
#             detail_html_list.append("https://www.veryins.com/p/" + shortcode + '/?taken-by=' + blogger)
#         # print detail_html_list
#         for detail_html in detail_html_list:
#             # detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=False)
#             # detail_html_content = spider.get_html_with_cookie(detail_html, cookie)
#             detail_html_content = get_html(detail_html, spider)
#             # print detail_html_content.content
#             if detail_html_content:
#                 VERYINS_LOGGER.info(blogger + ': detail page ' + detail_html)
#                 if 'video_url' in detail_html_content.content:
#                     videos = re.findall('\"video_url+\": ?\"([^\"]+?)\", ?\"',
#                                         detail_html_content.content, re.S)
#                     # remove_tag(videos)
#                     if videos:
#                         videos = unicode_escape(videos)
#                         VERYINS_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
#                         save_video(video_path, videos)
#                     else:
#                         VERYINS_LOGGER.warn(blogger + ': Fail to get video(s) on ' + detail_html)
#
#                 img_list = re.findall(prey.page_reg, detail_html_content.content, re.S)
#                 # remove_tag(img_list)
#                 if img_list:
#                     img_list = unicode_escape(img_list)
#                     # 只有一个的，就抓那一个；两个以上的，从第二个开始抓取，去掉重复的
#                     if len(img_list) > 1:
#                         img_list = img_list[1:]
#                     VERYINS_LOGGER.info(blogger + ': image(s) ' + ' '.join(img_list))
#
#                     save_img(img_path, img_list)
#                 else:
#
#                     VERYINS_LOGGER.warn(blogger + ': Fail to get image(s) on ' + detail_html)
#             else:
#                 VERYINS_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)
#
#         # 获取第一页的帖子数
#         pageInfoCount = len(short_code_list)
#         # 获取这个ins总共有多个帖子
#         pageInfoNum = int(
#             re.findall('\"edge_owner_to_timeline_media\":{\"count\": ?([^\"]+?), ?\"', html.content, re.S)[0])
#         VERYINS_LOGGER.info(blogger + ": Get " + str(pageInfoCount) + ' out of ' + str(pageInfoNum) + ' .')
#
#         id = re.findall("\"id\": ?\"(\d+)\", ?\"username", html.content, re.S)[0]
#         # print id
#         # query_id = 17862015703145017
#         query_hash = ''
#         count = 0
#         queryHashChangeCount = 0
#         # self.query2alive(id)
#         # 有下拉页需要抓取，使用伪造的query_id配合页面的end_cursor，组建需要抓取的下一页信息，同时在获取的帖子数大于等于总共有的帖子数的时候停止
#         nextHtml = html
#         while nextHtml.content.find("has_next_page\":true") != -1 and pageInfoCount < pageInfoNum:
#             count += 1
#             # print "next cursor:" + str(count)
#             VERYINS_LOGGER.info(blogger + ": next cursor:" + str(count))
#             end_cursor = re.findall("\"end_cursor\": ?\"([^\"]+?)\"", nextHtml.content, re.S)[0]
#             #query_hash为空的话，从QUERY_HASH_LIST的指定位置获取query_hash
#             if not query_hash:
#                 query_hash = QUERY_HASH_LIST[queryHashChangeCount]
#             # print end_cursor
#             # next_page = "https://www.instagram.com/graphql/query/?query_id=" + str(query_id) \
#             #            + "&variables=%7B%22id%22%3A%22" + id + "%22%2C%22first%22%3A12%2C%22after%22%3A%22" + end_cursor + "%22%7D"
#             next_page = "https://www.veryins.com/graphql/query/?query_hash=" + str(query_hash) \
#                         + "&variables=%7B%22id%22%3A%22" + id + "%22%2C%22first%22%3A12%2C%22after%22%3A%22" + end_cursor + "%22%7D"
#             # print next_page
#             # nextHtml = spider.getHtml(next_page, timeout=10, retries=2, proxy=False)
#             # nextHtml = spider.get_html_with_cookie(next_page, cookie)
#             nextHtml = get_html(next_page, spider)
#             if nextHtml:
#                 VERYINS_LOGGER.info(blogger + ': next cursor page ' + next_page)
#                 # print re.findall(prey.page_reg, nextweb.content, re.S)
#                 # 先抓取shortcode，来拼接详情页面的网址 www.instagram.com/p/shortcode/?taken-by=xxx
#                 short_code_list_next_cursor = re.findall('\"shortcode\": ?\"([^\"]+?)\", ?\"', nextHtml.content, re.S)
#                 detail_html_list = []
#                 short_code_list_next_cursor = list(set(short_code_list_next_cursor))
#                 for shortcode in short_code_list_next_cursor:
#                     detail_html_list.append(
#                         "https://www.veryins.com/p/" + shortcode)
#                 # print detail_html_list
#                 # print len(detail_html_list)
#
#                 for detail_html in detail_html_list:
#                     # detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=False)
#                     # detail_html_content = spider.get_html_with_cookie(detail_html, cookie)
#                     detail_html_content = get_html(detail_html, spider)
#                     # print detail_html_content.content
#
#                     if detail_html_content:
#                         VERYINS_LOGGER.info(blogger + ': detail page ' + detail_html)
#                         if 'video_url' in detail_html_content.content:
#                             videos = re.findall('\"video_url+\": ?\"([^\"]+?)\", ?\"',
#                                                 detail_html_content.content, re.S)
#                             # print videos
#                             if videos:
#                                 # dir = prey.page.split('/')[-1]
#                                 # path = "video" + os.path.sep + dir
#                                 # self.mkdir(path)
#                                 # if copy_new == 1:
#                                 #     newpath = "video" + os.path.sep + "new" + os.path.sep + dir
#                                 #     self.mkdir(newpath)
#                                 videos = unicode_escape(videos)
#                                 VERYINS_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
#                                 save_video(video_path, videos)
#                             else:
#                                 # print 'Fail to get ' + blogger + ' \'s video on ' + detail_html
#                                 VERYINS_LOGGER.warn(blogger + ': Fail to get video(s) on ' + detail_html)
#
#                         img_list = re.findall(prey.page_reg, detail_html_content.content, re.S)
#                         if img_list:
#                             img_list = unicode_escape(img_list)
#                             # 只有一个的，就抓那一个；两个以上的，从第二个开始抓取，去掉重复的
#                             if len(img_list) > 1:
#                                 img_list = img_list[1:]
#                             # print img_list
#                                 VERYINS_LOGGER.info(blogger + ': image(s) ' + ' '.join(img_list))
#
#                             # dir = prey.page.split('/')[-1]
#                             # path = "img" + os.path.sep + dir
#                             # self.mkdir(path)
#                             # if copy_new == 1:
#                             #     newpath = "img" + os.path.sep + "new" + os.path.sep + dir
#                             #     self.mkdir(newpath)
#
#                             save_img(img_path, img_list)
#                         else:
#                             # print 'Fail to get ' + blogger + ' \'s images on ' + detail_html
#                             VERYINS_LOGGER.warn(blogger + ': Fail to get image(s) on ' + detail_html)
#
#                     else:
#                         # print 'Fail to get ' + blogger + ' \'s detail web:' + detail_html
#                         VERYINS_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)
#
#                         # result = re.findall("\"display_url\": ?\"([^\"]+?)\", ?\"", html.content, re.S)
#                         # if result:
#                         #     dir = prey.page.split('/')[-1]
#                         #     path = "img" + os.path.sep + dir
#                         #     self.mkdir(path)
#                         #     if copy_new == 1:
#                         #         newpath = "img" + os.path.sep + "new" + os.path.sep + dir
#                         #         self.mkdir(newpath)
#                         #     self.save_img(path, result, copy_new)
#                         # else:
#                         #     print 'Get proxy through regs failed!!'
#
#                 pageInfoCount = pageInfoCount + len(short_code_list_next_cursor)
#                 VERYINS_LOGGER.info(blogger + ": Get " + str(pageInfoCount) + ' out of ' + str(pageInfoNum) + ' .')
#             else:
#                 # print 'Get ' + prey.page + ' next cursor ' + str(count) + ' failed!!'
#                 VERYINS_LOGGER.warn(blogger + ': Fail to get ' + str(count) + ' cursor ' + next_page)
#
#                 #更换queryhash
#                 while True:
#                     find_query_hash = False
#                     for query_hash_in_list in QUERY_HASH_LIST:
#                         #跳过正在使用的queryhash
#                         if query_hash == query_hash_in_list:
#                             continue
#
#                         # 测试一下该query_hash能否抓取到信息，无法抓取到的话，是返回一段没有太多内容的信息
#                         query_hash = query_hash_in_list
#                         test_page = "https://www.veryins.com/graphql/query/?query_hash=" + str(query_hash) \
#                                     + "&variables=%7B%22id%22%3A%22" + id + "%22%2C%22first%22%3A12%2C%22after%22%3A%22" + end_cursor + "%22%7D"
#                         # testhtml = spider.getHtml(test_page, timeout=10, retries=2, proxy=False)
#                         # testhtml = spider.get_html_with_cookie(test_page, cookie)
#                         testhtml = get_html(test_page, spider)
#                         if testhtml:
#                             #会返回两种异常的回复，暂时没有测试出来，两者的区别
#                             if testhtml.content.find('{\"viewer\":null,\"user\":null}') == -1 and testhtml.content.find('\"status\": \"fail\"') == -1:
#                                 #获取到了可以抓取的内容，则使用该queryhash去继续抓取
#                                 VERYINS_LOGGER.info(blogger + ': Find ' + str(query_hash) + ' ok to use.')
#                                 find_query_hash = True
#                                 break
#                         else:
#                             #获取不到页面，则尝试使用下一个queryhash来爬取
#                             VERYINS_LOGGER.warn(blogger + ': Fail to get ' + str(count) + ' cursor ' + test_page + ' .Try another query_hash.')
#                             continue
#
#                     if find_query_hash:
#                         VERYINS_LOGGER.info(blogger + ': next cursor page ' + test_page)
#
#                         short_code_list_test = re.findall('\"shortcode\": ?\"([^\"]+?)\", ?\"', testhtml.content, re.S)
#                         detail_html_list = []
#                         short_code_list_test = list(set(short_code_list_test))
#                         for shortcode in short_code_list_test:
#                             detail_html_list.append(
#                                 "https://www.veryins.com/p/" + shortcode)
#
#                         for detail_html in detail_html_list:
#                             # detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=False)
#                             # detail_html_content = spider.get_html_with_cookie(detail_html, cookie)
#                             detail_html_content = get_html(detail_html, spider)
#                             if detail_html_content:
#                                 VERYINS_LOGGER.info(blogger + ': detail page ' + detail_html)
#                                 if 'video_url' in detail_html_content.content:
#                                     videos = re.findall('\"video_url+\": ?\"([^\"]+?)\", ?\"',
#                                                         detail_html_content.content, re.S)
#                                     if videos:
#                                         videos = unicode_escape(videos)
#                                         VERYINS_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
#                                         save_video(video_path, videos)
#                                     else:
#                                         VERYINS_LOGGER.warn(blogger + ': Fail to get video(s) on ' + detail_html)
#
#                                 img_list = re.findall(prey.page_reg, detail_html_content.content, re.S)
#                                 if img_list:
#                                     img_list = unicode_escape(img_list)
#                                     if len(img_list) > 1:
#                                         img_list = img_list[1:]
#                                     VERYINS_LOGGER.info(blogger + ': image(s) ' + ' '.join(img_list))
#                                     save_img(img_path, img_list)
#                                 else:
#                                     VERYINS_LOGGER.warn(blogger + ': Fail to get image(s) on ' + detail_html)
#                             else:
#                                 VERYINS_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)
#                         pageInfoCount = pageInfoCount + len(short_code_list_test)
#                         VERYINS_LOGGER.info(
#                             blogger + ": Get " + str(pageInfoCount) + ' out of ' + str(pageInfoNum) + ' .')
#                         nextHtml = testhtml
#                         break
#                     else:
#                         time.sleep(120)
#
#     else:
#         # print 'Get ' + prey.page + ' failed!!'
#         VERYINS_LOGGER.warn(blogger + ': Fail to get ' + prey.page)


def save_img(path, result):
    spider = ipProxySpider()
    # print "save_img"
    if result:
        total = 0
        down_load_count = 0

        for item in result:
            total += 1
            img_file_name = path + os.path.sep + item.split('/')[-1].split('?')[0]
            # print img_file_name
            if os.path.exists(img_file_name):
                down_load_count += 1
                # print item + ' exists.'
                pass
            else:
                # print img_file_name
                img = get_html(item)
                if img:
                    f = open(img_file_name, 'ab')
                    f.write(img.content)
                    f.close()
                    down_load_count += 1
                    # print item + ' downloads successfully.'
                    VERYINS_LOGGER.info(path.split(os.path.sep)[-1] + ': successfully downloads ' + item)
                else:
                    # print item + " downloads failed."
                    VERYINS_LOGGER.warn(path.split(os.path.sep)[-1] + ': fail to downloads ' + item)

        # if down_load_count == total and down_load_count > 0:
        #     print "save all pics of this page."
        # else:
        #     print "save some of pics failed!"


def save_video(path, videos):
    spider = ipProxySpider()
    if videos:
        total = 0
        down_load_count = 0

        for item in videos:
            total += 1
            video_file_name = path + os.path.sep + item.split('/')[-1].split('?')[0]
            # print img_file_name
            if os.path.exists(video_file_name):
                down_load_count += 1

                # print item + ' exists.'
                pass
            else:
                # print video_file_name

                video = get_html(item)
                if video:
                    with open(video_file_name, 'wb') as f:
                        f.write(video.content)
                    down_load_count += 1
                    # print item + ' downloads successfully.'
                    VERYINS_LOGGER.info(path.split(os.path.sep)[-1] + ': successfully downloads ' + item)
                else:
                    # print item + " downloads failed."
                    VERYINS_LOGGER.warn(path.split(os.path.sep)[-1] + ': fail to downloads ' + item)

        # if down_load_count == total and down_load_count > 0:
        #     print "save all videos of this page."
        # else:
        #     print "save some of videos failed!"


def mkdir(path):
    path = path.strip()
    isExists = os.path.exists(path)
    if not isExists:
        # print u'建了一个名字叫做', path, u'的文件夹！'
        VERYINS_LOGGER.info(u'建了一个名字叫做' + path + u'的文件夹！')
        # 递归创建文件夹
        os.makedirs(os.path.join(".", path))
        return True
    else:
        # print u'名字叫做', path, u'的文件夹已经存在了！'
        VERYINS_LOGGER.debug(u'名字叫做' +  path + u'的文件夹已经存在了！')
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
    filename = './conf/veryinscookie.json'
    load_dict = {}
    with open(filename, 'r') as load_f:
        load_dict = json.load(load_f)
        # print(load_dict)
    return load_dict

def get_html(url, cookie=''):
    if COOKIE:
        if not cookie:
            cookie = get_cookie()
        #return spider.get_html_with_cookie(url, cookie)
        return requests.get(url, headers=HEADERS, cookies=cookie, timeout=10)
    else:
        #return spider.getHtml(url)
        return requests.get(url, headers=HEADERS, timeout=10)


def post_html(url, cookie=''):
    if COOKIE:
        if not cookie:
            cookie = get_cookie()
        #return spider.get_html_with_cookie(url, cookie)
        return requests.post(url, headers=HEADERS, cookies=cookie, timeout=10)
    else:
        #return spider.getHtml(url)
        return requests.post(url, headers=HEADERS, timeout=10)


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
    prey_list = []
    # for blogger in ['kingjames']:
    #     prey = SpiderPrey()
    #     page = "https://www.veryins.com/" + blogger
    #     prey.page = page
    #     prey_list.append(prey)

    prey_list = get_prey_list()

    # 用来截取，从某一个网页（包含该网页）之后的页面数据
    # start = 0
    # for prey in prey_list:
    #     if prey.page == 'https://www.veryins.com/manyo_yoojin':
    #         break
    #     start += 1
    # prey_list = prey_list[start:]

    # 按照获取的list，爬取数字指定的页码的数据
    spider_mutile_cpu(spider_one_veryins_blogger, prey_list, 0)
    # headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1"}
    # req = urllib2.Request('https://www.veryins.com/nasa', headers=headers)
    # r = urllib2.urlopen(req)
    # print(r.read())
    # print('==============================================================')
    # h = requests.get('https://www.veryins.com/nasa', headers=headers)
    # print(h.text)
    # 按照获取的list，爬取网页的全部数据

    #use_mutile_cpu(spider_one_veryins_blogger_full, prey_list)
    # 只爬一个ins的全部数据
    #spider_one_veryins_blogger_full(prey_list[0])