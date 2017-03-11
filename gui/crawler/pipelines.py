# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from crawler.items import HncrawlerItem
from crawler.settings import mysql_conn

from MySQLdb import IntegrityError


class HncrawlerPipeline(object):
    def process_item(self, item, spider):
        cursor = mysql_conn.cursor()
        idAuth = selectAuthor(cursor, item['auth'])

        if idAuth == -1:
            item['idAuth'] = int(insertAuthor(cursor, item['auth']))
        else:
            item['idAuth'] = int(idAuth)

        insertArticle(cursor, item)
        return item

def insertArticle(cursor, item):
    try:
        insertStmt  = """INSERT INTO articles (title, date, author_id, content)
                         VALUES (%s, %s, %s, %s)"""
        data = (item['title'], item['date'], item['idAuth'], item['cont'])
        cursor.execute(insertStmt, data)
        cursor.execute("""COMMIT""")
    except IntegrityError, e:
        print "Article already in database!"

def selectAuthor(cursor, name):
    selectStmt = """SELECT *
                    FROM authors
                    WHERE name=%s"""
    data = (name,)
    cursor.execute(selectStmt, data)
    rows = cursor.fetchone()

    if rows != None:
        return rows[0]
    else:
        return -1

def insertAuthor(cursor, name):
    insertStmt = """INSERT INTO authors (name)
                    VALUES(%s)"""
    data = (name,)
    cursor.execute(insertStmt, data)
    cursor.execute("""COMMIT""")

    selectStmt = """SELECT author_id
                    FROM authors
                    WHERE name=%s"""
    cursor.execute(selectStmt, data)
    row = cursor.fetchone()

    return row[0]