from os import listdir
import os
from qgis.core import *
import re
from operator import itemgetter, attrgetter, methodcaller
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from .layer_importer_dockwidget import LayerImporterDockWidget
from .layer_importer_core import LayerImporterCore
from qgis.PyQt.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox
#from ply.lex import runmain


class LayerImporterGuiManager:
    
    def __init__(self):
        self.vectorPath = None
        self.dockWidget = LayerImporterDockWidget()
        self.dockWidget.radioButton.setChecked(True)
        self.dockWidget.pushButton.clicked.connect(self.runImport)
        self.initializeDir()
        self.core = LayerImporterCore(self.dockWidget,self.vectorPath)
        self.dockWidget.pushButton_2.clicked.connect(self.clearLogBox)
        self.dockWidget.checkBox_3.clicked.connect(self.handleSSCollapseCheckBox)
        self.dockWidget.checkBox_4.clicked.connect(self.handleSSExpandCheckBox)
        self.dockWidget.pushButton_3.clicked.connect(self.selectDir)
        self.dockWidget.checkBox_6.clicked.connect(self.enableDevMode)
        #self.dockWidget.checkBox_6.setChecked(True)
        self.dockWidget.pushButton_4.clicked.connect(self.featureTest)
        self.dockWidget.pushButton_5.clicked.connect(self.runUpdate)
        #self.dockWidget.pushButton_4.clicked.connect(self.showDialog)
        
        if self.dockWidget.tabWidget.currentIndex() !=0:
            self.dockWidget.tabWidget.setCurrentIndex(0)
        print(self.dockWidget.tabWidget.currentIndex())
        
        if self.dockWidget.checkBox_6.isChecked():
            self.dockWidget.tabWidget.setTabEnabled(2,True)
        else:
            self.dockWidget.tabWidget.setTabEnabled(2,False)
        
    def featureTest(self):
        
        self.core.runOrderLayers() 
        #self.core.runHandleSS()   
    
    def runImport(self):
        if self.vectorPath == None:
            self.showDialog()

        if self.dockWidget.radioButton.isChecked()==True:
             importList = self.core.getImportExistingLayersList()
            
             self.core.importExistingLayersList(importList)
             #self.core.runMain()
             if self.dockWidget.checkBox_5.isChecked():
                 #print('hrete')
                 self.core.limitVersions()
            
             if self.dockWidget.checkBox.isChecked() and not self.dockWidget.checkBox_2.isChecked() :
                 self.core.runOrderLayers()
            
             if self.dockWidget.checkBox_2.isChecked():
                 self.core.runHandleSS()
                 if self.dockWidget.checkBox.isChecked():
                     self.core.runOrderLayers()
             
             if self.dockWidget.checkBox_3.isChecked():
                 self.core.SSGroupSetExpanded(False)
                 
             if self.dockWidget.checkBox_4.isChecked():
                 self.core.SSGroupSetExpanded(True)
             
             
        elif self.dockWidget.radioButton_2.isChecked()==True:
            #self.core.importExistingLayers()
            #LayerImporterCore.runMain()
            print('running limit versions')
            self.core.limitVersions()
            
            
        else:
            print('button not checked')
    
    def runUpdate(self):
        if self.dockWidget.checkBox_5.isChecked():
                 #print('hrete')
                 self.core.limitVersions()
            
        if self.dockWidget.checkBox.isChecked() and not self.dockWidget.checkBox_2.isChecked() :
            self.core.runOrderLayers()
            
        if self.dockWidget.checkBox_2.isChecked():
            self.core.runHandleSS()
            if self.dockWidget.checkBox.isChecked():
                self.core.runOrderLayers()
             
        if self.dockWidget.checkBox_3.isChecked():
            self.core.SSGroupSetExpanded(False)
                 
        if self.dockWidget.checkBox_4.isChecked():
            self.core.SSGroupSetExpanded(True)
    
    def clearLogBox(self):
        self.dockWidget.plainTextEdit.clear()
    
    def getDockWidget(self):
        return self.dockWidget
    
    def handleSSCollapseCheckBox(self):
        #print('here1')
        if  self.dockWidget.checkBox_3.isChecked():
             #print('here2')
             self.dockWidget.checkBox_4.setChecked(False)
             
    def handleSSExpandCheckBox(self):        
        if  self.dockWidget.checkBox_4.isChecked():
             #print('here2')
             self.dockWidget.checkBox_3.setChecked(False)   

    def enableDevMode(self): 
        if self.dockWidget.checkBox_6.isChecked():
            self.dockWidget.tabWidget.setTabEnabled(2,True)
        else:
            self.dockWidget.tabWidget.setTabEnabled(2,False)    
        
     
    def initializeDir(self):
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
            self.vectorPath = QFileDialog.getExistingDirectory(self.dockWidget,'Selectvector data path','/home',QFileDialog.ShowDirsOnly)
            QgsExpressionContextUtils.setProjectVariable(project,'project_importpath',self.vectorPath)
            self.dockWidget.lineEdit.setText(self.vectorPath)
         #C:\\Users\\timc7\\Dropbox (Personal)\\Tim\\Employment\\WestWind Energy\\Work\\Projects\\GPWF\\GIS\\VectorData
            #P:\\P158_GPWF_GoldenPlainsWindFarm\\GIS_Maps\\VectorData

        else:    
            self.vectorPath = QgsExpressionContextUtils.projectScope(project).variable('project_importpath')
            self.vectorPath = QFileDialog.getExistingDirectory(self.dockWidget,'Selectvector data path',self.vectorPath ,QFileDialog.ShowDirsOnly)
            QgsExpressionContextUtils.setProjectVariable(project,'project_importpath',self.vectorPath)
            self.dockWidget.lineEdit.setText(self.vectorPath)
   
 