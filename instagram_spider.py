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

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    )
INSTAGRAM_LOGGER = logging.getLogger(__name__)
# INSTAGRAM_STREAM_HANDLER = logging.StreamHandler(sys.stdout)
# INSTAGRAM_STREAM_HANDLER.setLevel(logging.INFO)
# INSTAGRAM_STREAM_HANDLER.setFormatter(logging.Formatter(
#     '[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s'))
# INSTAGRAM_LOGGER.addHandler(INSTAGRAM_STREAM_HANDLER)
INSTAGRAM_ROTATING_FILE_HANDLER = RotatingFileHandler('./log/info.log', maxBytes=100 * 1024 * 1024, backupCount=10)
INSTAGRAM_ROTATING_FILE_HANDLER.setLevel(logging.DEBUG)
INSTAGRAM_ROTATING_FILE_HANDLER.setFormatter(logging.Formatter(
    '[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s'))
INSTAGRAM_LOGGER.addHandler(INSTAGRAM_ROTATING_FILE_HANDLER)

QUERY_HASH_LIST = ['e7e2f4da4b02303f74f0841279e52d76', 'c9100bf9110dd6361671f113dd02e7d6', '2c5d4d8b70cad329c4a6ebe3abb6eedd']

def get_prey_list():
    file = "./conf/instagram.xml"
    preylist = []
    try:
        domTree = xml.dom.minidom.parse(file)
    except:
        INSTAGRAM_LOGGER.error("Can't open Instagram xml file!")
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

def spider_mutile_cpu(preylist, next_curosr_num, copy_new):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for prey in preylist:
            executor.submit(spider_one_instagram_blogger, prey, next_curosr_num, copy_new)

def use_mutile_cpu(preylist, func):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for prey in preylist:
            executor.submit(func, prey)


def spider_one_instagram_blogger(prey, next_curosr_num, copy_new=True):
    spider = ipProxySpider()
    blogger = prey.page.split('/')[-1]
    html = spider.getHtml(prey.page, timeout=10, retries=2, proxy=False)
    # self.batch_fetch_web()
    if html:
        INSTAGRAM_LOGGER.info(blogger + ': main page ' + prey.page)
        # print html.content
        # re.S匹配换行符 可以多行匹配
        # 先抓取shortcode，来拼接详情页面的网址 www.instagram.com/p/shortcode/?taken-by=xxx
        short_code_list = re.findall('\"shortcode\": ?\"([^\"]+?)\", ?\"', html.content, re.S)
        # print short_code_list
        detail_html_list = []

        dir = blogger
        video_path = "video" + os.path.sep + dir
        mkdir(video_path)
        img_path = "img" + os.path.sep + dir
        mkdir(img_path)
        if copy_new:
            new_img_path = "img" + os.path.sep + "new" + os.path.sep + dir
            mkdir(new_img_path)
            new_video_path = "video" + os.path.sep + "new" + os.path.sep + dir
            mkdir(new_video_path)

        for shortcode in short_code_list:
            detail_html_list.append("https://www.instagram.com/p/" + shortcode + '/?taken-by=' + blogger)
        # print detail_html_list
        for detail_html in detail_html_list:
            detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=False)
            # print detail_html_content.content
            if detail_html_content:
                INSTAGRAM_LOGGER.info(blogger + ': detail page ' + detail_html)
                if 'video_url' in detail_html_content.content:
                    videos = re.findall('\"video_url+\": ?\"([^\"]+?)\", ?\"',
                                        detail_html_content.content, re.S)
                    # remove_tag(videos)
                    INSTAGRAM_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
                    if videos:
                        videos = unicode_escape(videos)
                        save_video(video_path, videos, copy_new)
                    else:
                        INSTAGRAM_LOGGER.warn(blogger + ': Fail to get video(s) on ' + detail_html)

                img_list = re.findall(prey.page_reg, detail_html_content.content, re.S)
                # remove_tag(img_list)
                if img_list:
                    img_list = unicode_escape(img_list)
                    # 只有一个的，就抓那一个；两个以上的，从第二个开始抓取，去掉重复的
                    if len(img_list) > 1:
                        img_list = img_list[1:]
                    INSTAGRAM_LOGGER.info(blogger + ': images ' + ' '.join(img_list))

                    save_img(img_path, img_list, copy_new)
                else:
                    
                    INSTAGRAM_LOGGER.warn(blogger + ': Fail to get image(s) on ' + detail_html)
            else:
                
                INSTAGRAM_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)

        id = re.findall("\"id\": ?\"(\d+)\", ?\"username", html.content, re.S)[0]
        # print id
        #query_id = 17862015703145017
        query_hash = ''
        count = 0
        queryHashChangeCount = 0
        # self.query2alive(id)
        # 有下拉页需要抓取，使用伪造的query_id配合页面的end_cursor，组建需要抓取的下一页信息
        while html.content.find("has_next_page\":true") != -1 and count < next_curosr_num:
            count += 1
            # print "next cursor:" + str(count)
            INSTAGRAM_LOGGER.info(blogger + ': next cursor:' + str(count))
            end_cursor = re.findall("\"end_cursor\": ?\"([^\"]+?)\"", html.content, re.S)[0]
            # print end_cursor
            if not query_hash:
                query_hash = QUERY_HASH_LIST[queryHashChangeCount]
            # next_page = "https://www.instagram.com/graphql/query/?query_id=" + str(query_id) \
            #            + "&variables=%7B%22id%22%3A%22" + id + "%22%2C%22first%22%3A12%2C%22after%22%3A%22" + end_cursor + "%22%7D"
            next_page = "https://www.instagram.com/graphql/query/?query_hash=" + str(query_hash) \
                       + "&variables=%7B%22id%22%3A%22" + id + "%22%2C%22first%22%3A12%2C%22after%22%3A%22" + end_cursor + "%22%7D"
            # print next_page
            nextHtml = spider.getHtml(next_page, timeout=10, retries=2, proxy=True)
            if nextHtml:
                INSTAGRAM_LOGGER.info(blogger + ': next cursor page ' + next_page)
                # print re.findall(prey.page_reg, nextweb.content, re.S)
                # 先抓取shortcode，来拼接详情页面的网址 www.instagram.com/p/shortcode/?taken-by=xxx
                short_code_list = re.findall('\"shortcode\": ?\"([^\"]+?)\", ?\"', html.content, re.S)
                # print short_code_list
                detail_html_list = []
                for shortcode in short_code_list:
                    detail_html_list.append(
                        "https://www.instagram.com/p/" + shortcode + '/?taken-by=' + blogger)
                # print detail_html_list
                # print len(detail_html_list)

                for detail_html in detail_html_list:
                    detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=True)
                    # print detail_html_content.content

                    if detail_html_content:
                        INSTAGRAM_LOGGER.info(blogger + ': detail page ' + detail_html)
                        if 'video_url' in detail_html_content.content:
                            videos = re.findall('\"video_url+\": ?\"([^\"]+?)\", ?\"',
                                                detail_html_content.content, re.S)
                            # print videos
                            INSTAGRAM_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
                            if videos:
                                # dir = prey.page.split('/')[-1]
                                # path = "video" + os.path.sep + dir
                                # self.mkdir(path)
                                # if copy_new == 1:
                                #     newpath = "video" + os.path.sep + "new" + os.path.sep + dir
                                #     self.mkdir(newpath)
                                videos = unicode_escape(videos)
                                save_video(video_path, videos, copy_new)
                            else:
                                # print 'Fail to get ' + blogger + ' \'s video on ' + detail_html
                                INSTAGRAM_LOGGER.warn(blogger + ': Fail to get video(s) on ' + detail_html)

                        img_list = re.findall(prey.page_reg, detail_html_content.content, re.S)
                        if img_list:
                            img_list = unicode_escape(img_list)
                            # 只有一个的，就抓那一个；两个以上的，从第二个开始抓取，去掉重复的
                            if len(img_list) > 1:
                                img_list = img_list[1:]
                            # print img_list
                            INSTAGRAM_LOGGER.info(blogger + ': image(s) ' + ' '.join(img_list))

                            # dir = prey.page.split('/')[-1]
                            # path = "img" + os.path.sep + dir
                            # self.mkdir(path)
                            # if copy_new == 1:
                            #     newpath = "img" + os.path.sep + "new" + os.path.sep + dir
                            #     self.mkdir(newpath)

                            save_img(img_path, img_list, copy_new)
                        else:
                            # print 'Fail to get ' + blogger + ' \'s images on ' + detail_html
                            INSTAGRAM_LOGGER.warn(blogger + ': Fail to get image(s) on ' + detail_html)

                    else:
                        # print 'Fail to get ' + blogger + ' \'s detail web:' + detail_html
                        INSTAGRAM_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)

                        # result = re.findall("\"display_url\": ?\"([^\"]+?)\", ?\"", html.content, re.S)
                        # if result:
                        #     dir = prey.page.split('/')[-1]
                        #     path = "img" + os.path.sep + dir
                        #     self.mkdir(path)
                        #     if copy_new == 1:
                        #         newpath = "img" + os.path.sep + "new" + os.path.sep + dir
                        #         self.mkdir(newpath)
                        #     self.save_img(path, result, copy_new)
                        # else:
                        #     print 'Get proxy through regs failed!!'

                html = nextHtml
            else:
                # print 'Get ' + prey.page + ' next cursor ' + str(count) + ' failed!!'
                INSTAGRAM_LOGGER.warn(blogger + ': Fail to get ' + str(count) + ' cursor ' + next_page)

                queryHashChangeCount = queryHashChangeCount + 1
                if queryHashChangeCount == len(QUERY_HASH_LIST):
                    # 使用完了QUERY_HASH_LIST里所有的query_hash，需要等待一定的时间，再从头使用列表里的值
                    time.sleep(120)
                    INSTAGRAM_LOGGER.info(blogger + ': Reuse query_hash in QUERY_HASH_LIST.')
                    queryHashChangeCount = 0
                    query_hash = ''
                    count = count - 1
                else:
                    # 获取新的query_hash重新尝试,重置翻页计数，并统计更换quert_hash的次数，并在更换次数达到QUERY_HASH_LIST长度后，等待一定时间，重新从列表拿取query_hash尝试
                    INSTAGRAM_LOGGER.info(blogger + ': Refresh query_hash by ' + str(queryHashChangeCount) + ' time.')
                    query_hash = ''
                    count = count - 1
    else:
        # print 'Get ' + prey.page + ' failed!!'
        INSTAGRAM_LOGGER.warn(blogger + ': Fail to get ' + prey.page)


def spider_one_instagram_blogger_full(prey, copy_new=True):
    spider = ipProxySpider()
    blogger = prey.page.split('/')[-1]
    html = spider.getHtml(prey.page, timeout=10, retries=2, proxy=False)
    # self.batch_fetch_web()
    if html:
        INSTAGRAM_LOGGER.info(blogger + ': main page ' + prey.page)
        # print html.content
        # re.S匹配换行符 可以多行匹配
        # 先抓取shortcode，来拼接详情页面的网址 www.instagram.com/p/shortcode/?taken-by=xxx
        short_code_list = re.findall('\"shortcode\": ?\"([^\"]+?)\", ?\"', html.content, re.S)
        # print short_code_list
        detail_html_list = []

        dir = blogger
        video_path = "video" + os.path.sep + dir
        mkdir(video_path)
        img_path = "img" + os.path.sep + dir
        mkdir(img_path)
        if copy_new:
            new_img_path = "img" + os.path.sep + "new" + os.path.sep + dir
            mkdir(new_img_path)
            new_video_path = "video" + os.path.sep + "new" + os.path.sep + dir
            mkdir(new_video_path)

        for shortcode in short_code_list:
            detail_html_list.append("https://www.instagram.com/p/" + shortcode + '/?taken-by=' + blogger)
        # print detail_html_list
        for detail_html in detail_html_list:
            detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=False)
            # print detail_html_content.content
            if detail_html_content:
                INSTAGRAM_LOGGER.info(blogger + ': detail page ' + detail_html)
                if 'video_url' in detail_html_content.content:
                    videos = re.findall('\"video_url+\": ?\"([^\"]+?)\", ?\"',
                                        detail_html_content.content, re.S)
                    # remove_tag(videos)
                    INSTAGRAM_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
                    if videos:
                        videos = unicode_escape(videos)
                        save_video(video_path, videos, copy_new)
                    else:
                        INSTAGRAM_LOGGER.warn(blogger + ': Fail to get video(s) on ' + detail_html)

                img_list = re.findall(prey.page_reg, detail_html_content.content, re.S)
                # remove_tag(img_list)
                if img_list:
                    img_list = unicode_escape(img_list)
                    # 只有一个的，就抓那一个；两个以上的，从第二个开始抓取，去掉重复的
                    if len(img_list) > 1:
                        img_list = img_list[1:]
                    INSTAGRAM_LOGGER.info(blogger + ': image(s) ' + ' '.join(img_list))

                    save_img(img_path, img_list, copy_new)
                else:

                    INSTAGRAM_LOGGER.warn(blogger + ': Fail to get image(s) on ' + detail_html)
            else:
                INSTAGRAM_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)

        # 获取第一页的帖子数
        pageInfoCount = len(short_code_list)
        # 获取这个ins总共有多个帖子
        pageInfoNum = int(
            re.findall('\"edge_owner_to_timeline_media\":{\"count\": ?([^\"]+?), ?\"', html.content, re.S)[0])
        INSTAGRAM_LOGGER.info(blogger + ": Get " + str(pageInfoCount) + ' out of ' + str(pageInfoNum) + ' .')

        id = re.findall("\"id\": ?\"(\d+)\", ?\"username", html.content, re.S)[0]
        # print id
        # query_id = 17862015703145017
        query_hash = ''
        count = 0
        queryHashChangeCount = 0
        # self.query2alive(id)
        # 有下拉页需要抓取，使用伪造的query_id配合页面的end_cursor，组建需要抓取的下一页信息，同时在获取的帖子数大于等于总共有的帖子数的时候停止
        while html.content.find("has_next_page\":true") != -1 and pageInfoCount < pageInfoNum:
            count += 1
            # print "next cursor:" + str(count)
            INSTAGRAM_LOGGER.info(blogger + ": next cursor:" + str(count))
            end_cursor = re.findall("\"end_cursor\": ?\"([^\"]+?)\"", html.content, re.S)[0]
            #query_hash为空的话，从QUERY_HASH_LIST的指定位置获取query_hash
            if not query_hash:
                query_hash = QUERY_HASH_LIST[queryHashChangeCount]
            # print end_cursor
            # next_page = "https://www.instagram.com/graphql/query/?query_id=" + str(query_id) \
            #            + "&variables=%7B%22id%22%3A%22" + id + "%22%2C%22first%22%3A12%2C%22after%22%3A%22" + end_cursor + "%22%7D"
            next_page = "https://www.instagram.com/graphql/query/?query_hash=" + str(query_hash) \
                        + "&variables=%7B%22id%22%3A%22" + id + "%22%2C%22first%22%3A12%2C%22after%22%3A%22" + end_cursor + "%22%7D"
            # print next_page
            nextHtml = spider.getHtml(next_page, timeout=10, retries=2, proxy=True)
            if nextHtml:
                INSTAGRAM_LOGGER.info(blogger + ': next cursor page ' + next_page)
                # print re.findall(prey.page_reg, nextweb.content, re.S)
                # 先抓取shortcode，来拼接详情页面的网址 www.instagram.com/p/shortcode/?taken-by=xxx
                short_code_list = re.findall('\"shortcode\": ?\"([^\"]+?)\", ?\"', html.content, re.S)
                # print short_code_list
                detail_html_list = []
                blogger = prey.page.split('/')[-1]
                for shortcode in short_code_list:
                    detail_html_list.append(
                        "https://www.instagram.com/p/" + shortcode + '/?taken-by=' + blogger)
                # print detail_html_list
                # print len(detail_html_list)

                for detail_html in detail_html_list:
                    detail_html_content = spider.getHtml(detail_html, timeout=10, retries=2, proxy=True)
                    # print detail_html_content.content

                    if detail_html_content:
                        INSTAGRAM_LOGGER.info(blogger + ': detail page ' + detail_html)
                        if 'video_url' in detail_html_content.content:
                            videos = re.findall('\"video_url+\": ?\"([^\"]+?)\", ?\"',
                                                detail_html_content.content, re.S)
                            # print videos
                            INSTAGRAM_LOGGER.info(blogger + ': video(s) ' + ' '.join(videos))
                            if videos:
                                # dir = prey.page.split('/')[-1]
                                # path = "video" + os.path.sep + dir
                                # self.mkdir(path)
                                # if copy_new == 1:
                                #     newpath = "video" + os.path.sep + "new" + os.path.sep + dir
                                #     self.mkdir(newpath)
                                videos = unicode_escape(videos)
                                save_video(video_path, videos, copy_new)
                            else:
                                # print 'Fail to get ' + blogger + ' \'s video on ' + detail_html
                                INSTAGRAM_LOGGER.warn(blogger + ': Fail to get video(s) on ' + detail_html)

                        img_list = re.findall(prey.page_reg, detail_html_content.content, re.S)
                        if img_list:
                            img_list = unicode_escape(img_list)
                            # 只有一个的，就抓那一个；两个以上的，从第二个开始抓取，去掉重复的
                            if len(img_list) > 1:
                                img_list = img_list[1:]
                            # print img_list
                            INSTAGRAM_LOGGER.info(blogger + ': image(s) ' + ' '.join(img_list))

                            # dir = prey.page.split('/')[-1]
                            # path = "img" + os.path.sep + dir
                            # self.mkdir(path)
                            # if copy_new == 1:
                            #     newpath = "img" + os.path.sep + "new" + os.path.sep + dir
                            #     self.mkdir(newpath)

                            save_img(img_path, img_list, copy_new)
                        else:
                            # print 'Fail to get ' + blogger + ' \'s images on ' + detail_html
                            INSTAGRAM_LOGGER.warn(blogger + ': Fail to get image(s) on ' + detail_html)

                    else:
                        # print 'Fail to get ' + blogger + ' \'s detail web:' + detail_html
                        INSTAGRAM_LOGGER.warn(blogger + ': Fail to get detail web ' + detail_html)

                        # result = re.findall("\"display_url\": ?\"([^\"]+?)\", ?\"", html.content, re.S)
                        # if result:
                        #     dir = prey.page.split('/')[-1]
                        #     path = "img" + os.path.sep + dir
                        #     self.mkdir(path)
                        #     if copy_new == 1:
                        #         newpath = "img" + os.path.sep + "new" + os.path.sep + dir
                        #         self.mkdir(newpath)
                        #     self.save_img(path, result, copy_new)
                        # else:
                        #     print 'Get proxy through regs failed!!'

                pageInfoCount = pageInfoCount + len(short_code_list)
                INSTAGRAM_LOGGER.info(blogger + ": Get " + str(pageInfoCount) + ' out of ' + str(pageInfoNum) + ' .')
                html = nextHtml
            else:
                # print 'Get ' + prey.page + ' next cursor ' + str(count) + ' failed!!'
                INSTAGRAM_LOGGER.warn(blogger + ': Fail to get ' + str(count) + ' cursor ' + next_page)

                queryHashChangeCount = queryHashChangeCount + 1
                if queryHashChangeCount == len(QUERY_HASH_LIST):
                    #使用完了QUERY_HASH_LIST里所有的query_hash，需要等待一定的时间，再从头使用列表里的值
                    time.sleep(120)
                    INSTAGRAM_LOGGER.info(blogger + ': Reuse query_hash in QUERY_HASH_LIST.')
                    queryHashChangeCount = 0
                    query_hash = ''
                    count = count - 1
                else:
                    #获取新的query_hash重新尝试,重置翻页计数，并统计更换quert_hash的次数，并在更换次数达到QUERY_HASH_LIST长度后，等待一定时间，重新从列表拿取query_hash尝试
                    INSTAGRAM_LOGGER.info(blogger + ': Refresh query_hash by ' + str(queryHashChangeCount) + ' time.')
                    query_hash = ''
                    count = count - 1

    else:
        # print 'Get ' + prey.page + ' failed!!'
        INSTAGRAM_LOGGER.warn(blogger + ': Fail to get ' + prey.page)

def save_img(path, result, copy_new=True):
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
                img = spider.getHtml(item, timeout=10, retries=2, proxy=False)
                if img:
                    f = open(img_file_name, 'ab')
                    f.write(img.content)
                    f.close()
                    if copy_new:
                        directory = path.split(os.path.sep)[-1]
                        filename = item.split('/')[-1].split('?')[0]
                        new_file = "img" + os.path.sep + "new" + os.path.sep + directory + os.path.sep + filename
                        f = open(new_file, 'ab')
                        f.write(img.content)
                        f.close()
                    down_load_count += 1
                    # print item + ' downloads successfully.'
                    INSTAGRAM_LOGGER.info(path.split(os.path.sep)[-1] + ': successfully downloads ' + item)
                else:
                    # print item + " downloads failed."
                    INSTAGRAM_LOGGER.warn(path.split(os.path.sep)[-1] + ': fail to downloads ' + item)

        # if down_load_count == total and down_load_count > 0:
        #     print "save all pics of this page."
        # else:
        #     print "save some of pics failed!"



def save_video(path, videos, copy_new=0):
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

                video = spider.getHtml(item, timeout=10, retries=2, proxy=False)
                if video:
                    with open(video_file_name, 'wb') as f:
                        f.write(video.content)
                    if copy_new:
                        directory = path.split(os.path.sep)[-1]
                        filename = item.split('/')[-1].split('?')[0]
                        new_file = "video" + os.path.sep + "new" + os.path.sep + directory + os.path.sep + filename
                        with open(new_file, 'wb') as f:
                            f.write(video.content)
                    down_load_count += 1
                    # print item + ' downloads successfully.'
                    INSTAGRAM_LOGGER.info(path.split(os.path.sep)[-1] + ': successfully downloads ' + item)
                else:
                    # print item + " downloads failed."
                    INSTAGRAM_LOGGER.warn(path.split(os.path.sep)[-1] + ': fail to downloads ' + item)

        # if down_load_count == total and down_load_count > 0:
        #     print "save all videos of this page."
        # else:
        #     print "save some of videos failed!"

def mkdir(path):
    path = path.strip()
    isExists = os.path.exists(path)
    if not isExists:
        # print u'建了一个名字叫做', path, u'的文件夹！'
        INSTAGRAM_LOGGER.info(u'建了一个名字叫做' + path + u'的文件夹！')
        # 递归创建文件夹
        os.makedirs(os.path.join(".", path))
        return True
    else:
        # print u'名字叫做', path, u'的文件夹已经存在了！'
        INSTAGRAM_LOGGER.debug(u'名字叫做' +  path + u'的文件夹已经存在了！')
        return False

def spider_mutilecpu(next_curosr_num, copy_new = 1):
    preylist = get_prey_list()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for prey in preylist:
            executor.submit(spider_one_instagram_blogger, prey, next_curosr_num, copy_new)

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

# def batch_fetch_web(self):
#     posthtml = "https://www.instagram.com/qp/batch_fetch_web"
#     surfaces_to_queries = {"5095":"viewer() {\n  eligible_promotions.surface_nux_id(<surface>).external_gating_permitted_qps(<external_gating_permitted_qps>) {\n    edges {\n      priority,\n      time_range {\n        start,\n        end\n      },\n      node {\n        id,\n        promotion_id,\n        max_impressions,\n        triggers,\n        template {\n          name,\n          parameters {\n            name,\n            string_value\n          }\n        },\n        creatives {\n          title {\n            text\n          },\n          content {\n            text\n          },\n          footer {\n            text\n          },\n          social_context {\n            text\n          },\n          primary_action{\n            title {\n              text\n            },\n            url,\n            limit,\n            dismiss_promotion\n          },\n          secondary_action{\n            title {\n              text\n            },\n            url,\n            limit,\n            dismiss_promotion\n          },\n          dismiss_action{\n            title {\n              text\n            },\n            url,\n            limit,\n            dismiss_promotion\n          },\n          image {\n            uri\n          }\n        }\n      }\n    }\n  }\n}","5780":"viewer() {\n  eligible_promotions.surface_nux_id(<surface>).external_gating_permitted_qps(<external_gating_permitted_qps>) {\n    edges {\n      priority,\n      time_range {\n        start,\n        end\n      },\n      node {\n        id,\n        promotion_id,\n        max_impressions,\n        triggers,\n        template {\n          name,\n          parameters {\n            name,\n            string_value\n          }\n        },\n        creatives {\n          title {\n            text\n          },\n          content {\n            text\n          },\n          footer {\n            text\n          },\n          social_context {\n            text\n          },\n          primary_action{\n            title {\n              text\n            },\n            url,\n            limit,\n            dismiss_promotion\n          },\n          secondary_action{\n            title {\n              text\n            },\n            url,\n            limit,\n            dismiss_promotion\n          },\n          dismiss_action{\n            title {\n              text\n            },\n            url,\n            limit,\n            dismiss_promotion\n          },\n          image {\n            uri\n          }\n        }\n      }\n    }\n  }\n}"}
#     data = {"surfaces_to_queries": surfaces_to_queries, "vc_policy": 'default', 'version':'1'}
#     response = self.spider.postHtml(posthtml, data)
#     print(response.status_code)
#     print(response.content)
#
#
#
#
# def query2alive(self, user_id, query_hash="7c16654f22c819fb63d1183034a5162f"):
#     page = "https://www.instagram.com/graphql/query/?query_hash=" + query_hash \
#                + "&variables=%7B%22user_id%22%3A%22" + str(user_id) + "%22%2C%22include_chaining%22%3Afalse%2C%22include_reel%22%3Afalse%2C%22include_suggested_users%22%3Afalse%2C%22include_logged_out_extras%22%3Atrue%2C%22include_highlight_reels%22%3Afalse%7D"
#     print page
#     cookie = dict(
#         mid="WZpgvgAEAAGG_iVhMsPPgmROmB4d",
#               csrftoken="Q11AZtimliu1XPBNwSxrGtct2BXJtoS4",
#                           rur="ASH",
#                                 ig_vw="1680",
#                                         ig_pr="1",
#                                                 ig_vh="919",
#                                                         ig_or="landscape-primary",
#                                                               urlgen="\"{\"time\": 1523432755\054 \"103.65.40.65\": 135391}:1f6BGe:b1V-Mng7TDFII2ItHc4jF3lSbcQ\""
#     )
#     #print cookie
#     #self.spider.get_html_with_cookie(page, cookie)
#     responesePage = self.spider.getHtml(page, timeout=10, retries=2, proxy=False)
#     print responesePage
#
#
# def logging_client_events(self, content, url):
#     posthtml = "https://graph.instagram.com/logging_client_events"
#     access_token = "1217981644879628|65a937f07619e8d4dce239c462a447ce"
#     app_id = "1217981644879628"
#     timelist = [(int(round(time.time() * 1000)) + x) / 1000.0 for x in range(13)]
#     mediaId = re.findall("\"id\": ?\"(\d+)\", ?\"edge_media_to_caption", content, re.S)
#     #print mediaId
#     client_time = timelist[12] * 100
#     time_spent_id = "ve2efg"
#     session_id = "162b3daea5a-4019d4"
#     device_id = "WZpgvgAEAAGG_iVhMsPPgmROmB4d"
#     message = {"app_id":app_id,"app_ver":"1.0",
#     "data":[{"time":timelist[0],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[0],"loadTime":38,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[1],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[1],"loadTime":38,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[2],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[2],"loadTime":38,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[3],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[3],"loadTime":37,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[4],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[4],"loadTime":37,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[5],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[5],"loadTime":37,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[6],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[6],"loadTime":36,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[7],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[7],"loadTime":36,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[8],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[8],"loadTime":36,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[9],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[9],"loadTime":40,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[10],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[10],"loadTime":40,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[11],"name":"ig_web_image_loading","extra":{"isGridView":"true","mediaId":mediaId[11],"loadTime":40,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":timelist[12],"name":"instagram_web_time_spent_navigation","extra":{"qe":{"loggedout":"launch"},"event":"unload","client_time":client_time,"time_spent_id":time_spent_id,"extra_data":{},"source_endpoint":"profilePage","referrer":"","referrer_domain":"","url":url,"original_referrer":"","original_referrer_domain":""}}],
#     "log_type":"client_event","seq":1,"session_id":session_id,"device_id":device_id}
#     data = {"access_token":access_token,"message":message}
#     print data
#
#     """{"app_id":"1217981644879628","app_ver":"1.0",
#     "data":[{"time":1523346917.341,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1750391651047676908","loadTime":38,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.341,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1748988669252868588","loadTime":38,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.341,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1747685318124998996","loadTime":38,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.341,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1747259813877809952","loadTime":37,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.341,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1746604098083360659","loadTime":37,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.341,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1746191164435723717","loadTime":37,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.341,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1745142357319263299","loadTime":36,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.341,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1743723516232184921","loadTime":36,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.341,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1743593828067296052","loadTime":36,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.342,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1742309108205244439","loadTime":40,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.342,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1741508213691581362","loadTime":40,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.342,"name":"ig_web_image_loading","extra":{"isGridView":true,"mediaId":"1740037137287422445","loadTime":40,"percentRendered":100,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523346917.342,"name":"instagram_web_time_spent_navigation","extra":{"qe":{"loggedout":"launch"},"event":"unload","client_time":1523346917342,"time_spent_id":"uzuktv","extra_data":{},"source_endpoint":"profilePage","referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""}}],
#     "log_type":"client_event","seq":1,"session_id":"162ae8d3f32-1a9772","device_id":"WZpgvgAEAAGG_iVhMsPPgmROmB4d"}"""
#
#     """{"app_id":"1217981644879628","app_ver":"1.0",
#     "data":[{"time":1523432755.936,"name":"instagram_web_time_spent_navigation","extra":{"qe":{"loggedout":"launch"},"event":"load","client_time":1523432755934,"time_spent_id":"navm6a","extra_data":{},"dest_endpoint":"profilePage","referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""}},
#             {"time":1523432755.943,"name":"instagram_web_interaction_perf_events","extra":{"eventType":"asyncSwitch","orig":"","origId":"","dest":"profilePage","destId":"/justintimberlake/","timeTaken":43,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""}},
#             {"time":1523432755.944,"name":"instagram_web_client_events","extra":{"event_type":"page_view","qe":{"loggedout":"launch"},"page_id":"profilePage_303054725","referrer":"","referrer_domain":"","original_referrer":"","original_referrer_domain":""},"module":"profilePage","obj_type":"url","obj_id":"/justintimberlake/"},
#             {"time":1523432755.946,"name":"instagram_web_resource_transfer_size_events","extra":{"resource_type":"script","resources_count":4,"transfer_size":207275,"full_page_load":true,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""},"module":"profilePage"},
#             {"time":1523432756.298,"name":"instagram_web_graphql_timing_events","extra":{"query_hash":"bfe6fc64e0775b47b311fc0398df88a9","query_time":360,"qe":{"loggedout":"launch"},"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""}},
#             {"time":1523432756.516,"name":"instagram_web_time_spent_bit_array","extra":{"qe":{"loggedout":"launch"},"tos_id":"navm6a","start_time":1523432755,"tos_array":[3,0],"tos_len":2,"tos_seq":0,"tos_cum":2,"log_time":1523432756516,"referrer":"","referrer_domain":"","url":"/justintimberlake/","original_referrer":"","original_referrer_domain":""}},
#             {"time":1523432757.262,"name":"instagram_web_client_perf_events","extra":{"qe":{"loggedout":"launch"},"redirects":1296,"dns":0,"connect":0,"request":467,"response":4,"network":1298,"domInteractive":435,"domContentLoaded":435,"domComplete":1002,"loadEvent":1003,"displayDone":2300,"timeToInteractive":2300,"firstPaint":null,"firstContentfulPaint":null,"reactReady":382,"reactRender":51,"referrer":"","referrer_domain":"","original_referrer":"","original_referrer_domain":""},"module":"ProfilePage","obj_type":"url","obj_id":"/justintimberlake/"},
#             {"time":1523432758.265,"name":"device_status","extra":{"locale":"zh-CN"}},{"time":1523432758.265,"name":"device_id","extra":{"user_agent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36","screen_height":1010,"screen_width":1680,"density":null,"platform":"Win32","locale":"zh-CN"}}],"log_type":"client_event","seq":0,"session_id":"162b3ab12e0-f75e72","device_id":"WZpgvgAEAAGG_iVhMsPPgmROmB4d"}
#     """
#     self.spider.postHtml(posthtml, data)
#
# def ajax_bx(self):
#     posthtml = "https://www.instagram.com/ajax/bz"
#     page_id = "ve2efg"
#     mid = "WZpgvgAEAAGG_iVhMsPPgmROmB4d"
#     ts = (int(round(time.time() * 1000)))
#
#     q = [{"page_id":page_id,"posts":[["qe:expose",{"qe":"loggedout","mid":mid},ts - 3,0]],"trigger":"qe:expose","send_method":"ajax"}]
#     data = {"q": q, "ts": ts}
#
#     print data
#     """[{"page_id":"navm6a","posts":[["qe:expose",{"qe":"loggedout","mid":"WZpgvgAEAAGG_iVhMsPPgmROmB4d"},1523432755905,0]],"trigger":"qe:expose","send_method":"ajax"}]"""
#
#     self.spider.postHtml(posthtml, data)

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
    # prey_list = []
    # for blogger in ['mavrin', 'mavrin_film', 'mavrin_models', 'mavrinland', 'mavrinmag', 'mavrinstudios', 'maximmag_kr', 'mmodels_agency', '007natalee', 'n.lee007', 'natalee.007', 'olgademar']:
    #     prey = SpiderPrey()
    #     page = "https://www.instagram.com/" + blogger#  mavrin_film mavrin_models mavrinland mavrinmag mavrinstudios maximmag_kr mmodels_agency 007natalee n.lee007 natalee.007 olgademar
    #     reg = "\"display_[a-z]+\": *\"([^\"]+?)\", *\""
    #     prey.catalogue = "null"
    #     prey.catalogue_reg = "null"
    #     prey.page = page
    #     prey.next_page = "null"
    #     prey.page_reg = reg
    #     prey_list.append(prey)

    prey_list = get_prey_list()

    # #用来截取，从某一个网页（包含该网页）之后的页面数据
    # start = 0
    # for prey in prey_list:
    #     if prey.page == 'https://www.instagram.com/kiligkira11':
    #         break
    #     start += 1
    # prey_list = prey_list[start:]

    #按照获取的list，爬取数字指定的页码的数据
    spider_mutile_cpu(prey_list, 0, True)
    # 按照获取的list，爬取网页的全部数据
    #use_mutile_cpu(prey_list, spider_one_instagram_blogger_full)
    #只爬一个ins的全部数据
    #spider_one_instagram_blogger_full(prey_list[0])


