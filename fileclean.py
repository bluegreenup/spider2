# coding:utf-8
import logging
import xml.dom.minidom
import re
import os
import sys
from logging.handlers import RotatingFileHandler
import concurrent.futures
import random
import time

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

FILECLEAN_LOGGER = logging.getLogger(__name__)
FILECLEAN_STREAM_HANDLER = logging.StreamHandler(sys.stdout)
FILECLEAN_STREAM_HANDLER.setLevel(logging.INFO)
FILECLEAN_STREAM_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))
FILECLEAN_LOGGER.addHandler(FILECLEAN_STREAM_HANDLER)
FILECLEAN_ROTATING_FILE_HANDLER = RotatingFileHandler('./log/info.log', maxBytes=50 * 1024 * 1024, backupCount=10)
FILECLEAN_ROTATING_FILE_HANDLER.setLevel(logging.INFO)
FILECLEAN_ROTATING_FILE_HANDLER.setFormatter(logging.Formatter(LOG_FORMAT))
FILECLEAN_LOGGER.addHandler(FILECLEAN_ROTATING_FILE_HANDLER)

CONFDIR = os.path.join(os.getcwd(), 'conf')
INSTAGRAMDOWNLOADDIR = os.path.join(CONFDIR, 'instagramdownload')

# 获取指定文件夹下，所有文件的文件名，listdir只取了文件夹下的一级文件（包含了文件夹）的数据，并没有递归获取
# 返回一个list，如果文件夹不存在，则返回一个空的list
def getFileName(dirpath):
    if not os.path.exists(dirpath):
        return []
    filelist = os.listdir(dirpath)
    # 去掉文件夹，只保留一般的文件,这里偷懒，只保留了含有.的文件，默认文件夹不会使用包含.的名字，同时文件是有带.后缀名的
    filelist = [i for i in filelist if i.find('.') != -1]
    return filelist


# 删除指定文件夹下，匹配列表里的文件
def deleteFile(dirpath, deletelist):
    if not deletelist:
        FILECLEAN_LOGGER.info('List is [].Nothing to delete in ' + dirpath)
    elif not os.path.exists(dirpath):
        FILECLEAN_LOGGER.warn('Not exist ' + dirpath)
    else:
        for filename in deletelist:
            fullname = os.path.join(dirpath, filename)
            if os.path.exists(fullname):
                try:
                    os.remove(fullname)
                    FILECLEAN_LOGGER.info('Succeed to delete ' + fullname)
                except OSError:
                    FILECLEAN_LOGGER.warn('Fail to delete ' + fullname)


def getxmlname():
    file = "./conf/instagram.xml"
    namelist = []
    try:
        domTree = xml.dom.minidom.parse(file)
    except:
        FILECLEAN_LOGGER.error("Can't open Instagram xml file!")
        return namelist

    collection = domTree.documentElement
    nodes = collection.getElementsByTagName("html")
    for node in nodes:
        name = node.getElementsByTagName("page")[0].childNodes[0].data
        namelist.append(name.split('/')[-1])
    return namelist


def mkdir(path):
    path = path.strip()
    isExists = os.path.exists(path)
    if not isExists:
        # print u'建了一个名字叫做', path, u'的文件夹！'
        FILECLEAN_LOGGER.info(u'建了一个名字叫做' + path + u'的文件夹！')
        # 递归创建文件夹
        os.makedirs(os.path.join(".", path))
        return True
    else:
        # print u'名字叫做', path, u'的文件夹已经存在了！'
        FILECLEAN_LOGGER.debug(u'名字叫做' +  path + u'的文件夹已经存在了！')
        return False


#从存有下载数据的文件夹里获取已经下载的文件名，并保存到对应的已下载文件里
def updateDownloadedFileName(dirpath):
    #目录下一班包含Img和video文件夹，需分别获取文件名，并保存在同一个用户名的文件里，一行一个文件

    if os.path.exists(os.path.join(dirpath, 'img')):
        imgdir = os.path.join(dirpath, 'img')
        #获取img下的所有文件夹名
        dirlist = os.listdir(imgdir)
        #遍历期中的所有文件夹
        # print(dirlist)
        for dirname in dirlist:
            #不是文件夹则跳过
            if not os.path.isdir(os.path.join(imgdir, dirname)):
                FILECLEAN_LOGGER.warn(dirname + ' is not a directory.')
                continue
            #获取所有的已存文件名
            filelist = os.listdir(os.path.join(imgdir, dirname))
            #print(filelist)
            #print(len(filelist))
            if filelist:
                downloadfilenamelist = []
                if os.path.exists(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt')):
                    #print(u'存在download文件')
                    #获取里面已存的文件名
                    with open(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt'), 'r') as f:
                        for line in f.readlines():
                            #print line
                            downloadfilenamelist.append(line.strip())
                #print(len(downloadfilenamelist))

                with open(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt'), 'a') as f:
                    for filename in filelist:
                        #只添加不存在的文件名
                        if filename not in downloadfilenamelist:
                            f.write(filename + '\n')
                            FILECLEAN_LOGGER.info(dirname + '：add ' + filename + ' to instagramdownload.')

    if os.path.exists(os.path.join(dirpath, 'video')):
        videodir = os.path.join(dirpath, 'video')
        # 获取img下的所有文件夹名
        dirlist = os.listdir(videodir)
        # 遍历期中的所有文件夹
        # print(dirlist)
        for dirname in dirlist:
            # 不是文件夹则跳过
            if not os.path.isdir(os.path.join(videodir, dirname)):
                FILECLEAN_LOGGER.warn(dirname + ' is not a directory.')
                continue
            # 获取所有的已存文件名
            filelist = os.listdir(os.path.join(videodir, dirname))
            # print(filelist)
            # print(len(filelist))
            if filelist:
                downloadfilenamelist = []
                if os.path.exists(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt')):
                    # print(u'存在download文件')
                    # 获取里面已存的文件名
                    with open(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt'), 'r') as f:
                        for line in f.readlines():
                            # print line
                            downloadfilenamelist.append(line.strip())
                # print(len(downloadfilenamelist))

                with open(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt'), 'a') as f:
                    for filename in filelist:
                        # 只添加不存在的文件名
                        if filename not in downloadfilenamelist:
                            f.write(filename + '\n')
                            FILECLEAN_LOGGER.info(dirname + '：add ' + filename + ' to instagramdownload.')


#从存有下载数据的文件夹里获取已经下载的文件名，将这些文件名从对应的已下载列表文件中删除
def deleteDownloadedFileName(dirpath):
    #目录下一班包含Img和video文件夹，需分别获取文件名，并保存在同一个用户名的文件里，一行一个文件

    if os.path.exists(os.path.join(dirpath, 'img')):
        imgdir = os.path.join(dirpath, 'img')
        #获取img下的所有文件夹名
        dirlist = os.listdir(imgdir)
        #遍历期中的所有文件夹
        # print(dirlist)
        for dirname in dirlist:
            #不是文件夹则跳过
            if not os.path.isdir(os.path.join(imgdir, dirname)):
                FILECLEAN_LOGGER.warn(dirname + ' is not a directory.')
                continue
            #不存在已下载文件则跳过
            if not os.path.exists(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt')):
                FILECLEAN_LOGGER.info(dirname + ' doesn\'t have instagramdownload file.')
                continue
            #获取所有的文件名
            filelist = os.listdir(os.path.join(imgdir, dirname))
            #print(filelist)
            #print(len(filelist))
            if filelist:
                downloadfilenamelist = []
                if os.path.exists(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt')):
                    #print(u'存在download文件')
                    #获取里面已存的文件名
                    with open(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt'), 'r') as f:
                        for line in f.readlines():
                            #print line
                            downloadfilenamelist.append(line.strip())

                updatedownloadfilenamelist = [item for item in downloadfilenamelist if item not in filelist]

                # try:
                #     os.remove(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt'))
                #     FILECLEAN_LOGGER.info('Succeed to delete ' + dirname + '.txt')
                # except OSError:
                #     FILECLEAN_LOGGER.warn('Fail to delete ' + dirname + '.txt')
                #     continue

                #清空，再写入
                with open(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt'), 'w') as f:
                    for filename in updatedownloadfilenamelist:
                        f.write(filename + '\n')
                        FILECLEAN_LOGGER.info(dirname + '：add ' + filename + ' to instagramdownload.')

    if os.path.exists(os.path.join(dirpath, 'video')):
        videodir = os.path.join(dirpath, 'video')
        # 获取img下的所有文件夹名
        dirlist = os.listdir(videodir)
        # 遍历期中的所有文件夹
        # print(dirlist)
        for dirname in dirlist:
            # 不是文件夹则跳过
            if not os.path.isdir(os.path.join(videodir, dirname)):
                FILECLEAN_LOGGER.warn(dirname + ' is not a directory.')
                continue
            # 不存在已下载文件则跳过
            if not os.path.exists(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt')):
                FILECLEAN_LOGGER.info(dirname + ' doesn\'t have instagramdownload file.')
                continue
            # 获取所有的已存文件名
            filelist = os.listdir(os.path.join(videodir, dirname))
            # print(filelist)
            # print(len(filelist))
            if filelist:
                downloadfilenamelist = []
                if os.path.exists(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt')):
                    # print(u'存在download文件')
                    # 获取里面已存的文件名
                    with open(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt'), 'r') as f:
                        for line in f.readlines():
                            # print line
                            downloadfilenamelist.append(line.strip())

                updatedownloadfilenamelist = [item for item in downloadfilenamelist if item not in filelist]

                # try:
                #     os.remove(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt'))
                #     FILECLEAN_LOGGER.info('Succeed to delete ' + dirname + '.txt')
                # except OSError:
                #     FILECLEAN_LOGGER.warn('Fail to delete ' + dirname + '.txt')
                #     continue

                # 清空，再写入
                with open(os.path.join(INSTAGRAMDOWNLOADDIR, dirname + '.txt'), 'w') as f:
                    for filename in updatedownloadfilenamelist:
                        f.write(filename + '\n')
                        FILECLEAN_LOGGER.info(dirname + '：add ' + filename + ' to instagramdownload.')


def getDownloadedFileName(dirpath):
    if not os.path.exists(dirpath):
        return []
    downloadfilenamelist = []

    with open(dirpath, 'r') as f:
        for line in f.readlines():
            downloadfilenamelist.append(line.strip())
    return downloadfilenamelist


if __name__ == "__main__":
    sourceDir = 'D:\\Programme\\2020.1.22\\'#G:\ D:\Programme\2020.1.22
    deleteDir = 'D:\\Programme\\Python\\spider\\data'#F:\2020.1.22 D:\Programme\Python\spider
    downloadedDir = 'D:\\Programme\\Python\\spider'
    # fileNameList = ['']

    fileNameList = getxmlname()

    #从sourceDir获取需要删除的文件名列表，到deleteDir中将这些文件删除
    # for fileName in fileNameList:
    #     deleteList = getFileName(os.path.join(sourceDir, fileName))
    #     FILECLEAN_LOGGER.info(fileName + ' deletelist has ' + str(len(deleteList)))
    #     deleteFile(os.path.join(deleteDir, fileName), deleteList)

    #将sourceDir的数据保存到已下载文件中
    #updateDownloadedFileName(sourceDir)

    #将deleteDir的数据从已下载的文件中删除
    #deleteDownloadedFileName(deleteDir)

    # 从INSTAGRAMDOWNLOADDIR获取已下载的文件列表，到deleteDir中将这些文件删除
    # for fileName in fileNameList:
    #     deleteList = getDownloadedFileName(os.path.join(INSTAGRAMDOWNLOADDIR, fileName + '.txt'))
    #     FILECLEAN_LOGGER.info(fileName + ' deletelist has ' + str(len(deleteList)))
    #     deleteFile(os.path.join(deleteDir, 'img', fileName), deleteList)
    #     deleteFile(os.path.join(deleteDir, 'video', fileName), deleteList)