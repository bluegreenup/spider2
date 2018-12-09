# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
import json
import requests
import time

#手动输入用户名和密码，并在登录后保存cookies
def sina_login():
    driver = webdriver.Chrome()
    driver.get("https://weibo.com/")
    driver.maximize_window()
    # driver.close()

    #等待登录按钮可以点击后，开始输入用户名和密码
    WebDriverWait(driver, 10, 0.5).until(expected_conditions.element_to_be_clickable((By.XPATH, '//a[@action-type="btn_submit"]')))
    element = driver.find_element_by_xpath('//input[@id="loginname"]')
    username = raw_input('输入用户名：')
    element.send_keys(username)

    element = driver.find_element_by_xpath('//input[@type="password"]')
    password = raw_input('输入密码：')
    element.send_keys(password)

    element = driver.find_element_by_xpath('//a[@action-type="btn_submit"]')
    element.click()

    WebDriverWait(driver, 10, 0.5).until(
        expected_conditions.element_to_be_clickable((By.XPATH, '//input[@node-type="searchInput"]')))
    #保存登录后的cookie
    cookies = driver.get_cookies()
    with open("conf/sinacookies.txt", "w") as fp:
        json.dump(cookies, fp)
    return driver

def sina_login_with_cookie():
    driver = webdriver.Chrome()
    driver.get("https://weibo.com/")
    driver.maximize_window()
    WebDriverWait(driver, 10, 0.5).until(
        expected_conditions.element_to_be_clickable((By.XPATH, '//a[@action-type="btn_submit"]')))
    driver.delete_all_cookies()
    with open("conf/sinacookies.txt", "r") as fp:
        cookies = json.load(fp)
        for cookie in cookies:
            driver.add_cookie(cookie)
    driver.get("http://photo.weibo.com/")
    return driver


if __name__ == '__main__':
    driver = sina_login()
    time.sleep(2)