from os import listdir
import os
from qgis.core import *
import re
from operator import itemgetter, attrgetter, methodcaller
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
import datetime
from .helperclasses.layer_class import *
import time
from qgis.PyQt.QtWidgets import QApplication, QMessageBox


class ImporterCore:

    def __init__(self, dockWidget, _vectorPath):
        print("Initialising the Importer Core")
        self.dockWidget = dockWidget
        self.removeLayerList = []
        self.vectorPath = _vectorPath

    def infoExtractor(layer):
        reg = re.compile('(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*)')
        result = reg.match(layer.name())
        splitName = layer.name().split("_")

        if result !=None:
            version = 'v'+result.group('majorversion')+'-'+result.group('minorversion')
            cleanName =  result.group('name')
            versionNum = int(result.group('majorversion')+result.group('minorversion'))
        else:
            version = ''
            cleanName = ''
            versionNum = 0

        return [('layer', layer), ('cleanName', cleanName), ('version', version), ('fullName', layer.name()), ('versionNum', versionNum)]

    def getLatestVersion(self, layerList):
        latestVersion = 0
        for layer in layerList:
            newLayerObject = layerInfo(layer, layer.name())
            if newLayerObject.versionNum > latestVersion:
                latestVersion = newLayerObject.versionNum
        return latestVersion

    def handleSS(self, group):
        subGroupCount = 0
        containsSS = False
        layerCount = 0

        for child in group.children():
            if child.nodeType() == QgsLayerTreeNode.NodeGroup:

                subGroupCount = subGroupCount+1
                if child.name() == 'SS':
                    containsSS = True
            if child.nodeType() == QgsLayerTreeNode.NodeLayer:
                layerCount= layerCount + 1

        if subGroupCount < 1 and containsSS == False and layerCount > 1:
            print('adding group')
            group.addGroup('SS')
            self.handleSS(group)
        if containsSS == True and subGroupCount < 2:
            layers = group.findLayers()
            groupSS = group.findGroup('SS')
            latestVersion = self.getLatestVersion(layers)

            for layer in layers:
                newLayerObject = layerInfo(layer, layer.name())

                layerVersion = newLayerObject.versionNum
                #print('Latest version is %s' %layerVersion)
                if layerVersion < int(latestVersion) and self.checkForVersion(layer.name()) != None:

                    clone = layer.clone()
                    groupSS.insertChildNode(0, clone)
                    layer.parent().removeChildNode(layer)

                #print('current version is %s and latest version is %s' %(latestVersion,layerVersion))
                if layerVersion == latestVersion:
                    #check if latest version is in the SS group
                    #print('latest and current version are equal')
                    if layer.parent().name() == 'SS':
                        print('latest version in ss')
                        clone = layer.clone()
                        group.insertChildNode(0 ,clone)
                        layer.parent().removeChildNode(layer)

    def getVersionNum(string):
        p = re.compile(r'\d+')
        num = p.findall(string)
        versionNum = ''.join(num)
        #print(version)
        return versionNum

    def orderLayers(self, layerList):
        root = QgsProject.instance().layerTreeRoot()
        for layer in layerList:
            layerObject = layer.layerObject
            clone = layerObject.clone()
            layerObject.parent().insertChildNode(0, clone)
            layerObject.parent().removeChildNode(layerObject)

    def getOrderedLayers_list(self, layerList):
        #sortedList = layerList.sort(key=lambda x: x.versionNum, reverse=False)
        sortedList = sorted(layerList,key=lambda x: x.versionNum, reverse=False)
        return sortedList

    def setLoadPath (self):
        project = QgsProject.instance()
        if QgsExpressionContextUtils.projectScope(project).variable('project_importpath') == None:
            QgsExpressionContextUtils.setProjectVariable(project,
            'project_importpath','C:\\Users\\timc7\\Dropbox (Personal)\\Tim\\Employment\\WestWind Energy\\Work\\Projects\\GPWF\\GIS\\VectorData')
            #C:\\Users\\timc7\\Dropbox (Personal)\\Tim\\Employment\\WestWind Energy\\Work\\Projects\\GPWF\\GIS\\VectorData
            #P:\\P158_GPWF_GoldenPlainsWindFarm\\GIS_Maps\\VectorData
        path = QgsExpressionContextUtils.projectScope(project).variable('project_importpath')
        self.vectorPath = self.dockWidget.lineEdit.text()

        return self.vectorPath

    def runMain(self):
        root = QgsProject.instance().layerTreeRoot()
        groups = root.findGroups()
        layers = root.findLayers()
        orderedLayers = LayerImporterCore.getOrderedLayers_list(layers)
        LayerImporterCore.orderLayers(orderedLayers)

        for group in groups:
            LayerImporterCore.exploreGroup(group)

    def runHandleSS(self):
        def exploreGroup(group):
            subgroupcount = 0
            for node in group.children():
                subgroupcount = 0
                if node.nodeType() == QgsLayerTreeNode.NodeGroup:
                    if node.name() != 'SS':
                        self.handleSS(node)
                        exploreGroup(node)

            if subgroupcount < 2:
                self.handleSS(group)

        root = QgsProject.instance().layerTreeRoot()
        groups = root.findGroups()

        for group in groups:
            exploreGroup(group)

    def runOrderLayers(self):

        def exploreGroup(group):
             #check if the group contains any subgroups
            layersList = []
            subgroupcount = 0
            for node in group.children():
                #print(node.nodeType())
                subgroupcount = 0
                if node.nodeType()==QgsLayerTreeNode.NodeGroup:
                    exploreGroup(node)
                if node.nodeType() == QgsLayerTreeNode.NodeLayer:
                    if self.checkForVersion(node.name()):
                        print(node.layerId())
                        newLayerObject = layerInfo(node, node.name())
                        layersList.append(newLayerObject)

            orderedLayers = self.getOrderedLayers_list(layersList)
            layersList.reverse()

            unorderedLayerIds= [layer.layerObject.layerId() for layer in layersList]
            orderedLayerIds = [layer.layerObject.layerId() for layer in orderedLayers]

            unorderedLayerNames = [layer.shortName for layer in layersList]
            orderedLayerNames=[layer.shortName for layer in orderedLayers]

            if orderedLayerNames == unorderedLayerNames:
                print('Group is already sorted')     
            else:
                print('Sorting List')
                self.orderLayers(orderedLayers)
                


        root = QgsProject.instance().layerTreeRoot()
        children = root.children()
        groups = root.findGroups()
        rootLayers = []


        for node in children:
            if node.nodeType() == QgsLayerTreeNode.NodeLayer:
                if self.checkForVersion(node.name()):
                    newLayerObject = layerInfo(node, node.name())
                    rootLayers.append(newLayerObject)

        orderedLayers = self.getOrderedLayers_list(rootLayers)
        self.orderLayers(orderedLayers)

        for group in groups:
            exploreGroup(group)

    def displayLogText(self, stringList):
        for string in stringList:
            self.dockWidget.plainTextEdit. appendPlainText(string)

    def limitVersionsSearchGroups(self, group):
        versionLimit = self.dockWidget.spinBox.value()
        #removeLayerList = _removeLayerList
        layersInGroup = []
        print(group.name())

        for node in group.children():
        #print(node.nodeType())
            containsSS = False
            subgroupcount = 0
            #print(node.name())
            if node.nodeType() == QgsLayerTreeNode.NodeGroup:   
                #print(node.name())
                subgroupcount = subgroupcount + 1
                if (node.name() != 'SS'):
                    self.limitVersionsSearchGroups(node)

                if (node.name() == 'SS'):
                    containsSS = True


            if node.nodeType() == QgsLayerTreeNode.NodeLayer:
                if self.checkForVersion(node.name()):
                    newLayerObject = layerInfo(node ,node.name())
                    layersInGroup.append(newLayerObject)
                #print(len(layersInGroup))
            if subgroupcount < 2 and containsSS == True:
                #print('Subgroup count is %s Contains SS is %s Node name is %s' %(str(subgroupcount),containsSS, node.name()))
                groupSS = group.findGroup('SS')        
                #print (groupSS.name())
                for layer in groupSS.findLayers():
                    newLayerObject = layerInfo(layer, node.name())
                    layersInGroup.append(newLayerObject)
                #print('here')

        #for layer in layersInGroup:
        layersInGroup.sort(key=lambda x: x.versionNum, reverse=True)
         #sortedLayerTuples.sort(key=itemgetter(4),reverse=True) 

                
        if len(layersInGroup)>versionLimit:
            toAdd = layersInGroup[versionLimit:]
            
            for layer in toAdd:
                self.removeLayerList.append(layer)
                    #print(toAdd)

    def SSGroupSetExpanded(self, _expand):
        def helper(_group, _expand):
            for node in _group.children():

                if node.nodeType() == QgsLayerTreeNode.NodeGroup:

                    if (node.name() == 'SS'):
                       node.setExpanded(_expand)
                       #print ('Found SS')


                    helper(node, _expand)
        root = QgsProject.instance().layerTreeRoot()
        groups = root.findGroups()

        for group in groups:
            #print ('checking for ss expanded %s' %group.name())

            if group.name() == 'SS':
                group.setExpanded(_expand)

            helper(group, _expand)

    def checkForVersion(self, name):
        regA = re.compile('(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*)')
        result= regA.match(name)
        # if result:
        #     print(result)
        return result

    def limitVersions(self):
        root = QgsProject.instance().layerTreeRoot()
        groups = root.findGroups()
        self.removeLayerList = []
        logText = []
        for group in groups:
            self.limitVersionsSearchGroups(group)

        for layer in self.removeLayerList:
            layer.layerObject.parent().removeChildNode(layer.layerObject)
            logText.append('')

    def getImportExistingLayersList(self,_ignoreFolders,limitVersion=False):
        self.dockWidget.label_2.setText('Getting layer list to import')

        self.dockWidget.progressBar.reset()
        self.dockWidget.progressBar.setMinimum(0)
        self.dockWidget.progressBar.setMaximum(0) # ProgressBar in busy mode
        importLayerList = []
        existingLayerList = []
        root = QgsProject.instance().layerTreeRoot()
        vectorDataPath = self.setLoadPath()
        walkData = os.walk(vectorDataPath, topdown=True)

        for layer in root.findLayers():
            if self.checkForVersion(layer.name()) != None:
                newLayerObject = layerInfo(layer, layer.name())
                existingLayerList.append(newLayerObject)

        


        #existingLayers = root.findLayers()
        latestVersionDic = {}

        for roots, dirs, files in walkData:

            dirs[:] = [d for d in dirs if d not in _ignoreFolders]
            count = 0

            for file in files:

                #reg = re.compile('\S*[vV]\d{2}-\d{2}\S*.(?=shp)')
                #reg = re.compile('(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*).shp\Z')

                if self.dockWidget.LI_ImportWorkingLayers.isChecked():
                    reg = re.compile('(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*)(\s(W||w)orking)?.shp\Z')
                
                else:
                    reg = re.compile('(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*).shp\Z')


                if reg.match(file):
                    #print(file)
                    TLayerFileInfo = layerFileInfo(roots+"\\"+file, file)
                    exactLayerExists = False
                    partNameFound = False
                    layerGroup = None

                    for layer in existingLayerList:
                        if layer.shortName == TLayerFileInfo.shortName:
                            exactLayerExists = True

                        if layer.disciplineName == TLayerFileInfo.disciplineName:

                            partNameFound = True
                            layerGroup = layer.layerObject.parent()

                            if layerGroup.name() == 'SS':
                                layerGroup = layerGroup.parent()

                    if exactLayerExists == False and partNameFound == True:
                        #print("exactLayerExists is %s and partNameFound is %s" %(exactLayerExists, partNameFound))
                        #print(TLayerFileInfo.path)
                        #copy the style of the previous latest layer
                        self.copyLatestLayerStyle(existingLayerList, TLayerFileInfo)
                        TLayerFileInfo.setlayerGroup(layerGroup)

                        if limitVersion:
                            print(f'Dictionary is {latestVersionDic}')
                            if TLayerFileInfo.disciplineName not in latestVersionDic:

                                print(f'Creating new dictionary item {TLayerFileInfo.disciplineName}. The current keys name is {TLayerFileInfo.disciplineName}')

                                latestVersionDic= {TLayerFileInfo.disciplineName:[TLayerFileInfo]}
                                print(f'The dictionary is now {latestVersionDic}')

                            else:
                                existingList = latestVersionDic[TLayerFileInfo.disciplineName]
                                print(f'Existing list is {existingList}')

                                print(f'The file infor is {TLayerFileInfo}')

                                appendedList = existingList + [TLayerFileInfo]

                                print(f'The appended list is now {appendedList}')

                                latestVersionDic[TLayerFileInfo.disciplineName]=appendedList

                                print(f'The diction was added to and is now {latestVersionDic}')


                        importLayerList.append(TLayerFileInfo)

        if limitVersion:

            importLayerList_=[]

            for key in latestVersionDic:
                layers = latestVersionDic[key]

                layers.sort(key=lambda x: x.versionNum,reverse=True)

                importLayerList_=importLayerList_+layers[:3]

            importLayerList=importLayerList_

        print(f'Import layer List is {importLayerList}')
        self.dockWidget.label_2.setText('Layer list retrieved!')

        return importLayerList

    def importExistingLayersList(self, layerObjectList):

        logText = []
        logText.append(str('Import executed %s') % datetime.datetime.now())
        self.dockWidget.label_2.setText('Beginning layer import')
        self.dockWidget.progressBar.reset()
        self.dockWidget.progressBar.setMinimum(0)
        self.dockWidget.progressBar.setMaximum(len(layerObjectList))
        QApplication.processEvents()
        treeRoot = QgsProject.instance().layerTreeRoot()

        step = 0

        for layerObject in layerObjectList:

            vectorLayer = QgsVectorLayer(layerObject.path, layerObject.shortName)
            QgsProject.instance().addMapLayer(vectorLayer)
            print('vector layer is %s. short Name is %s' %(vectorLayer.name(),layerObject.path))
            insertedLayer = treeRoot.findLayer(vectorLayer.id())
            clone = insertedLayer.clone()
            if layerObject.layerStyle is not None:
                layerObject.layerStyle.writeToLayer(clone.layer())
            layerObject.layerGroup.insertChildNode(0,clone)
                        #TODO add check to remove layer if parent is Null
            insertedLayer.parent().removeChildNode(insertedLayer)
            step = step + 1
            self.dockWidget.progressBar.setValue(step)
            logText.append(clone.name())

        if len(layerObjectList) < 1:
            logText.append('No new layers were added!')
            self.dockWidget.progressBar.setMinimum(0)
            self.dockWidget.progressBar.setMaximum(1)
            self.dockWidget.progressBar.setValue(1)
            self.dockWidget.label_2.setText('No new layers imported!')
        else:

            self.dockWidget.label_2.setText('Layers imported!')

        self.displayLogText(logText)

    def copyLatestLayerStyle(self,existingLayers, newLayer):
        matchedLayers=[]
        latestVersion =0
        latestVersionLayer = None
        #print('Here50')
        for layer in existingLayers:

            if layer.disciplineName == newLayer.disciplineName and layer.additionalInfo == newLayer.additionalInfo:
                matchedLayers.append(layer)

        for _layer in matchedLayers:
            if _layer.versionNum>latestVersion:
                latestVersion=_layer.versionNum
                latestVersionLayer = _layer
        newLayerStyle = QgsMapLayerStyle()

        #print(latestVersionLayer.layerObject)
        #print('checking lastest version layer style')
        if latestVersionLayer !=None:
            #print('Testing')
            #print(latestVersionLayer)
            newLayerStyle.readFromLayer(latestVersionLayer.layerObject.layer())
        if newLayerStyle.isValid():
            #print('Style is valid and good to go')
            newLayer.setLayerStyle(newLayerStyle)
