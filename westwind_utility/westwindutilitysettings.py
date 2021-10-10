from qgis.core import *
import os
import configparser
import ntpath
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import re
from itertools import chain
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import datetime
import time
import random
import multiprocessing
import pathlib
import yaml
import inspect
from distutils.util import strtobool




class WestWindUtilitySettings:

    def __init__(self,_dockWidget):

        print('loading settings')
        self.dockWidget = _dockWidget
        self.settingsFileDirectory = QgsApplication.qgisSettingsDirPath()
        print(self.settingsFileDirectory)
        #self.settingsFileDirectory = 'C:/Users/timc7/AppData/Roaming/QGIS/QGIS3\profiles\default/'
        self.settingsFileName = 'westwinduntilitysettings.ini'
        self.settingsFilePath = os.path.abspath(self.settingsFileDirectory + self.settingsFileName)
        self.settings = QSettings(self.settingsFilePath,QSettings.IniFormat)
        self.dockWidget.pushButton_5.clicked.connect(self.guisave)
        self.dockWidget.pushButton_9.clicked.connect(self.guirestore)
        self.guirestore()
        self.dockWidget.settings = self






    def guisave(self):

    # Save geometry
        self.settings.setValue('size', self.dockWidget.size())
        self.settings.setValue('pos', self.dockWidget.pos())

        for name, obj in inspect.getmembers(self.dockWidget):
        # if type(obj) is QComboBox:  # this works similar to isinstance, but missed some field... not sure why?
            if isinstance(obj, QComboBox):
                name = obj.objectName()  # get combobox name
                index = obj.currentIndex()  # get current index from combobox
                text = obj.itemText(index)  # get the text for current index
                self.settings.setValue(name, text)  # save combobox selection to registry

            if isinstance(obj, QLineEdit):
                name = obj.objectName()
                value = obj.text()
                self.settings.setValue(name, value)  # save ui values, so they can be restored next time

            if isinstance(obj, QCheckBox):
                name = obj.objectName()
                state = obj.isChecked()
                self.settings.setValue(name, state)

            if isinstance(obj, QRadioButton):
                name = obj.objectName()
                value = obj.isChecked()  # get stored value from registry
                self.settings.setValue(name, value)

            if isinstance(obj, QSpinBox):
                name  = obj.objectName()
                value = obj.value()             # get stored value from registry
                self.settings.setValue(name, value)

            if isinstance(obj, QSlider):
                name  = obj.objectName()
                value = obj.value()             # get stored value from registry
                self.settings.setValue(name, value)


    def guirestore(self):

    # Restore geometry  
        self.dockWidget.resize(self.settings.value('size', QSize(500, 500)))
        self.dockWidget.move(self.settings.value('pos', QPoint(60, 60)))

        for name, obj in inspect.getmembers(self.dockWidget):
            if isinstance(obj, QComboBox):
                index = obj.currentIndex()  # get current region from combobox
                # text   = obj.itemText(index)   # get the text for new selected index
                name = obj.objectName()

                value = (self.settings.value(name))

                if value == "":
                    continue

                index = obj.findText(value)  # get the corresponding index for specified string in combobox

                if index == -1:  # add to list if not found
                    obj.insertItems(0, [value])
                    index = obj.findText(value)
                    obj.setCurrentIndex(index)
                else:
                    obj.setCurrentIndex(index)  # preselect a combobox value by index

            if isinstance(obj, QLineEdit):
                name = obj.objectName()
                value = (self.settings.value(name))  # get stored value from registry
                obj.setText(value)  # restore lineEditFile

            if isinstance(obj, QCheckBox):
                name = obj.objectName()
                value = self.settings.value(name)  # get stored value from registry
                if value != None:

                    if isinstance(value, bool):
                        obj.setChecked(value)
                    else:
                        obj.setChecked(bool(strtobool(value)))  # restore checkbox
                    #obj.setChecked(value)

            if isinstance(obj, QRadioButton):
                name = obj.objectName()
                value = self.settings.value(name)  # get stored value from registry
                if value != None:

                    if isinstance(value, bool):
                        obj.setChecked(value)
                    else:
                    #obj.setChecked(strtobool(value))
                        obj.setChecked(bool(strtobool(value)))
                    
                    
            if isinstance(obj, QSlider):
                name = obj.objectName()
                value = self.settings.value(name)    # get stored value from registry
                if value != None:           
                    obj. setValue(int(value))   # restore value from registry

            if isinstance(obj, QSpinBox):
                name = obj.objectName()
                value = self.settings.value(name)    # get stored value from registry
                if value != None:
                    obj. setValue(int(value))   # restore value from registry

            



    def loadSettings(self):

        if os.path.exists(self.settingsFilePath):

            self.createDefaultSettings()


    def createDefaultSettings(self):
        print('making config')
        config = configparser.ConfigParser()
        config['Default'] = {'ServerAliveInterval': '45','Compression': 'yes','CompressionLevel': '9'}
        print(config)
        config['bitbucket.org'] = {}
        config['bitbucket.org']['User'] = 'hg'
        config['topsecret.server.com'] = {}
        topsecret = config['topsecret.server.com']
        topsecret['Port'] = '50022'     # mutates the parser
        topsecret['ForwardX11'] = 'no'  # same here
        config['Default']['ForwardX11'] = 'yes'


        config


        with open(self.settingsFilePath, 'w') as configfile:
            config.write(configfile)

        print('fin')