from PySide2.QtWidgets import *

from PortalParser.window import Ui_MainWindow
from PortalParser import serverFunctions

import sys
import pandas as pd
import datetime
from tqdm import tqdm
import os
print(os.getcwd())

TYPEDICT = {
    1: 'Integer',
    2: 'Float',
    3: 'Float',
    6: 'Date',
    9: 'String',
    11: 'Binary',
    12: 'Binary'
}


class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.Form = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.Form)

        self.ui.radioButtonAllAttrs.setChecked(True)
        self.ui.radioButtonAllClasses.setChecked(True)
        self.ui.tabWidget.setHidden(True)
        self.ui.lineEdit.setHidden(True)
        self.ui.spinBox.setButtonSymbols(QAbstractSpinBox.NoButtons)

        self.ui.radioButtonAllAttrs.clicked.connect(self.change)
        self.ui.radioButtonAllClasses.clicked.connect(self.change)
        self.ui.radioButtonSelAttrs.clicked.connect(self.change)
        self.ui.radioButtonSelAttrs.clicked.connect(self.tabChangeAttr)
        self.ui.radioButtonSelClasses.clicked.connect(self.change)
        self.ui.radioButtonSelClasses.clicked.connect(self.tabChangeClass)
        self.ui.actionUpdate.triggered.connect(self.update)
        self.ui.lineEdit.textChanged.connect(self.filter)
        self.ui.pushButton.clicked.connect(self.parse)
        self.ui.PortalNameBox.currentIndexChanged.connect(self.changePortal)
        self.ui.PortalLine.editingFinished.connect(self.changePortal)
        self.ui.actionAttributes.triggered.connect(self.unloadAttrs)
        self.ui.actionClasses.triggered.connect(self.unloadClasses)
        self.ui.actionHide.triggered.connect(self.change)

        self.ui.actionCSV.setChecked(True)

        self.changePortal()

        self.Form.show()
        sys.exit(self.app.exec_())

    def tabChangeClass(self):
        self.ui.tabWidget.setCurrentIndex(1)

    def tabChangeAttr(self):
        self.ui.tabWidget.setCurrentIndex(0)

    def change(self):
        if self.ui.radioButtonSelAttrs.isChecked() or self.ui.radioButtonSelClasses.isChecked():
            if self.ui.tabWidget.isHidden():
                self.ui.tabWidget.setHidden(False)
                self.ui.lineEdit.setHidden(False)
                self.Form.setFixedSize(self.Form.width() + 392, self.Form.height())
        else:
            self.ui.tabWidget.setHidden(True)
            self.ui.lineEdit.setHidden(True)
            self.Form.setFixedSize(self.Form.width() - 392, self.Form.height())

    def update(self):
        # print(self.PortalName)
        self.key = serverFunctions.login(self.PortalName)
        # print(self.ui.PortalNameBox.currentText())
        self.attrs = serverFunctions.getAttrsFromSite(self.PortalName, self.key,self.Verify)
        self.classes = serverFunctions.getClassesFromSite(self.PortalName, self.key,self.Verify)
        for i in self.attrs.getNameIdDict():
            self.ui.textEdit_2.append(i)
        for i in self.classes.getNameIdDict():
            self.ui.textEdit.append(i)

    def changePortal(self):
        # print(self.ui.PortalLine.text())
        if self.ui.PortalLine.text() == '':
            self.PortalName = self.ui.PortalNameBox.currentText()
        else:
            self.PortalName = self.ui.PortalLine.text()

        if self.PortalName != 'https://192.168.200.52/':
            self.ui.verifyBox.setChecked(True)
        else:
            self.ui.verifyBox.setChecked(False)

        self.Verify = self.ui.verifyBox.isChecked()

        self.ui.textEdit_2.clear()
        self.ui.textEdit.clear()
        self.update()


    def filter(self):
        obj = self.ui.textEdit_2 if self.ui.tabWidget.currentIndex() == 0 else self.ui.textEdit
        obj.clear()
        type = self.attrs.getNameIdDict() if self.ui.tabWidget.currentIndex() == 0 else self.classes.getNameIdDict()

        for i in type.keys():
            if i.lower().find(self.ui.lineEdit.text().lower()) != -1:
                obj.append(i)

    def parse(self):
        self.attrs = serverFunctions.getAttrsFromSite(self.PortalName, self.key,self.Verify)
        self.classes = serverFunctions.getClassesFromSite(self.PortalName, self.key,self.Verify)
        self.references = serverFunctions.getRefsFromSite(self.PortalName, self.key,self.Verify)
        if self.ui.radioButtonSelAttrs.isChecked():
            try:
                attrs = [self.attrs.getNameIdDict()[i] for i in self.ui.CheckedAttrs.toPlainText().split('\n')]
            except:
                attrs = []
        else:
            attrs = list(self.attrs.getIdNameDict().keys())

        if self.ui.radioButtonSelClasses.isChecked():
            classes = [self.classes.getNameIdDict()[i] for i in self.ui.CheckedClasses.toPlainText().split('\n')]
        else:
            classes = list(self.classes.getIdNameDict().keys())

        if self.ui.radioButtonSelRefs.isChecked():
            try:
                references = [self.references.getNameIdDict()[i] for i in self.ui.CheckedRefs.toPlainText().split('\n')]
            except:
                references = []
        else:
            references = list(self.references.getIdNameDict().keys())



        skip = self.ui.skipNum.value()
        take = self.ui.takeNum.value()
        # print(attrs)
        # print(classes)

        renameColumns = {'properties.' + i: self.attrs.getIdNameDict()[i] for i in self.attrs.getIdNameDict()}
        renameColumns['id'] = 'Entity Id'
        renameColumns['classId'] = 'classId'
        renameColumns['path'] = 'path'
        renameColumns['permissions'] = 'permissions'
        renameColumns['searchPath'] = 'searchPath'
        renameColumns['links.097c0fd9-f2b9-4810-b4d6-469d28758539'] = 'link'
        for i in self.references.getIdNameDict():
            renameColumns['links.' + i] = self.references.getIdNameDict()[i]

        fileAttrs = []
        for i in self.attrs.getNameClassDict():
            if (self.attrs.getNameClassDict()[i].type == 11 or self.attrs.getNameClassDict()[i].type == 12):
                fileAttrs.append(i)


        for i in renameColumns.copy():
            if renameColumns[i] in fileAttrs:
                renameColumns[i + '.id'] = renameColumns[i] + '.id'
                renameColumns[i + '.hash'] = renameColumns[i] + '.hash'
                renameColumns[i + '.name'] = renameColumns[i] + '.name'
                renameColumns[i + '.size'] = renameColumns[i] + '.size'
                renameColumns[i + '.type'] = renameColumns[i] + '.type'


        self.ui.statusbar.showMessage('Getting data...')


        if self.ui.unloadByParts.isChecked():
            df1 = pd.DataFrame()
            nodes = serverFunctions.sendReqTreeData(self.PortalName, self.ui.spinBox.value(), self.key, self.Verify)[
                'items']
            for i in tqdm(nodes):
                node = i['entity']['id']
                data = serverFunctions.Query(self.PortalName, node, self.key, classes, attrs, references, skip, take,
                                             self.Verify,self.ui.checkBox.isChecked())
                df = pd.json_normalize(data['items'])
                df1 = df1.append(df, ignore_index=True)
        else:
            data = serverFunctions.Query(self.PortalName, self.ui.spinBox.value(), self.key, classes, attrs, references, skip, take,
                                         self.Verify,self.ui.checkBox.isChecked())
            print(data)
            df1 = pd.json_normalize(data['items'])
        print(df1)



        self.ui.statusbar.showMessage('Parsing data...')

        df1.rename(columns=lambda x: renameColumns[x], inplace=True)
        try:
            df1.drop(['permissions'], axis=1, inplace=True)
        except:
            pass

        for ind in df1.index:
            df1.at[ind, 'className'] = self.classes.getIdNameDict()[df1.at[ind, 'classId']]
        cols = df1.columns.tolist()
        cols.remove('className')
        cols.insert(2, 'className')
        df1 = df1[cols]
        # print(df1)
        fname = QFileDialog.getSaveFileName(filter='*.csv')
        #
        if self.ui.actionExcel.isChecked():
            self.ui.statusbar.showMessage('Saving Excel')
            df1.to_excel(fname[0] + '.xlsx')
            self.ui.statusbar.showMessage('Excel Saved')

        if self.ui.actionCSV.isChecked():
            self.ui.statusbar.showMessage('Saving Csv')
            df1.to_csv(fname[0],encoding='1251',sep = ';',decimal=',')
            self.ui.statusbar.showMessage('Csv Saved')



        # except Exception as e:
        #     print(e)
        #     self.ui.statusbar.showMessage(str(e))

    def unloadAttrs(self):
        attrs = self.attrs.getNameClassDict()
        df = pd.DataFrame(columns=['Id', 'Name', 'Type', 'System'])
        for i in attrs:
            df = df.append(
                {
                    'Id': attrs[i].id,
                    'Name': attrs[i].name,
                    'Type': attrs[i].type,
                    'System': attrs[i].system
                }, ignore_index=True
            )
        for ind in df.index:
            df.at[ind, 'TypeName'] = TYPEDICT[df.at[ind, 'Type']]
        cols = df.columns.tolist()
        cols.remove('TypeName')
        cols.insert(3, 'TypeName')
        df = df[cols]
        fname = QFileDialog.getSaveFileName(filter='*.xlsx')
        df.to_excel(fname[0])

    def unloadClasses(self):
        classes = self.classes.getIdNameDict()
        df = pd.DataFrame(columns=['Id', 'Name'])
        for i in classes:
            df = df.append(
                {
                    'Id': i,
                    'Name': classes[i]
                }, ignore_index=True
            )
        # print(df)
        fname = QFileDialog.getSaveFileName(filter='*.xlsx')
        df.to_excel(fname[0])


now = datetime.datetime.now()
if now.month == 1:
    App()
else:
    print('Program License Expired')
