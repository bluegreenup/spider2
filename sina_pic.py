# -*- coding: utf-8 -*-
import json
import requests
import time
import os
import re
from requests.cookies import RequestsCookieJar
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import logging
from logging.handlers import RotatingFileHandler
import sina_login

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    )
SINA_PIC_LOGGER = logging.getLogger(__name__)
SINA_PIC_ROTATING_FILE_HANDLER = RotatingFileHandler('./log/info.log', maxBytes=100 * 1024 * 1024, backupCount=10)
SINA_PIC_ROTATING_FILE_HANDLER.setLevel(logging.DEBUG)
SINA_PIC_ROTATING_FILE_HANDLER.setFormatter(logging.Formatter(
    '[%(levelname)s] %(asctime)s %(filename)s[line:%(lineno)d] %(message)s'))
SINA_PIC_LOGGER.addHandler(SINA_PIC_ROTATING_FILE_HANDLER)

user_agents = ['Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',]
header = {
            "User-Agent": user_agents[0],
            # "Host": url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            #"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            # "Referer": url,
            "Connection": "keep-alive",
            # "Cache-Control":"max-age=0",
        }

def spider_img_requests(large_img_url, owner_uid, album_id, album_photo_ids):
    img_path = "img" + os.path.sep + str(owner_uid) + os.path.sep + str(album_id)
    mkdir(img_path)

    jar = RequestsCookieJar()
    with open("conf/sinacookies.txt", "r") as fp:
        cookies = json.load(fp)
        for cookie in cookies:
            jar.set(cookie['name'], cookie['value'])

    # jar = {}
    # cookies = {}
    # with open("conf/sinacookies.txt", "r") as fp:
    #     cookies = json.load(fp)
    # for cookie in cookies:
    #     jar[cookie['name']] = cookie['value']

    s = requests.session()
    s.verify = False
    s.headers = header

    for photo_id in album_photo_ids:
        # r = s.get("http://photo.weibo.com/3253743361/wbphotos/large/photo_id/4300596959980112/album_id/3573653261396014", cookies=jar)
        # print(r.content)
        url = large_img_url % (str(owner_uid), str(photo_id), str(album_id))
        SINA_PIC_LOGGER.info(url)
        try:
            response = s.get(url, cookies=jar, verify=False)
            SINA_PIC_LOGGER.info(response.status)
            if response:
                imgurl = re.findall('<img id=\"pic\" src=\"([^\"]+?)\" ?', response.content, re.S)
                SINA_PIC_LOGGER.info(imgurl)
                SINA_PIC_LOGGER.info('Img download1.')
                img = s.get(imgurl, cookies=jar, verify=False)
                SINA_PIC_LOGGER.info('Img download.')
                if img:
                    SINA_PIC_LOGGER.info('Img downloads successfully.')
                    save_img(img_path, img)
                else:
                    SINA_PIC_LOGGER.warn('Fail to get img.')
            else:
                SINA_PIC_LOGGER.warn('Fail to get detail web.')
        except:
            SINA_PIC_LOGGER.warn('Fail to get web.')
        #愚蠢的反扒
        time.sleep(1)

def spider_img_selenium(large_img_url, owner_uid, album_id, album_photo_ids, driver):
    driver.implicitly_wait(2)

    # img_path = "img" + os.path.sep + str(owner_uid) + os.path.sep + str(album_id)
    # mkdir(img_path)

    SINA_PIC_LOGGER.info('%d imgs to be downloaded.' % (len(album_photo_ids)))
    for photo_id in album_photo_ids:
        url = large_img_url % (str(owner_uid), str(photo_id), str(album_id))
        SINA_PIC_LOGGER.info(url)
        driver.get(url)
        if 'login.php?' in driver.current_url:
            WebDriverWait(driver, 10, 0.5).until(
                expected_conditions.element_to_be_clickable((By.XPATH, '//a[@action-type="btn_submit"]')))
            element = driver.find_element_by_xpath('//input[@id="loginname"]')
            username = raw_input('输入用户名：')
            element.send_keys(username)

            element = driver.find_element_by_xpath('//input[@type="password"]')
            password = raw_input('输入密码：')
            element.send_keys(password)

            element = driver.find_element_by_xpath('//a[@action-type="btn_submit"]')
            element.click()

        try:
            WebDriverWait(driver, 10, 0.5).until(
                expected_conditions.visibility_of_element_located((By.XPATH, '//img[@id="pic"]')))
        except TimeoutException:
            if '该照片不存在'.decode('utf-8') in driver.find_element_by_xpath('//p[@class="txt M_txtb"]').text:
                SINA_PIC_LOGGER.info('该照片不存在')
            else:
                SINA_PIC_LOGGER.warn('获取大图地址超时')
            continue
        element = driver.find_element_by_xpath('//img[@id="pic"]')
        img_url = element.get_attribute('src')
        SINA_PIC_LOGGER.info(img_url)
        with open("data/sina_img_urls.txt", "a+") as f:
            f.write(img_url)
            f.write('\n')
        # save_img(img_path, img_url, driver.get(img_url).page)

        # action = ActionChains(driver).move_to_element(element)
        # action.context_click(element)
        # action.send_keys(Keys.ARROW_DOWN)
        # action.send_keys('V')
        # action.perform()

def mkdir(path):
    path = path.strip()
    isExists = os.path.exists(path)
    if not isExists:
        # print u'建了一个名字叫做', path, u'的文件夹！'
        SINA_PIC_LOGGER.info(u'建了一个名字叫做' + path + u'的文件夹！')
        # 递归创建文件夹
        os.makedirs(os.path.join(".", path))
        return True
    else:
        # print u'名字叫做', path, u'的文件夹已经存在了！'
        SINA_PIC_LOGGER.debug(u'名字叫做' +  path + u'的文件夹已经存在了！')
        return False


def save_img(path, img):
    img_file_name = path + os.path.sep + img.split('/')[-1].split('?')[0]
    if os.path.exists(img_file_name):
        SINA_PIC_LOGGER.info(img_file_name + ' exists.')
        pass
    else:
        with open(img_file_name, 'ab') as f:
            f.write(img.coment)
            SINA_PIC_LOGGER.info(img_file_name + ' saves successfully.')


if __name__ == '__main__':
    driver = sina_login.sina_login()
    # driver = sina_login.sina_login_with_cookie()
    #微博用户图片详情页获取以下信息
    large_img_url = "http://photo.weibo.com/%s/wbphotos/large/photo_id/%s/album_id/%s"
    owner_uid = 1925950032
    album_id = 3561864429362712
    album_photo_ids = [4315305371726080,4315305371726079]
    spider_img_selenium(large_img_url, owner_uid, album_id, album_photo_ids, driver)