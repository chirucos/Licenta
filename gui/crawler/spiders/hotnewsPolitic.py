# -*- coding: utf-8 -*-
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import Spider
from datetime import datetime
from unidecode import unidecode
from crawler.items import HncrawlerItem
import re

month = {
    'ianuarie': 1,
    'februarie': 2,
    'martie': 3,
    'aprilie': 4,
    'mai': 5,
    'iunie': 6,
    'iulie': 7,
    'august': 8,
    'septembrie': 9,
    'octombrie': 10,
    'noiembrie': 11,
    'decembrie': 12
}


class HotnewspoliticSpider(Spider):
    name = "hotnewsPolitic"
    allowed_domains = ["hotnews.ro"]
    start_urls = (
        'http://www.hotnews.ro/politic',
    )
    scrapedPagesCount = 0

    def removeTags(self, text):
        text = re.sub(r'<script.*?>.*?</script>', '', text)
        text = re.sub(r'<.*?>', '', text)
        return text

    def convertDate(self, date):
        tok = date.split(',')
        dateTok = tok[1].strip().split(" ")
        timeTok = tok[2].strip().split(":")
        return datetime(int(dateTok[2]), month[dateTok[1]], int(dateTok[0]), int(timeTok[0]), int(timeTok[1]))

    def parse(self, response):
        sel = Selector(response)
        requests = []

        # parsing urls for articles
        articleUrls = sel.xpath('//div[@class="articol_lead_full"]/h2/a/@href')
        if len(articleUrls) == 0:
            articleUrls = sel.xpath('//div[@class="result_item"]/a[@class="result_title"]/@href')
        for url in articleUrls:
            link = unidecode(url.extract())
            request = Request(url=link , callback=self.parseArticle)
            requests.append(request)

        # parsing url for next page
        nextPageSel = sel.xpath('//div[@class="paging"]/a')
        currentPage = 0
        for i in xrange(len(nextPageSel)):
            page = unidecode(nextPageSel[i].extract())
            if page.find('font-weight:bold') != -1:
                currentPage = i
                self.scrapedPagesCount = self.scrapedPagesCount + 1
                break
        print "----- Length: " + str(len(nextPageSel))
        print "----- Current_page: " + str(currentPage)

        if currentPage != len(nextPageSel) - 1:
            nextPageUrl = unidecode(nextPageSel[currentPage + 1].xpath('@href').extract()[0])
            nextPageUrl = self.start_urls[0] + nextPageUrl
            request = Request(url=nextPageUrl , callback=self.parse)
            requests.append(request)

        print '\n-----------------\n'
        print '===== Page: ' + str(self.scrapedPagesCount) + '\n'
        print '-----------------\n'

        return requests

    def parseArticle(self, response):
        sel = Selector(response)
        scrapedItem = HncrawlerItem()

        # parsing title
        titleSel = sel.xpath('//h1[@class="title"]')
        try:
            title = unidecode(titleSel.extract()[0])
            title = self.removeTags(title).strip()
        except IndexError:
            title = ''

        # parsing date
        dateSel = sel.xpath('//div[@class="articol_render"]/div/span[@class="data"]/text()')
        try:
            date = unidecode(dateSel.extract()[0]).strip()
        except IndexError:
            date = ''

        # parsing author
        authSel = sel.xpath('//div[@class="autor"]/a/text()')
        try:
            auth = unidecode(authSel.extract()[0]).strip()
        except IndexError:
            auth = ''

        # parsing article content
        contSel = sel.xpath('//div[@id="articleContent"]')
        try:
            cont = unidecode(contSel.extract()[0])
            cont = self.removeTags(cont).strip()
        except IndexError:
            cont = ''

        scrapedItem['title'] = title
        scrapedItem['auth'] = auth
        scrapedItem['date'] = self.convertDate(date)
        scrapedItem['cont'] = cont

        return scrapedItem