# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class HncrawlerItem(scrapy.Item):
	title = scrapy.Field()
	date = scrapy.Field()
	auth = scrapy.Field()
	cont = scrapy.Field()
	idAuth = scrapy.Field()
