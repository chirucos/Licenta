from datetime import datetime

from crawler.settings import mysql_conn

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QApplication, QWidget, QDesktopWidget
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QComboBox
from PyQt5.QtWidgets import QSizePolicy, QLineEdit, QTextBrowser, QDialog
from PyQt5.QtWidgets import QGridLayout, QFrame

from random import shuffle
import sys
import re

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB

dClassToInt = {
    'positive': 1,
    'neutral': 0,
    'negative': -1
}

dIntToClass = {
    1: 'positive',
    0: 'neutral',
    -1: 'negative',
    None: ''
}


class Article(QDialog):

    def __init__(self, listIndexArticle, articleList, parentW=None, shuffle_=False):
        super(Article, self).__init__()

        self.parentW = parentW
        self.articleList = articleList
        if shuffle_ == True:
            shuffle(self.articleList)
        self.articleId = self.articleList[listIndexArticle]
        self.listIndexArticle = listIndexArticle
        self.selectArticle(self.articleId)


        self.setWindowTitle("Article id: " + str(self.articleId))
        self.initUI()

    def initUI(self):
        self.setGeometry(1030, 220, 400, 700)

        mainLayout = QVBoxLayout()

        self.createNavigationWidget()
        self.createTitleBox()
        self.createAuthorBox()
        self.createDateBox()
        self.createContentBrowser()
        self.createEntitiesBox()

        mainLayout.addWidget(self.titleBox)
        mainLayout.addWidget(self.authorBox)
        mainLayout.addWidget(self.dateBox)
        mainLayout.addWidget(self.contentBrowser)
        mainLayout.addWidget(self.entityBox)
        mainLayout.addWidget(self.navigationWidget)

        self.setLayout(mainLayout)

        self.show()

    def createNavigationWidget(self):
        previousButton = QPushButton("<")
        previousButton.setFocusPolicy(Qt.NoFocus)
        previousButton.clicked.connect(self.previousArticle)

        nextButton = QPushButton(">")
        nextButton.setFocusPolicy(Qt.NoFocus)
        nextButton.clicked.connect(self.nextArticle)

        layout = QHBoxLayout()
        layout.addWidget(previousButton)
        layout.addWidget(nextButton)

        self.navigationWidget = QWidget()
        self.navigationWidget.setLayout(layout)

    def createTitleBox(self):
        self.titleLabel = QLabel(self.articleTitle)
        self.titleLabel.setWordWrap(True)

        layout = QHBoxLayout()
        layout.addWidget(self.titleLabel)

        self.titleBox = QGroupBox("Title")
        self.titleBox.setLayout(layout)

    def createAuthorBox(self):
        self.authorLabel = QLabel(self.articleAuthor)

        layout = QHBoxLayout()
        layout.addWidget(self.authorLabel)

        self.authorBox = QGroupBox("Author")
        self.authorBox.setLayout(layout)

    def createDateBox(self):
        self.dateLabel = QLabel(str(self.articleDate))

        layout = QHBoxLayout()
        layout.addWidget(self.dateLabel)

        self.dateBox = QGroupBox("Date")
        self.dateBox.setLayout(layout)

    def createContentBrowser(self):
        self.contentBrowser = QTextBrowser(self)
        self.contentBrowser.setPlainText(self.articleContent)
        self.contentBrowser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def createEntitiesBox(self):
        layout = self.createEntityGridLayout()

        self.entityBox = QGroupBox("Entities - Opinions")
        self.entityBox.setLayout(layout)

        if len(self.entities) == 0:
            self.entityBox.setVisible(False)
        else:
            self.entityBox.setVisible(True)

    def updateEntityBox(self):
        QWidget().setLayout(self.entityBox.layout())
        layout = self.createEntityGridLayout()

        self.entityBox.setLayout(layout)

        if len(self.entities) == 0:
            self.entityBox.setVisible(False)
        else:
            self.entityBox.setVisible(True)

    def createEntityGridLayout(self):
        self.entities = self.selectEntitiesInArticle()

        self.manualClassLabels = []
        self.calculatedClassLabels = []

        # header labels
        calculatedLabel = QLabel("Calculated")
        calculatedLabel.setAlignment(Qt.AlignCenter)

        manualLabel = QLabel("Manual")
        manualLabel.setAlignment(Qt.AlignCenter)

        layout = QGridLayout()
        layout.addWidget(calculatedLabel,   0, 2, 1, 1)
        layout.addWidget(manualLabel,       0, 3, 1, 1)

        # entity rows
        for i in xrange(len(self.entities)):
            entityLabel = QLabel(self.entities[i][1])
            entityLabel.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            polarity = self.selectPolarityForEntityInArticle(self.articleId, self.entities[i][0])

            manualClass = QLineEdit(dIntToClass[polarity[0]])
            manualClass.setAlignment(Qt.AlignCenter)

            calculatedClass = QLabel(dIntToClass[polarity[1]])
            calculatedClass.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            calculatedClass.setAlignment(Qt.AlignCenter)

            self.manualClassLabels.append(manualClass)
            self.calculatedClassLabels.append(calculatedClass)

            layout.addWidget(entityLabel,       i+1, 0, 1, 2)
            layout.addWidget(calculatedClass,   i+1, 2, 1, 1)
            layout.addWidget(manualClass,       i+1, 3, 1, 1)

        # buttons row
        classifyButton = QPushButton("Classify")
        classifyButton.setFocusPolicy(Qt.NoFocus)
        classifyButton.clicked.connect(self.classifyEntitiesInArticle)

        clearButton = QPushButton("Clear")
        clearButton.clicked.connect(self.clearClassification)
        clearButton.setFocusPolicy(Qt.NoFocus)

        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.saveClassification)
        saveButton.setFocusPolicy(Qt.NoFocus)

        layout.addWidget(classifyButton,    len(self.entities) + 1, 1, 1, 1)
        layout.addWidget(clearButton,       len(self.entities) + 1, 2, 1, 1)
        layout.addWidget(saveButton,        len(self.entities) + 1, 3, 1, 1)

        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        layout.setColumnStretch(3, 1)

        return layout

    def draw(self):
        self.titleLabel.setText(self.articleTitle)
        self.authorLabel.setText(self.articleAuthor)
        self.dateLabel.setText(str(self.articleDate))
        self.contentBrowser.setText(self.articleContent)
        self.updateEntityBox()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()

        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def previousArticle(self):
        if self.listIndexArticle > 0:
            self.listIndexArticle -= 1
            self.articleId = self.articleList[self.listIndexArticle]
            self.selectArticle(self.articleList[self.listIndexArticle])
            self.setWindowTitle("Article id: " + str(self.articleId))
            self.draw()

    def nextArticle(self):
        if self.listIndexArticle < len(self.articleList) - 1:
            self.listIndexArticle += 1
            self.articleId = self.articleList[self.listIndexArticle]
            self.selectArticle(self.articleList[self.listIndexArticle])
            self.setWindowTitle("Article id: " + str(self.articleId))
            self.draw()

    def saveClassification(self):
        cursor = mysql_conn.cursor()

        for i in xrange(len(self.manualClassLabels)):
            lineEdit = self.manualClassLabels[i]
            text = lineEdit.text().strip()
            if text in dClassToInt.keys():
                updateStmt = """UPDATE assocEntityArticle
                                SET polarity_manual=%s, polarity_calculated=%s
                                WHERE article_id=%s AND entity_id=%s"""
                data = (dClassToInt[text], None, self.articleId, self.entities[i][0])
                cursor.execute(updateStmt, data)
                cursor.execute("""COMMIT""")
            elif len(text) == 0:
                updateStmt = """UPDATE assocEntityArticle
                                SET polarity_manual=%s
                                WHERE article_id=%s AND entity_id=%s"""
                data = (None, self.articleId, self.entities[i][0])
                cursor.execute(updateStmt, data)
                cursor.execute("""COMMIT""")

        self.parentW.articleInfoUpdate.emit()
        self.updateEntityBox()

    def classifyEntitiesInArticle(self):
        cursor = mysql_conn.cursor()

        for i in xrange(len(self.entities)):
            if len(self.calculatedClassLabels[i].text().strip()) == 0:
                entityId, entity = self.entities[i]
                manualPol = self.selectManualPolaritiesForEntity(entityId)
                trainingData = [self.selectArticle(id_)[4] for (id_, _) in manualPol]
                trainingTarget = [polarity for (_, polarity) in manualPol]

                countVect = CountVectorizer()
                trainingDataCounts = countVect.fit_transform(trainingData)
                tfidfTransformer = TfidfTransformer()
                trainingTfidf = tfidfTransformer.fit_transform(trainingDataCounts)

                clf = MultinomialNB().fit(trainingTfidf, trainingTarget)

                testData = [self.articleContent]
                testDataCounts = countVect.transform(testData)
                testTfidf = tfidfTransformer.transform(testDataCounts)

                predicted = clf.predict(testTfidf)


    def clearClassification(self):
        cursor = mysql_conn.cursor()

        for i in xrange(len(self.entities)):
            updateStmt = """UPDATE assocEntityArticle
                            SET polarity_calculated=%s
                            WHERE article_id=%s AND entity_id=%s"""
            data = (None, self.articleId, self.entities[i][0])
            cursor.execute(updateStmt, data)
            cursor.execute("""COMMIT""")

        self.parentW.articleInfoUpdate.emit()
        self.updateEntityBox()

    def selectArticle(self, articleId):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT *
                        FROM articles
                        WHERE article_id=%s"""
        data = (articleId,)
        cursor.execute(selectStmt, data)
        row = cursor.fetchone()

        self.articleTitle = row[1]
        self.articleDate = row[2]
        self.articleAuthor = self.selectAuthor(row[3])
        self.articleContent = row[4]

        return row

    def selectAuthor(self, id):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT *
                        FROM authors
                        WHERE author_id=%s"""
        data = (id,)
        cursor.execute(selectStmt, data)
        rows = cursor.fetchone()

        return rows[1]

    def selectCountArticles(self):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT count(*)
                        FROM articles"""
        cursor.execute(selectStmt)
        rows = cursor.fetchone()

        return rows[0]

    def selectEntitiesInArticle(self):
        cursor = mysql_conn.cursor()
        entities = []

        selectStmt = """SELECT entity_id
                        FROM assocEntityArticle
                        WHERE article_id=%s"""
        data = (self.articleId,)
        cursor.execute(selectStmt, data)
        listOfEntityIds = cursor.fetchall()
        listOfEntityIds = [pair[0] for pair in listOfEntityIds]

        selectStmt = """SELECT entity
                        FROM entities
                        WHERE entity_id=%s"""
        for entityId in listOfEntityIds:
            data = (entityId,)
            cursor.execute(selectStmt, data)
            entity = (entityId, cursor.fetchone()[0])
            entities.append(entity)

        return entities

    def selectPolarityForEntityInArticle(self, articleId, entityId):
        cursor = mysql_conn.cursor()

        selectStmt = """SELECT polarity_manual, polarity_calculated
                        FROM assocEntityArticle
                        WHERE article_id=%s AND entity_id=%s"""
        data = (articleId, entityId)

        cursor.execute(selectStmt, data)
        return cursor.fetchone()

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

if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Article(1)
    sys.exit(app.exec_())
