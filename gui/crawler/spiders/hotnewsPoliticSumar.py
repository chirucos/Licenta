# -*- coding: utf-8 -*-
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.spider import Spider
from datetime import datetime
from unidecode import unidecode
from crawler.items import HncrawlerItem
from scrapy import log
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


class HotnewspoliticSpiderSumar(Spider):
    name = "hotnewsPoliticSumar"
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

    def getTitle(self, sel, pType):
        if pType == 0:
            title = sel.xpath('.//h2[@class="article_title"]/a/@title')
            title = title.extract()
            title = map(unidecode, title)
            title = ' '.join(title).strip()
            title = re.sub('\n', '', title)
            return title
        elif pType == 1:
            title = sel.xpath('.//a[@class="result_title"]/strong/text()')
            title = title.extract()
            title = map(unidecode, title)
            title = ' '.join(title).strip()
            title = re.sub('\n', '', title)
            return title

    def getContent(self, sel, pType):
        if pType == 0:
            content = sel.xpath('.//div[@class="lead"]/text()')
            content = content.extract()
            content = map(unidecode, content)
            content = ' '.join(content).strip()
            content = re.sub('\n', '', content)
            return content
        elif pType == 1:
            content = sel.xpath('.//span[@class="stire"]/text()')
            content = content.extract()
            content = map(unidecode, content)
            content = ' '.join(content).strip()
            content = re.sub('\n', '', content)
            return content

    def getLink (self, sel, pType):
        if pType == 0:
            link = sel.xpath('.//h2/a/@href')
            link = link.extract()[0]
            link = unidecode(link)
            return link
        elif pType == 1:
            link = sel.xpath('.//a[@class="result_title"]/@href')
            link = link.extract()[0]
            link = unidecode(link)
            return link

    def getDate(self, sel):
        date = sel.xpath('.//div[@class="actualitate_footer align_text"]/span/text()')
        date = date.extract()
        date = map(unidecode, date)
        date = ' '.join(date).strip()
        date = re.sub('\n.*', '', date)
        return self.convertDate(date)

    def getAuthor(self, sel):
        author = sel.xpath('.//div[@class="autor"]/text()')
        author = author.extract()
        author = map(unidecode, author)
        author = ' '.join(author).strip()
        author = re.sub('\n.*', '', author)
        return author

    def parse(self, response):
        sel = Selector(response)
        requests = []

        # parsing archive
        articles = sel.xpath('//div[@class="articol_lead_full"]')
        if len(articles) != 0:
            # parsing first page of archive
            for article in articles:
                articleInfo = {
                    'title': self.getTitle(article, 0),
                    'content': self.getContent(article, 0)
                }
                link = self.getLink(article, 0)
                request = Request(url=link , callback=self.parseDate, meta=articleInfo)
                requests.append(request)
        else:
            # parsing the rest of the archive pages
            articles = sel.xpath('//div[@class="result_item"]')
            for article in articles:
                articleInfo = {
                    'title': self.getTitle(article, 1),
                    'content': self.getContent(article, 1)
                }
                link = self.getLink(article, 1)
                request = Request(url=link , callback=self.parseDate, meta=articleInfo)
                requests.append(request)

        log.msg("Page: " + str(self.scrapedPagesCount), level=log.ERROR)

        # parsing url for next page
        nextPageSel = sel.xpath('//div[@class="paging"]/a')
        currentPage = 0
        for i in xrange(len(nextPageSel)):
            page = unidecode(nextPageSel[i].extract())
            if page.find('font-weight:bold') != -1:
                currentPage = i
                log.msg("Current page: " + str(currentPage) + "   out of: " + str(len(nextPageSel)), level=log.ERROR)
                self.scrapedPagesCount = self.scrapedPagesCount + 1
                break

        # check if this is the last page of the archive
        if currentPage != len(nextPageSel) - 1:
            nextPageUrl = unidecode(nextPageSel[currentPage + 1].xpath('@href').extract()[0])
            nextPageUrl = self.start_urls[0] + nextPageUrl
            request = Request(url=nextPageUrl , callback=self.parse)
            requests.append(request)

        return requests

    def parseDate(self, response):
        sel = Selector(response)
        scrapedItem = HncrawlerItem()

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

        scrapedItem['title'] = response.meta['title']
        scrapedItem['auth'] = auth
        scrapedItem['date'] = self.convertDate(date)
        scrapedItem['cont'] = response.meta['content']

        return scrapedItem
