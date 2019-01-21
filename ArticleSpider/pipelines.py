# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import codecs
import json
import pymysql.cursors

from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


#############以json包的方式输出#########################################
class JsonWithEncodingPipeline(object):
    """
    处理 item 数据，保存为json格式的文件中
    """

    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'  # False，才能够在处理非acsii编码的时候，不会出错，尤其
        # 中文
        self.file.write(lines)
        return item  # 必须 return

    def spider_close(self, spider):
        """
        把文件关闭
        """
        self.file.close()


#############以scrapy.exporters的方式输出#########################################
class JsonExporterPipeline(object):

    def __init__(self):
        """
        先打开文件，传递一个文件
        """
        self.file = open('articleexporter.json', 'wb')
        # 调用 scrapy 提供的 JsonItemExporter导出json文件
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def spider_close(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


#############存储到mysql#########################################
class MysqlPipeline(object):

    def __init__(self):
        # 连接数据库
        # self.conn = MySQLdb.connect('192.168.0.101', 'spider', 'wuzhenyu', 'article_spider', charset="utf8", use_unicode=True)
        # self.cursor = self.conn.cursor()

        # 连接数据库
        self.connect = pymysql.Connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='root',
            db='dbtest',
            charset='utf8'
        )
        self.cursor = self.connect.cursor()

    def process_item(self, item, spider):
        insert_sql = """insert into article(title, create_date, url, url_object_id, front_img_url, comment_nums, fav_nums, vote_nums, tags, content) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_sql, (
            item["title"],
            item["create_date"],
            item["url"],
            item["object_id"],
            item["front_img_url_download"][0],
            item["comment_nums"],
            item["fav_nums"],
            item["vote_nums"],
            item["tags"],
            item["content"]
        ))
        self.connect.commit()

    def spider_close(self, spider):
        self.cursor.close()
        self.connect.close()


#############通过 Twisted 框架提供的异步方法入库#########################################
class MysqlTwistedPipeline(object):
    """
    利用 Twisted API 实现异步入库 MySQL 的功能
    Twisted 提供的是一个异步的容器，MySQL 的操作还是使用的MySQLDB 的库
    """
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbpool = adbapi.ConnectionPool(
            "pymysql",
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            password=settings["MYSQL_PASSWORD"],
            charset="utf8",
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode = True,
            cp_max=4
        )
        return cls(dbpool)


    def process_item(self, item, spider):
        """
        使用 twisted 将 mysql 操作编程异步执行
        """
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error) # handle exceptions

    def handle_error(self, failure):
        """
        处理异步操作的异常
        """
        print(failure)

    def do_insert(self, cursor, item):
        """
        执行具体的操作，能够自动 commit
        """

        insert_sql = """insert into article(title, create_date, url, url_object_id, front_img_url, comment_nums, fav_nums, vote_nums, tags, content) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (
            item["title"],
            item["create_date"],
            item["url"],
            item["object_id"],
            item["front_img_url_download"][0],
            item["comment_nums"],
            item["fav_nums"],
            item["vote_nums"],
            item["tags"],
            item["content"]
        ))
