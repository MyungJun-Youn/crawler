# -*- coding: utf-8 -*-

import urllib
import datetime
import MySQLdb

from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http import Request

from ..items import PpomppuItem

from konlpy.tag import Mecab

print "============================="
print "start Ppomppu crawling..."
print "============================="

maxUrlCount = 1
currentUrlCount = 1
BOARD_NO = "2"

#크롤링할 URL
domain = u"http://www.ppomppu.co.kr"
urlPath = u"/zboard/zboard.php?id=freeboard"
page = u"&page="
url = domain + urlPath + page + u"1"

mecab = Mecab()

class PpomppuSpider(Spider):
    name = "ppomppu"
    allowed_domains = ["www.ppomppu.co.kr"]
    start_urls = [url]

    print "start :" + str(start_urls)

    def parse(self, response):
        global currentUrlCount, maxUrlCount

        print "parsing pagelink..." + str(currentUrlCount)

        hxs = Selector(response)

        posts =[]
        posts = hxs.xpath('//tr[@class="list1" or @class="list0"]')
        print "posts count: " + str(len(posts))

        LastPostTime = self.getLastPostTime()

        items = []
        for post in posts:
            item = PpomppuItem()
            item['title'] = post.xpath('td[3]/a[1]/font[@class="list_title"]/text()').extract()[0]
            item['dateTime'] = datetime.datetime.strptime('20' + ''.join(post.xpath('td[4]/@title').extract()), '%Y.%m.%d %H:%M:%S')
            item['sourceUrl'] = domain + u'/zboard/' + post.xpath('td[3]/a[1]/@href').extract()[0]
            item['contents'] = self.contentsParse(item['sourceUrl'])
            item['keywords'] = self.keywordsParse(item['title'], item['contents'])

            if LastPostTime >= item['dateTime'] :
                break;

            yield item

        if(currentUrlCount < maxUrlCount):
            currentUrlCount = currentUrlCount + 1
            nextPage = [domain + urlPath + page + str(currentUrlCount)]
            print '------->request url :' + nextPage[0]
            yield Request(nextPage[0], self.parse)

        # return items

    def contentsParse(self, url):
        data = urllib.urlopen(url).read()
        hxs = Selector(text=data)

        contents = ''.join(hxs.select('//td[@id="realArticleView"]').extract())
        contents = contents.replace("'",'"')

        return contents

    def keywordsParse(self, title, contents) :
        titleKeywords = mecab.nouns(title)
        contentsKeywords = mecab.nouns(contents)

        keywords = titleKeywords + contentsKeywords

        return list(set(keywords))

    def getLastPostTime(self):
        db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="hub", charset="utf8")
        cursor = db.cursor()

        try :
            query = ("SELECT MAX(post_time) FROM article where board_no =" + BOARD_NO + ";")
            cursor.execute(query)
            return cursor.fetchone()[0]
        except MySQLdb.Error, e:
            try:
                print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
            except IndexError:
                print "MySQL Error: %s" % str(e)
