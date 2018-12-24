# spider2
基于python2.7，依赖requests、selenium等

1. instagram
   > 原理：使用多进程，使用requests，根据配置文件抓取对应用户主页面的12个最新的ins图片和视频  
   > 相关文件：`instagram_spider.py instagram.xml`
2. mzitu
   > 原理：使用requests和bs，抓取指定页面下的所有链接，保存其中的图片   
   > 相关文件：`mzitu2.py downloadbyproxy.py`
3. sina
   > 原理：使用selenium模拟登陆，人工输入用户名密码，从微薄相册-相册专辑-xx专辑-xx相册-当前照片的网页源代码中获取`owner_uid album_id album_photo_ids`，拼接出待爬取的地址，爬取获得具体图片的地址，改用迅雷下载orz   
   > 相关文件：`sina_login.py sina_pic.py`
3. alisaverner
   > 原理：使用requests，采用多线程下载主页的所有图片
   > 相关文件：`alisaverner.py`