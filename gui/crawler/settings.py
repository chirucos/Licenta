# -*- coding: utf-8 -*-

# Scrapy settings for crawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

from sys import exit
from MySQLdb import connect, Error

# SCRAPY SETTINGS
BOT_NAME = 'crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'
ITEM_PIPELINES = {
    'crawler.pipelines.HncrawlerPipeline': 1
}

LOG_LEVEL = 'ERROR'
DOWNLOAD_DELAY = 1

# MYSQL DATABASE SETTINGS
SQL_DB = 'licentadb'
SQL_HOST = 'localhost'
SQL_USER = 'tuddim'

try:
    mysql_conn = connect(host=SQL_HOST, user=SQL_USER, db=SQL_DB)

except Error, e:
    print "Error %d %d" % (e.args[0], e.args[1])
    exit(1)

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'hnCrawler (+http://www.yourdomain.com)'
