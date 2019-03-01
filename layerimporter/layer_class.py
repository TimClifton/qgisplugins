from os import listdir
import os
from qgis.core import *
import re
from operator import itemgetter, attrgetter, methodcaller
from .layer_importer_dockwidget import LayerImporterDockWidget
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
import datetime

#from ply.lex import runmain


class layerInfo:

    def __init__(self,_layerObject, _name ):
        
        self.layerObject = _layerObject
        self.parentTree = self.getLayerParents(self.layerObject)
        self.shortName = self.layerObject.name()
        
        regA = re.compile('(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*)')
        result=regA.match(self.shortName)
        if (result!= None):
            self.version = 'v'+result.group('majorversion')+'-'+result.group('minorversion')
            self.versionNum=int(result.group('majorversion')+result.group('minorversion'))
            self.disciplineName = result.group('name')
            self.additionalInfo = result.group('suffix')
        else:
            self.version = ''
            self.versionNum=0
            self.disciplineName = ''
            self.additionalInfo = ''
        
        #self.path = _path
        
    
    
    
    def getLayerParents(self, layer):
         layerTree = []
         node=layer
         while node.parent()!=None:
            layerTree.append(node.name())
            node=node.parent()
            
         return layerTree
     
    def setLayerStyle (self,_style):
        self.layerStyle = _style
    
    
class layerFileInfo:
    
    def __init__(self, _path, _fullName ):
        
        self.path = _path
        self.fullName = _fullName
        self.shortName = os.path.splitext(self.fullName)[0]
        self.ext = os.path.splitext(self.fullName)[1]
        
        regA = re.compile('(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*).shp\Z')
        result=regA.match(self.fullName)
        self.version = 'v'+result.group('majorversion')+'-'+result.group('minorversion')
        self.versionNum=int(result.group('majorversion')+result.group('minorversion'))
        self.disciplineName = result.group('name')
        self.additionalInfo = result.group('suffix')
        """ The node that the layer is going to be added to """
        self.layerGroup = None 
        
        
    def setlayerGroup(self,_group):
        self.layerGroup = _group    
        
        
    def setLayerStyle (self,_style):
        self.layerStyle = _style
        
        
        
        
        
        
        