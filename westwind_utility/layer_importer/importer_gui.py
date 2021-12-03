import os
from qgis.core import *
import re
from operator import itemgetter, attrgetter, methodcaller
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from .importer_core import ImporterCore

from qgis.PyQt.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox
#from ply.lex import runmain


class ImporterGui:

    def __init__(self,_dockWidget):
        self.vectorPath = None
        print("Starting Importer")
        self.dockWidget = _dockWidget
        self.dockWidget.LI_existingLayersRadioButton.setChecked(True)
        self.dockWidget.pushButton_7.clicked.connect(self.printStuff)
        self.dockWidget.LI_importPushButton.clicked.connect(self.runImport)
        
        self.initializeDirs()
        self.core = ImporterCore(self.dockWidget, self.vectorPath)
        self.dockWidget.LI_clearLogBoxPushButton.clicked.connect(self.clearLogBox)
        self.dockWidget.LI_collapseSSCheckBox.clicked.connect(self.handleSSCollapseCheckBox)
        self.dockWidget.LI_expandSSCheckBox.clicked.connect(self.handleSSExpandCheckBox)
        self.dockWidget.LI_selectDirPushButton.clicked.connect(self.selectDir)
        self.dockWidget.LI_EnableDevPushButton.clicked.connect(self.enableDevMode)
        #self.dockWidget.checkBox_6.setChecked(True)
        self.dockWidget.pushButton_4.clicked.connect(self.featureTest)
        self.dockWidget.LI_updatePushButton.clicked.connect(self.runUpdate)
        #self.dockWidget.pushButton_4.clicked.connect(self.showDialog)
        self.dockWidget.WWEU_tab.setCurrentIndex(0)

        self.dockWidget.pushButton.clicked.connect(self.printStuff)

        self.readSettings()

        if self.dockWidget.tabWidget.currentIndex() != 0:
            self.dockWidget.tabWidget.setCurrentIndex(0)
        print(f"The current index is {self.dockWidget.tabWidget.currentIndex()}")

        if self.dockWidget.LI_EnableDevPushButton.isChecked():
            self.dockWidget.tabWidget.setTabEnabled(2, True)
        else:
            self.dockWidget.tabWidget.setTabEnabled(2, False)
        self.printStuff()
        print("Importer Started")

    def printStuff(self):
        print("printing some stuff")
        text=self.dockWidget.ignoreFoldersTextEdit.toPlainText()
        print(text)
        stringList = text.split("\n")
        print(stringList)

    def featureTest(self):

        self.core.runOrderLayers() 
        #self.core.runHandleSS()   

    def setProgressBarBusy(self):
        self.dockWidget.progressBar.setMinimum(0)
        self.dockWidget.progressBar.setMaximum(0)
        self.dockWidget.progressBar.setValue(0)

    def setProgressBarComplete(self):
        self.dockWidget.progressBar.setMinimum(0)
        self.dockWidget.progressBar.setMaximum(1)
        self.dockWidget.progressBar.setValue(1)

    def runImport(self):
        print("Running layer import")
        if self.vectorPath is None:
            self.showDialog()

        if self.dockWidget.LI_existingLayersRadioButton.isChecked():
            ignoreFolders=self.dockWidget.ignoreFoldersTextEdit.toPlainText().split("\n")
            importList = self.core.getImportExistingLayersList(ignoreFolders,self.dockWidget.LI_LimitVersionsCheckBox.isChecked())

            self.core.importExistingLayersList(importList)
            #self.core.runMain()
            #if self.dockWidget.LI_LimitVersionsCheckBox.isChecked():
                #print('hrete')
               # self.core.limitVersions()

            if self.dockWidget.LI_SortLayerCheckbox.isChecked()  and not self.dockWidget.LI_AddSSGroupCheckbox.isChecked() :
                print('Preparing to sort')
                self.dockWidget.label_2.setText('Sorting Layers')
                self.setProgressBarBusy()
                self.core.runOrderLayers()
                self.dockWidget.label_2.setText('Sorting Complete')
                self.setProgressBarComplete()

            if self.dockWidget.LI_AddSSGroupCheckbox.isChecked():
                self.core.runHandleSS()
                if self.dockWidget.LI_SortLayerCheckbox.isChecked():
                    self.core.runOrderLayers()

            if self.dockWidget.LI_collapseSSCheckBox.isChecked():
                self.core.SSGroupSetExpanded(False)

            if self.dockWidget.LI_expandSSCheckBox.isChecked():
                self.core.SSGroupSetExpanded(True)
                 
             
             
        elif self.dockWidget.radioButton_2.isChecked():
            #self.core.importExistingLayers()
            #LayerImporterCore.runMain()
            print('running limit versions')
            self.core.limitVersions()
            
            
        else:
            print('button not checked')

    def runUpdate(self):
        if self.dockWidget.LI_LimitVersionsCheckBox.isChecked():
                 #print('hrete')
                 self.core.limitVersions()
            
        if self.dockWidget.LI_SortLayerCheckbox.isChecked() and not self.dockWidget.LI_AddSSGroupCheckbox.isChecked() :
                print('Preparing to sort')
                self.dockWidget.label_2.setText('Sorting Layers')
                self.setProgressBarBusy()
                self.core.runOrderLayers()
                self.dockWidget.label_2.setText('Sorting Complete')
                self.setProgressBarComplete()
            
        if self.dockWidget.LI_AddSSGroupCheckbox.isChecked():
            self.core.runHandleSS()
            if self.dockWidget.LI_SortLayerCheckbox.isChecked():
                self.core.runOrderLayers()
             
        if self.dockWidget.LI_collapseSSCheckBox.isChecked():
            self.core.SSGroupSetExpanded(False)
                 
        if self.dockWidget.LI_expandSSCheckBox.isChecked():
            self.core.SSGroupSetExpanded(True)

    def clearLogBox(self):
        self.dockWidget.plainTextEdit.clear()

    def getDockWidget(self):
        return self.dockWidget

    def handleSSCollapseCheckBox(self):
        #print('here1')
        if  self.dockWidget.LI_collapseSSCheckBox.isChecked():
             #print('here2')
             self.dockWidget.LI_expandSSCheckBox.setChecked(False)
             
    def handleSSExpandCheckBox(self):
        if  self.dockWidget.LI_expandSSCheckBox.isChecked():
             #print('here2')
             self.dockWidget.LI_collapseSSCheckBox.setChecked(False)   

    def enableDevMode(self): 
        print("Enabling Dev Mode")
        if self.dockWidget.LI_EnableDevPushButton.isChecked():
            self.dockWidget.tabWidget.setTabEnabled(2,True)
        else:
            self.dockWidget.tabWidget.setTabEnabled(2,False)    

    def initializeDirs(self):
        print("directory Initialised")
        project = QgsProject.instance()
        
        if QgsExpressionContextUtils.projectScope(project).variable('project_importpath') == None:
            self.showDialog()
            a=1
            
            #C:\\Users\\timc7\\Dropbox (Personal)\\Tim\\Employment\\WestWind Energy\\Work\\Projects\\GPWF\\GIS\\VectorData
            #P:\\P158_GPWF_GoldenPlainsWindFarm\\GIS_Maps\\VectorData
        else:
            
            self.vectorPath = QgsExpressionContextUtils.projectScope(project).variable('project_importpath')
            self.dockWidget.lineEdit.setText(self.vectorPath) 

    def showDialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)

        msg.setText("Vector data path has not been set")
        msg.setInformativeText("Please set the vector data path before running the import. This only has to be set once")
        msg.setWindowTitle("Path not Set")
        #msg.setDetailedText("The details are as follows:")
        #msg.addButton(QPushButton)
        msg.setStandardButtons(QMessageBox.Open)
        #msg.buttonClicked.connect(msgbtn)
        retval = msg.exec_()
        print ("value of pressed message box button:", retval )
        
        if (retval==8192):
            self.selectDir()

    def selectDir( self ):
        """ Open a dialog for the user to choose a starting directory """

        #self.showdialog()
        project = QgsProject.instance()
        if QgsExpressionContextUtils.projectScope(project).variable('project_importpath') == None:            
            self.vectorPath = QFileDialog.getExistingDirectory(self.dockWidget, 'Selectvector data path', '/home', QFileDialog.ShowDirsOnly)
            QgsExpressionContextUtils.setProjectVariable(project, 'project_importpath', self.vectorPath)
            self.dockWidget.lineEdit.setText(self.vectorPath)
         #C:\\Users\\timc7\\Dropbox (Personal)\\Tim\\Employment\\WestWind Energy\\Work\\Projects\\GPWF\\GIS\\VectorData
            #P:\\P158_GPWF_GoldenPlainsWindFarm\\GIS_Maps\\VectorData

        else:    
            originalVectorPath = QgsExpressionContextUtils.projectScope(project).variable('project_importpath')
            self.vectorPath=originalVectorPath
            self.vectorPath = QFileDialog.getExistingDirectory(self.dockWidget, 'Selectvector data path', self.vectorPath , QFileDialog.ShowDirsOnly)
            
            if (self.vectorPath and self.vectorPath is not None):
                self.dockWidget.lineEdit.setText(self.vectorPath)
                QgsExpressionContextUtils.setProjectVariable(project, 'project_importpath', self.vectorPath)
            else:
                self.dockWidget.lineEdit.setText(originalVectorPath)

    def storeSettings(self):
        s=QgsSettings()
        print("Storing Importer Settings")
        #ignoreFolders=self.dockWidget.ignoreFoldersTextEdit.toPlainText()
        #print(text)
        #stringList = text.split("\n")

        #ignoreFolders=self.dockWidget.ignoreFoldersTextEdit.toPlainText().split("\n")
        s.setValue("layerimporter/ignorefolders",self.dockWidget.ignoreFoldersTextEdit.toPlainText())
    
    def readSettings(self):
        s=QgsSettings()
        print("Reading Importer Settings")
        self.dockWidget.ignoreFoldersTextEdit.setText(s.value("layerimporter/ignorefolders","workingFiles\nmapworkingData"))

