# coding:utf-8

from bs4 import BeautifulSoup
import os
from downloadbyproxy import request  ##导入模块变了一下
#from pymongo import MongoClient


class mzitu2():
    def all_url(self, url):

        html = request.get(url, 3)
        all_a = BeautifulSoup(html.text, 'lxml').find('div', class_='all').find_all('a')
        for a in all_a:
            title = a.get_text()
            #print(u'开始保存：', title)
            href = a['href']
            # print href.split('/')
            path = str(href.split('/')[3])
            print u'开始保存：', path
            #path = str(title).replace("?", '_')
            returns = self.mkdir(path)
            if returns == False:
                print path, u' 文件夹已存在'
                continue
            os.chdir("D:\mzitu\\" + path)
            href = a['href']
            self.html(href)

    def html(self, href):
        html = request.get(href, 3)
        max_span = BeautifulSoup(html.text, 'lxml').find_all('span')[10].get_text()

        if max_span.find(u'下一页') != -1:
            max_span = BeautifulSoup(html.text, 'lxml').find_all('span')[9].get_text()

        if max_span.find(u'相关专题') != -1:
            max_span = BeautifulSoup(html.text, 'lxml').find_all('span')[8].get_text()



        for page in range(1, int(max_span) + 1):
            page_url = href + '/' + str(page)
            self.img(page_url)

    def img(self, page_url):
        img_html = request.get(page_url, 3)
        img_url = BeautifulSoup(img_html.text, 'lxml').find('div', class_='main-image').find('img')['src']
        self.save(img_url)

    def save(self, img_url):
        name = img_url.split('/')[-1].split('.')[0]
        # name = img_url[-9:-4]
        print u'开始保存：', img_url
        img = request.get(img_url, 3)
        f = open(name + '.jpg', 'ab')
        f.write(img.content)
        f.close()

    def mkdir(self, path):
        path = path.strip()
        isExists = os.path.exists(os.path.join("D:\mzitu", path))
        if not isExists:
            print u'建了一个名字叫做', path, u'的文件夹！'
            os.makedirs(os.path.join("D:\mzitu", path))
            return True
        else:
            print u'名字叫做', path, u'的文件夹已经存在了！'
            return False


Mzitu = mzitu2()
Mzitu.all_url('http://www.mzitu.com/all')