# -*- coding: utf-8 -*-
from urllib import parse

import scrapy
import re
import hashlib

from scrapy import Request

from ArticleSpider.items import JobBoleArticleItem
 

class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        post_nodes = response.css("#archive .floated-thumb .post-thumb")  # a selector, 可以在这个基础上继续做 selector

        for post_node in post_nodes:
            post_url = post_node.css("a::attr(href)").extract_first("")
            img_url = post_node.css("a img::attr(src)").extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url),meta={"front-image-url":img_url}, callback=self.parse_detail)
            #yield Request(url=parse.urljoin(response.url, post_url),meta={"front-image-url":img_url}, callback=self.parse_detail_byItemLoader)

        # # 必须考虑到有前一页，当前页和下一页链接的影响，使用如下所示的方法
        # next_url = response.css("span.page-numbers.current+a::attr(href)").extract_first("")
        # if next_url:
        #     yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)


    def parse_detail(self, response):
        """作为回调函数，在上面调用"""
        title = response.css(".entry-header h1::text").extract()[0]
        match_date = re.match("([0-9/]*).*",
                              response.css(".entry-meta-hide-on-mobile::text").extract()[0].strip())
        if match_date:
            create_date = match_date.group(1)

        votes_css = response.css(".vote-post-up h10::text").extract_first()
        if votes_css:
            vote_nums = int(votes_css)
        else:
            vote_nums = 0

        ma_fav_css = re.match(".*?(\d+).*",
                              response.css(".bookmark-btn::text").extract_first())
        if ma_fav_css:
            fav_nums = int(ma_fav_css.group(1))
        else:
            fav_nums = 0

        ma_comments_css = re.match(".*?(\d+).*",
                                   response.css("a[href='#article-comment'] span::text").extract_first())
        if ma_comments_css:
            comment_nums = int(ma_comments_css.group(1))
        else:
            comment_nums = 0

        tag_lists_css = response.css(".entry-meta-hide-on-mobile a::text").extract()
        tag_lists_css = [ele for ele in tag_lists_css if not ele.strip().endswith('评论')]
        tags = ','.join(tag_lists_css)

        # cpyrights = response.css(".copyright-area").extract()
        content = response.css(".entry *::text").extract()

        front_img_url = response.meta.get("front-image-url", "")
        #front_img_url = response.css('.aligncenter::attr(src)').extract_first

        article_item = JobBoleArticleItem() # 实例化 item 对象
        # 赋值 item 对象
        article_item["title"] = title
        article_item["create_date"] = create_date
        article_item["url"] = response.url
        article_item["front_img_url_download"] = [front_img_url] # 这里传递的需要是列表的形式，否则后面保存图片的时候，会出现类型错误，必须是可迭代对象
        article_item["fav_nums"] = fav_nums
        article_item["comment_nums"] = comment_nums
        article_item["vote_nums"] = vote_nums
        article_item["tags"] = tags
        # article_item["cpyrights"] = cpyrights
        article_item["content"] = ''.join(content)      # 取出的 content 是一个 list ,存入数据库的时候，需要转换成字符串
        article_item["object_id"] = gen_md5(response.url)
        yield article_item

    # def parse_detail_byItemLoader(self, response):
    #     front_img_url = response.meta.get("front-image-url", "")
    #     item_loader = ArticleItemLoader(item=JobBoleArticleItem(), response=response)
    #     article_item_loader = JobBoleArticleItem()
    #     item_loader.add_css("title", ".entry-header h1::text")  # 通过 css 选择器获取值
    #     item_loader.add_value("url", response.url)
    #     item_loader.add_css("create_date", ".entry-meta-hide-on-mobile::text")
    #     item_loader.add_value("front_img_url_download", [[front_img_url]])
    #     item_loader.add_css("fav_nums", ".bookmark-btn::text")
    #     item_loader.add_css("comment_nums", "a[href='#article-comment'] span::text")
    #     item_loader.add_css("vote_nums", ".vote-post-up h10::text")
    #     item_loader.add_css("tags", ".entry-meta-hide-on-mobile a::text")
    #     item_loader.add_css("content", ".entry *::text")
    #     item_loader.add_value("object_id", gen_md5(response.url))
    #     # item_loader.add_xpath()
    #     # item_loader.add_value()
    #     article_item_loader = item_loader.load_item()
    #     yield article_item_loader

def gen_md5(data):
    res = hashlib.md5(data.encode('utf-8')).hexdigest()
    return res
