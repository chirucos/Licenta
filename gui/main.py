from threading import Thread

from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtWidgets import QPushButton, QApplication, QWidget, QDesktopWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QGroupBox
from PyQt5.QtWidgets import QSizePolicy, QLineEdit, QDialog, QListWidget
from PyQt5.QtWidgets import QGridLayout, QComboBox, QDateEdit

from articol import Article
from MySQLdb import IntegrityError

from crawler.settings import mysql_conn

from twisted.internet import reactor
from scrapy.crawler import Crawler
from scrapy import log, signals
from crawler.spiders.hotnewsPoliticSumar import HotnewspoliticSpiderSumar
from scrapy.utils.project import get_project_settings

import re
import sys

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB, GaussianNB, BernoulliNB
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline

import plotly.plotly as py
from plotly.graph_objs import *
from PIL import Image


classifiers = {
    'Multinomial NB': MultinomialNB(),
    'Gaussian NB': GaussianNB(),
    'Bernoulli NB': BernoulliNB(),
    'SVM': SGDClassifier(loss='hinge', penalty='l2', alpha=1e-3, n_iter=5, random_state=42)
}


monthIntToString = {
    1: 'Ian',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'Mai',
    6: 'Iun',
    7: 'Iul',
    8: 'Aug',
    9: 'Sep',
    10: 'Oct',
    11: 'Noi',
    12: 'Dec'
}

reportTypes = [
    "Opinions/Entity Selected",
    "Opinions/All Entities",
    "Appearances/Entity Selected",
    "Appearances/All Entities"
]

class MainWindow(QWidget):

    articleInfoUpdate = pyqtSignal()
    entityUpdate = pyqtSignal()
    crawlerUpdate = pyqtSignal()

    def __init__(self):
        super(MainWindow, self).__init__()

        self.initUI()

        self.articleInfoUpdate.connect(self.updateArticleInfo)
        self.entityUpdate.connect(self.updateEntityList)

    def initUI(self):
        self.setGeometry(0, 0, 500, 700)

        self.center()
        self.setWindowTitle('PView')

        mainLayout = QVBoxLayout()

        self.createArticleInfoBox()
        self.createViewArticleBox()
        self.createEntityBox()
        self.createReportBox()
        self.createDatabaseBox()

        mainLayout.addWidget(self.infoBox)
        mainLayout.addWidget(self.viewArticleBox)
        mainLayout.addWidget(self.entityBox)
        mainLayout.addWidget(self.raportBox)
        mainLayout.addWidget(self.databaseBox)

        self.setLayout(mainLayout)

        self.show()

    def createArticleInfoBox(self):
        self.articleCount = self.selectCountArticles()
        entityCount = self.selectCountEntities()
        associationsCount = self.selectCountAssociations()
        classifiedCount = self.selectCountClassifiedAssociations()

        label = "Number of articles: " + str(self.articleCount)
        self.articleCountLabel = QLabel(label)

        label = "Number of entities: " + str(entityCount)
        self.entitiesCountLabel = QLabel(label)

        label = "Number of associations: " + str(associationsCount)
        self.associationsCountLabel = QLabel(label)

        label = "Number of classified associations: " + str(classifiedCount)
        self.classifiedCountLabel = QLabel(label)

        layout = QVBoxLayout()
        layout.addWidget(self.articleCountLabel)
        layout.addWidget(self.entitiesCountLabel)
        layout.addWidget(self.associationsCountLabel)
        layout.addWidget(self.classifiedCountLabel)

        self.infoBox = QGroupBox("Statistics")
        self.infoBox.setLayout(layout)

    def createCrawlerBox(self):
        self.crawlButton = QPushButton("Crawl")
        self.crawlButton.setFocusPolicy(Qt.NoFocus)

        self.websiteList = QComboBox()
        self.websiteList.addItem("HotNews")

        layout = QGridLayout()

        layout.addWidget(self.websiteList, 0, 0, 1, 1)
        layout.addWidget(self.crawlButton, 0, 1, 1, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        self.crawlerBox = QGroupBox("Crawler")
        self.crawlerBox.setLayout(layout)

    def createViewArticleBox(self):
        self.articleNumberLineEdit = QLineEdit("")
        self.articleNumberLineEdit.setAlignment(Qt.AlignHCenter)

        self.viewArticleButton = QPushButton("Open")
        self.viewArticleButton.clicked.connect(self.viewArticle)

        layout = QGridLayout()

        layout.addWidget(self.articleNumberLineEdit, 0, 0, 1, 1)
        layout.addWidget(self.viewArticleButton, 0, 1, 1, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        self.viewArticleBox = QGroupBox("View Article")
        self.viewArticleBox.setLayout(layout)

    def createReportBox(self):
        minDate, maxDate = self.selectMinAndMaxDate()
        minDate = QDate(minDate.year, minDate.month, minDate.day)
        maxDate = QDate(maxDate.year, maxDate.month, maxDate.day)

        self.fromDateEdit = QDateEdit()
        self.fromDateEdit.setDate(minDate)
        self.fromDateEdit.setDisplayFormat('d MMM yyyy')
        self.fromDateEdit.setAlignment(Qt.AlignHCenter)

        self.toDateEdit = QDateEdit()
        self.toDateEdit.setDate(maxDate)
        self.toDateEdit.setDisplayFormat('d MMM yyyy')
        self.toDateEdit.setAlignment(Qt.AlignHCenter)

        self.reportTypeComboBox = QComboBox()
        for item in reportTypes:
            self.reportTypeComboBox.addItem(item)

        monthlyButton = QPushButton("View")
        monthlyButton.clicked.connect(self.createReport)

        layout = QGridLayout()

        layout.addWidget(self.fromDateEdit,         0, 0, 1, 1)
        layout.addWidget(self.toDateEdit,           0, 1, 1, 1)
        layout.addWidget(self.reportTypeComboBox,   1, 0, 1, 1)
        layout.addWidget(monthlyButton,             1, 1, 1, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)

        self.raportBox = QGroupBox("Charts")
        self.raportBox.setLayout(layout)

    def createEntityBox(self):
        rows = self.selectCountEntities()

        self.entityList = QListWidget()
        entities = self.selectAllEntities()
        for entity in entities:
            self.doAssociationsForEntity(entity[1])
            self.entityList.addItem(entity[1])

        addButton = QPushButton("Add")
        addButton.clicked.connect(self.addEntity)

        removeButton = QPushButton("Delete")
        removeButton.clicked.connect(self.removeEntity)

        self.addEntityLineEdit = QLineEdit("")
        viewArticlesButton = QPushButton("View articles")
        viewArticlesButton.clicked.connect(self.viewArticleByEntity)

        self.algorithmComboBox = QComboBox()
        for key in classifiers.keys():
            self.algorithmComboBox.addItem(key)

        classifyButton = QPushButton("Classify")
        classifyButton.clicked.connect(self.classifyAllAssociations)

        layout = QGridLayout()
        layout.addWidget(self.entityList,           0, 0, 1, 4)
        layout.addWidget(self.addEntityLineEdit,    1, 0, 1, 2)
        layout.addWidget(addButton,                 1, 2, 1, 1)
        layout.addWidget(removeButton,              1, 3, 1, 1)
        layout.addWidget(viewArticlesButton,        2, 0, 1, 4)
        layout.addWidget(self.algorithmComboBox,    3, 0, 1, 2)
        layout.addWidget(classifyButton,            3, 2, 1, 2)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)

        self.entityBox = QGroupBox("Entities")
        self.entityBox.setLayout(layout)

    def createDatabaseBox(self):
        deleteClassificationsButton = QPushButton("Remove all classifications")
        deleteClassificationsButton.clicked.connect(self.clearAllCalculatedPolarities)

        deleteEntitiesButton = QPushButton("Remove all entities")
        deleteEntitiesButton.clicked.connect(self.deleteAllEntities)

        deleteAssociationsButton = QPushButton("Remove all associations")
        deleteAssociationsButton.clicked.connect(self.deleteAllAssociations)

        layout = QVBoxLayout()
        layout.addWidget(deleteClassificationsButton)
        layout.addWidget(deleteAssociationsButton)
        layout.addWidget(deleteEntitiesButton)

        self.databaseBox = QGroupBox("Database")
        self.databaseBox.setLayout(layout)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def monthsBetweenDates(self, fromDate, toDate):
        curDate = QDate(fromDate)
        months =[]

        while curDate < toDate:
            months.append(curDate)
            curDate = curDate.addMonths(1)

        return months

    def makeMonthlyPolarityChart(self, entities, fromDate, toDate):
        cursor = mysql_conn.cursor()

        chartData = []

        for (entityId, entity) in entities:
            monthlyPol = self.selectAllPolaritiesForEntity(entityId, fromDate, toDate)

            trace0=Bar(
                x = [self.monthYearLabel(month) for (month, _, _) in monthlyPol],
                y = [(0.0 + rows.count(1L)) / (l+1) * 100 for (_, l, rows) in monthlyPol],
                name = entity,
                marker = Marker(
                        color = 'rgb(204,204,204)',
                        opacity = 0.5,
                ),
            )
            chartData.append(trace0)

        chartData = Data(chartData)
        layout = Layout( 
            xaxis=XAxis(
                #set x-axis' labels direction at 45 degree angle
                tickangle=-45,
                ),
            barmode='group',
        )
        fig = Figure(data = chartData, layout = layout)
        py.image.save_as({'data': chartData}, "polarities.png")
        img = Image.open("polarities.png")
        img.show()

    def makeMonthlyAppearanceChart(self, entities, fromDate, toDate):
        cursor = mysql_conn.cursor()

        chartData = []

        for (entityId, entity) in entities:
            monthlyApp = self.selectCountAssociationsForEntityBetweenDates(entityId, fromDate, toDate)

            trace0=Bar(
                x = [self.monthYearLabel(month) for (month, _) in monthlyApp],
                y = [count for (_, count) in monthlyApp],
                name = entity,
                marker = Marker(
                        color = 'rgb(204,204,204)',
                        opacity = 0.5,
                ),
            )
            chartData.append(trace0)

        chartData = Data(chartData)
        layout = Layout( 
            xaxis=XAxis(
                #set x-axis' labels direction at 45 degree angle
                tickangle=-45,
                ),
            barmode='group',
        )
        fig = Figure(data = chartData, layout = layout)
        py.image.save_as({'data': chartData}, "appearances.png")
        img = Image.open("appearances.png")
        img.show()

    def getStringDate(self, date):
        sDate = str(date.year())
        sDate += '-'+str(date.month())
        sDate += '-'+'01'
        time = '00:00:00'
        return sDate + ' ' + time

    def monthYearLabel(self, date):
        label = monthIntToString[date.month()] + ' '
        label += str(date.year())
        return label

    def createReport(self):
        reportType = self.reportTypeComboBox.currentText()
        fromDate = self.fromDateEdit.date()
        toDate = self.toDateEdit.date()
        entities = []

        if "All entities" in reportType:
            entities = self.selectAllEntities()
        else:
            selected = self.entityList.selectedItems()
            if len(selected) == 1:
                entity = selected[0].text()
                entities = [(self.selectEntityId(entity), entity)]

        if len(entities) > 0:
            if "Opinions" in reportType:
                self.makeMonthlyPolarityChart(entities, fromDate, toDate)
            else:
                print entities
                self.makeMonthlyAppearanceChart(entities, fromDate, toDate)

    def viewArticle(self):
        try:
            articleId = int(self.articleNumberLineEdit.text())
            if articleId > 0 and articleId < self.articleCount:
                self.viewArticleButton.setEnabled(False)
                self.articleNumberLineEdit.setDisabled(True)

                articleList = [i+1 for i in xrange(self.articleCount)]
                articleView = Article(articleId-1, articleList, parentW=self)
                articleView.exec_()

                self.viewArticleButton.setEnabled(True)
                self.articleNumberLineEdit.setDisabled(False)
        except ValueError:
            print "Invalid article id"

    def viewArticleByEntity(self):
        selected = self.entityList.selectedItems()

        if len(selected) == 1:
            articles = self.selectAllArticlesByEntity(selected[0].text())
            articleList = [a[0] for a in articles]
            articleView = Article(0, articleList, shuffle_=True, parentW=self)
            articleView.exec_()

    def addEntity(self):
        newEntity = self.addEntityLineEdit.text().strip()
        newEntity = re.sub(r' +', ' ', newEntity)
        cursor = mysql_conn.cursor()

        if len(newEntity) != 0:
            selectStmt = """SELECT *
                            FROM entities
                            WHERE entity=%s"""
            data = (newEntity,)
            cursor.execute(selectStmt, data)
            rows = cursor.fetchall()

            if len(rows) == 0:
                insertStmt = """INSERT INTO entities (entity)
                                VALUES (%s)"""
                data = (newEntity,)
                cursor.execute(insertStmt, data)
                cursor.execute("""COMMIT""")

                self.entityUpdate.emit()
                self.doAssociationsForEntity(newEntity)
                self.addEntityLineEdit.setText("")

    def removeEntity(self):
        selected = self.entityList.selectedItems()
        cursor = mysql_conn.cursor()

        for item in selected:
            self.deleteAssciationsForEntity(item.text())

            selectStmt = """SELECT entity_id
                            FROM entities
                            WHERE entity=%s"""
            data = (item.text(),)
            cursor.execute(selectStmt, data)
            entityId = cursor.fetchone()

            deleteStmt = """DELETE FROM entities
                            WHERE entity_id=%s"""
            data = (entityId[0],)
            cursor.execute(deleteStmt, data)
            cursor.execute("""COMMIT""")

            self.entityUpdate.emit()

    def updateEntityList(self):
        self.entityList.clear()
        entities = self.selectAllEntities()
        for entity in entities:
            self.entityList.addItem(entity[1])

        label = "Number of entities: " + str(len(entities))
        self.entitiesCountLabel.setText(label)

    def updateArticleInfo(self):
        self.articleCount = self.selectCountArticles()
        entityCount = self.selectCountEntities()
        associationsCount = self.selectCountAssociations()
        classifiedCount = self.selectCountClassifiedAssociations()

        label = "Number of articles: " + str(self.articleCount)
        self.articleCountLabel.setText(label)

        label = "Number of entities: " + str(entityCount)
        self.entitiesCountLabel.setText(label)

        label = "Number of classified associations: " + str(classifiedCount)
        self.classifiedCountLabel.setText(label)

        label = "Number of associations: " + str(associationsCount)
        self.associationsCountLabel.setText(label)

    def classifyAllAssociations(self):
        cursor = mysql_conn.cursor()

        entities = self.selectAllEntities()
        for (entityId, entity) in entities:
            manualPol = self.selectManualPolaritiesForEntity(entityId)
            trainingData = [self.selectArticle(id_)[4] for (id_, _) in manualPol]
            trainingTarget = [polarity for (_, polarity) in manualPol]

            algorithm = self.algorithmComboBox.currentText()
            textClf = Pipeline([('vect', CountVectorizer()),
                                ('tfidf', TfidfTransformer()),
                                ('clf', classifiers[algorithm]),
                                ])
            textClf.fit(trainingData, trainingTarget)

            # select all articles associated with entity that need to be classified
            selectStmt = """SELECT article_id
                            FROM assocEntityArticle
                            WHERE polarity_manual IS NULL
                            AND polarity_calculated IS NULL
                            AND entity_id=%s"""
            data = (entityId,)
            cursor.execute(selectStmt, data)
            ids = cursor.fetchall()

            if len(ids) > 0:
                ids = [a[0] for a in ids]
                testData = [self.selectArticle(id_)[4] for id_ in ids]

                predicted = textClf.predict(testData)
                print [x for x in predicted].count(1)
                updateData = zip(predicted, ids)
                updateData = [(polarity, entityId, id_) for (polarity, id_) in updateData]

                updateStmt = """UPDATE assocEntityArticle
                                SET polarity_calculated=%s
                                WHERE entity_id=%s AND article_id=%s"""
                cursor.executemany(updateStmt, updateData)
                cursor.execute("""COMMIT""")

                self.articleInfoUpdate.emit()

    def selectArticle(self, articleId):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT *
                        FROM articles
                        WHERE article_id=%s"""
        data = (articleId,)
        cursor.execute(selectStmt, data)
        row = cursor.fetchone()

        return row

    def selectEntityId(self, entity):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT entity_id
                FROM entities
                WHERE entity=%s"""
        data = (entity,)
        cursor.execute(selectStmt, data)
        entityId = cursor.fetchone()[0]

        return entityId

    def selectAllArticlesByEntity(self, entity):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT *
                        FROM articles
                        WHERE content LIKE %s"""
        data = ("%" + entity + "%",)
        cursor.execute(selectStmt, data)
        rows = cursor.fetchall()

        return rows

    def selectAllEntities(self):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT *
                        FROM entities"""
        cursor.execute(selectStmt)
        rows = cursor.fetchall()

        return rows

    def selectMinAndMaxDate(self):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT MIN(date), MAX(date)
                        FROM articles"""
        cursor.execute(selectStmt)
        row = cursor.fetchone()

        return row

    def selectCountArticles(self):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT count(*)
                        FROM articles"""
        cursor.execute(selectStmt)
        row = cursor.fetchone()

        return row[0]

    def selectCountAuthors(self):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT count(*)
                        FROM authors"""
        cursor.execute(selectStmt)
        row = cursor.fetchone()

        return row[0]

    def selectCountEntities(self):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT count(*)
                        FROM entities"""
        cursor.execute(selectStmt)
        row = cursor.fetchone()

        return row[0]

    def selectCountAssociations(self):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT count(*)
                        FROM assocEntityArticle"""
        cursor.execute(selectStmt)
        row = cursor.fetchone()

        return row[0]

    def selectCountAssociationsForEntityBetweenDates(self, entityId, fromDate, toDate):
        cursor = mysql_conn.cursor()
        months = self.monthsBetweenDates(fromDate, toDate)

        selectStmt = """SELECT count(*)
                        FROM assocEntityArticle a, articles b
                        WHERE a.article_id = b.article_id
                        AND b.date BETWEEN %s AND %s
                        AND a.entity_id=%s"""
        associations = []
        if len(months) != 0:
            for month in months:
                fromDateString = self.getStringDate(month)
                toDateString = self.getStringDate(month.addMonths(1))
                data = (fromDateString, toDateString, entityId)
                cursor.execute(selectStmt, data)
                count = cursor.fetchone()[0]
                associations.append((month, count))

        return associations

    def selectCountClassifiedAssociations(self):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT count(*)
                        FROM assocEntityArticle
                        WHERE polarity_calculated IS NOT NULL
                        OR polarity_manual IS NOT NULL"""
        cursor.execute(selectStmt)
        row = cursor.fetchone()

        return row[0]

    def selectManualPolaritiesForEntity(self, entityId):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT article_id, polarity_manual
                        FROM assocEntityArticle
                        WHERE polarity_manual IS NOT NULL
                        AND entity_id=%s"""
        data = (entityId,)
        cursor.execute(selectStmt, data)
        rows = cursor.fetchall()

        return rows

    def selectAllPolaritiesForEntity(self, entityId, fromDate, toDate):
        cursor = mysql_conn.cursor()
        months = self.monthsBetweenDates(fromDate, toDate)

        selectStmt = """SELECT a.polarity_manual, a.polarity_calculated
                        FROM assocEntityArticle a, articles b
                        WHERE (a.polarity_manual IS NOT NULL
                            OR a.polarity_calculated IS NOT NULL)
                        AND a.article_id = b.article_id
                        AND b.date BETWEEN %s AND %s
                        AND a.entity_id=%s"""

        polarities = []
        if len(months) != 0:
            for month in months:
                fromDateString = self.getStringDate(month)
                toDateString = self.getStringDate(month.addMonths(1))
                data = (fromDateString, toDateString, entityId)
                cursor.execute(selectStmt, data)
                rows = cursor.fetchall()
                rows = [a or b for a, b in rows]
                polarities.append((month, len(rows), rows))

        return polarities

    def doAssociationsForEntity(self, entity):
        cursor = mysql_conn.cursor()

        # select entity_id for entity given as parameter
        entityId = self.selectEntityId(entity)

        # select list of article_id for which associations exist
        # in database for entity given as param
        selectStmt = """SELECT article_id
                        FROM assocEntityArticle
                        WHERE entity_id=%s"""
        data = (entityId,)
        cursor.execute(selectStmt, data)
        articleIdsInDB = cursor.fetchall()
        articleIdsInDB = [pair[0] for pair in articleIdsInDB]

        # select all articles that contain entity in content
        selectStmt = """SELECT article_id
                        FROM articles
                        WHERE content LIKE %s"""
        data = ("%" + entity + "%",)
        cursor.execute(selectStmt, data)
        rows = cursor.fetchall()
        rows = [pair[0] for pair in rows]

        # find articles for which associations don't exist in the database
        diff = list(set(rows) - set(articleIdsInDB))
        if len(diff) != 0:
            insertStmt = """INSERT INTO assocEntityArticle (article_id, entity_id)
                            VALUES (%s, %s)"""
            data = [(articleId, entityId) for articleId in diff]
            cursor.executemany(insertStmt, data)
            cursor.execute("""COMMIT""")

            self.articleInfoUpdate.emit()

    def deleteAssciationsForEntity(self, entity):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT entity_id
                        FROM entities
                        WHERE entity=%s"""
        data = (entity,)
        cursor.execute(selectStmt, data)
        entityId = cursor.fetchone()[0]

        deleteStmt = """DELETE FROM assocEntityArticle
                        WHERE entity_id=%s"""
        data = (entityId,)
        cursor.execute(deleteStmt, data)
        cursor.execute("""COMMIT""")

        self.articleInfoUpdate.emit()

    def doAllAssociations(self):
        cursor = mysql_conn.cursor()

        entities = self.selectAllEntities()
        for entity in entities:
            self.doAssociationsForEntity(entity)

        self.articleInfoUpdate.emit()

    def deleteAllAssociations(self):
        cursor = mysql_conn.cursor()

        deleteStmt = """DELETE FROM assocEntityArticle
                        WHERE article_id > 0"""
        cursor.execute(deleteStmt)
        cursor.execute("""COMMIT""")

        self.articleInfoUpdate.emit()

    def clearAllCalculatedPolarities(self):
        cursor = mysql_conn.cursor()

        updateStmt = """UPDATE assocEntityArticle
                        SET polarity_calculated=%s
                        WHERE polarity_calculated IS NOT NULL"""
        data = (None,)
        cursor.execute(updateStmt, data)
        cursor.execute("""COMMIT""")

        self.articleInfoUpdate.emit()

    def deleteAllArticles(self):
        try:
            cursor = mysql_conn.cursor()

            deleteStmt = """DELETE FROM articles
                            WHERE article_id > 0"""
            cursor.execute(deleteStmt)
            alterTableStmt = """ALTER TABLE articles AUTO_INCREMENT = 1"""
            cursor.execute(alterTableStmt)
            cursor.execute("""COMMIT""")

            self.articleInfoUpdate.emit()
        except IntegrityError:
            pass

    def deleteAllAuthors(self):
        cursor = mysql_conn.cursor()

        deleteStmt = """DELETE FROM authors
                        WHERE author_id > 0"""
        cursor.execute(deleteStmt)
        alterTableStmt = """ALTER TABLE authors AUTO_INCREMENT = 1"""
        cursor.execute(alterTableStmt)
        cursor.execute("""COMMIT""")

    def deleteAllArticlesAndAuthors(self):
        self.deleteAllArticles()
        self.deleteAllAuthors()

    def deleteAllEntities(self):
        cursor = mysql_conn.cursor()

        deleteStmt = """DELETE FROM entities
                        WHERE entity_id > 0"""
        cursor.execute(deleteStmt)
        alterTableStmt = """ALTER TABLE entities AUTO_INCREMENT = 1"""
        cursor.execute(alterTableStmt)
        cursor.execute("""COMMIT""")

        self.articleInfoUpdate.emit()
        self.entityUpdate.emit()

if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
