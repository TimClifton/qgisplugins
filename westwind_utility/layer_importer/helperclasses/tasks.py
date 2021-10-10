import random
from time import sleep
import datetime
from PyQt5.QtCore import QEvent, Qt, pyqtSignal
from qgis.core import QgsExpressionContextUtils
from itertools import chain
import os
import re
from .layer_class import layerInfo, layerFileInfo
from qgis.core import (QgsApplication, QgsTask, QgsMessageLog, Qgis,
                       QgsVectorLayer, QgsProject, QgsLayerTreeNode, QgsMapLayerStyle)
import ntpath
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import sys


MESSAGE_CATEGORY = 'Layer Importer'


class runOrderLayerTask(QgsTask):
    myObjectsSignal = pyqtSignal(object, object)
    """This shows how to subclass QgsTask"""

    def __init__(self, description):
        super().__init__(description, QgsTask.CanCancel)

        self.total = 0
        self.iterations = 0
        self.exception = None
        # self.specialValue=0
        # self.source=_source
        #self.list = ["value 1","value 2", "value 3"]

    def run(self):

        root = QgsProject.instance().layerTreeRoot()
        children = root.children()
        groups = root.findGroups()
        rootLayers = []

        for node in children:
            QgsMessageLog.logMessage(
                f'Here 1 node type is {node.nodeType()} {QgsLayerTreeNode.NodeLayer}', MESSAGE_CATEGORY, Qgis.Info)
            if node.nodeType() == QgsLayerTreeNode.NodeLayer:
                QgsMessageLog.logMessage(
                    f'Here 2', MESSAGE_CATEGORY, Qgis.Info)
                if self.checkForVersion(node.name()):
                    QgsMessageLog.logMessage(
                        f'Here 3', MESSAGE_CATEGORY, Qgis.Info)
                    newLayerObject = layerInfo(node, node.name())
                    rootLayers.append(newLayerObject)

        orderedLayers = self.getOrderedLayers_list(rootLayers)
        self.orderLayers(orderedLayers)

        for group in groups:
            if self.isCanceled():
                return False
            QgsMessageLog.logMessage(f'Here 5', MESSAGE_CATEGORY, Qgis.Info)
            self.exploreGroup(group)

        QgsMessageLog.logMessage(f'Here 4', MESSAGE_CATEGORY, Qgis.Info)
        # self.exception=sys.exc_info()[0]
        #QgsMessageLog.logMessage(f'{sys.exc_info()}', MESSAGE_CATEGORY, Qgis.Info)
        return True

        # self.taskCompleted.emit()

    def getOrderedLayers_list(self, layerList):
        #sortedList = layerList.sort(key=lambda x: x.versionNum, reverse=False)
        sortedList = sorted(
            layerList, key=lambda x: x.versionNum, reverse=False)
        return sortedList

    def exploreGroup(self, group):

        # check if the group contains any subgroups
        QgsMessageLog.logMessage(
            f'Exploring Group', MESSAGE_CATEGORY, Qgis.Info)
        layersList = []
        subgroupcount = 0
        for node in group.children():
            QgsMessageLog.logMessage(
                f'Exploring Group 1', MESSAGE_CATEGORY, Qgis.Info)
            # print(node.nodeType())
            subgroupcount = 0
            if node.nodeType() == QgsLayerTreeNode.NodeGroup:
                self.exploreGroup(node)
            if node.nodeType() == QgsLayerTreeNode.NodeLayer:
                if self.checkForVersion(node.name()):
                    # print(node.layerId())
                    newLayerObject = layerInfo(node, node.name())
                    layersList.append(newLayerObject)
        QgsMessageLog.logMessage(f'Exploring Group 2',
                                 MESSAGE_CATEGORY, Qgis.Info)
        orderedLayers = self.getOrderedLayers_list(layersList)
        layersList.reverse()

        unorderedLayerIds = [layer.layerObject.layerId()
                             for layer in layersList]
        orderedLayerIds = [layer.layerObject.layerId()
                           for layer in orderedLayers]

        unorderedLayerNames = [layer.shortName for layer in layersList]
        orderedLayerNames = [layer.shortName for layer in orderedLayers]

        if orderedLayerNames == unorderedLayerNames:
            print('Group is already sorted')
        else:
            print('Sorting List')
            self.orderLayers(orderedLayers)

    def orderLayers(self, layerList):
        root = QgsProject.instance().layerTreeRoot()
        for layer in layerList:
            sleep(.5)
            layerObject = layer.layerObject
            clone = layerObject.clone()
            self.myObjectsSignal.emit(layerObject, clone)
            #layerObject.parent().insertChildNode(0, clone)
            # layerObject.parent().removeChildNode(layerObject)

    def checkForVersion(self, name):
        regA = re.compile(
            '(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*)')
        result = regA.match(name)
        # if result:
        #     print(result)
        return result

    def finished(self, result):
        """
        This function is automatically called when the task has
        completed (successfully or not).
        You implement finished() to do whatever follow-up stuff
        should happen after the task is complete.
        finished is always called from the main thread, so it's safe
        to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """
        QgsMessageLog.logMessage(
            f'Running finished', MESSAGE_CATEGORY, Qgis.Info)
        if result:
            QgsMessageLog.logMessage(
                'Task "{name}" completed\n'
                'Total: {total} (with {iterations} '
                'iterations)'.format(
                    name=self.description(),
                    total=self.total,
                    iterations=self.iterations),
                MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Task "{name}" not successful but without '
                    'exception (probably the task was manually '
                    'canceled by the user)'.format(
                        name=self.description()),
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(
                    'Task "{name}" Exception: {exception}'.format(
                        name=self.description(),
                        exception=self.exception),
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage(
            'Task "{name}" was canceled'.format(
                name=self.description()),
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

    def getSpecialValue(self):
        return self.specialValue


class getImportExistingLayersListTask(QgsTask):

    ImportLayerList = pyqtSignal(list)
    updateLabel = pyqtSignal(str)
    """This shows how to subclass QgsTask"""

    def __init__(self, description, _dockWidget):
        super().__init__(description, QgsTask.CanCancel)
        self.dockWidget = _dockWidget
        self.total = 0
        self.iterations = 0
        self.exception = None
        self.totalFiles = 0
        # self.specialValue=0
        # self.source=_source
        #self.list = ["value 1","value 2", "value 3"]
        #     def run(self):
        QgsMessageLog.logMessage(
            f'Running get Import Existing Layer List Task', MESSAGE_CATEGORY, Qgis.Info)
        self.importLayerList = []
        existingLayerList = []
        root = QgsProject.instance().layerTreeRoot()
        QgsMessageLog.logMessage(f'Here 0', MESSAGE_CATEGORY, Qgis.Info)
        path = self.setLoadPath()
        vectorDataPath = [path]

        ignoreFolders = self.dockWidget.ignoreFoldersTextEdit.toPlainText().split("\n")

        self.totalFiles = sum([len(files) for r, d, files in chain.from_iterable(
            os.walk(path) for path in vectorDataPath)])

        QgsMessageLog.logMessage(
            f'{vectorDataPath}', MESSAGE_CATEGORY, Qgis.Info)
        #walkData = os.walk(vectorDataPath, topdown=True)
        QgsMessageLog.logMessage(
            f'Here 2 {self.totalFiles}', MESSAGE_CATEGORY, Qgis.Info)

        stepRatio = 100

        if self.totalFiles < 40000:
            stepRatio = self.translate(self.totalFiles, 0, 40000, .001, 50)

        QgsMessageLog.logMessage(f'Here 44 ', MESSAGE_CATEGORY, Qgis.Info)

        step = self.totalFiles//stepRatio

        self.progressCount = 0

        for layer in root.findLayers():

            if self.checkForVersion(layer.name()) != None:
                newLayerObject = layerInfo(layer, layer.name())
                existingLayerList.append(newLayerObject)

        #QgsMessageLog.logMessage(f'Here 30', MESSAGE_CATEGORY, Qgis.Info)
        existingLayers = root.findLayers()
        QgsMessageLog.logMessage(f'Here 4 ', MESSAGE_CATEGORY, Qgis.Info)
        for roots, dirs, files in chain.from_iterable(os.walk(path) for path in vectorDataPath):

            QgsMessageLog.logMessage(f'Here 5', MESSAGE_CATEGORY, Qgis.Info)
            dirs[:] = [d for d in dirs if d not in ignoreFolders]

            for file in files:
                # sleep(.1)
                if self.isCanceled():
                    return False
                self.progressCount = self.progressCount + 1

                #self.updateLabel.emit(f"Checking file. total files {self.totalFiles}. step {step} progress {self.progressCount} value {self.progressCount % step}")
                if step == 0 or self.progressCount % step == 0:
                    QgsMessageLog.logMessage(
                        f'updating label', MESSAGE_CATEGORY, Qgis.Info)
                    self.updateLabel.emit(
                        f"Checking file {self.progressCount}")
                    self.setProgress(
                        int(100*self.progressCount/self.totalFiles))

                reg = re.compile(
                    '(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*).shp\Z')
                if reg.match(file):
                    TLayerFileInfo = layerFileInfo(roots+"\\"+file, file)
                    exactLayerExists = False
                    partNameFound = False
                    layerGroup = None
                    QgsMessageLog.logMessage(
                        f'getting list 1 ', MESSAGE_CATEGORY, Qgis.Info)
                    for layer in existingLayerList:
                        if layer.shortName == TLayerFileInfo.shortName:
                            exactLayerExists = True

                        if layer.disciplineName == TLayerFileInfo.disciplineName:

                            partNameFound = True
                            layerGroup = layer.layerObject.parent()

                            if layerGroup.name() == 'SS':
                                layerGroup = layerGroup.parent()

                    if exactLayerExists == False and partNameFound == True:

                        # copy the style of the previous latest layer
                        QgsMessageLog.logMessage(
                            f'Copying Layer', MESSAGE_CATEGORY, Qgis.Info)
                        self.copyLatestLayerStyle(
                            existingLayerList, TLayerFileInfo)
                        QgsMessageLog.logMessage(
                            f'Copying Layer complete', MESSAGE_CATEGORY, Qgis.Info)
                        TLayerFileInfo.setlayerGroup(layerGroup)
                        self.importLayerList.append(TLayerFileInfo)

        self.updateLabel.emit('Import list retrieved!')
        QgsMessageLog.logMessage(
            f'Emitting Complete Signal', MESSAGE_CATEGORY, Qgis.Info)
        self.ImportLayerList.emit(self.importLayerList)
        return True

    def finished(self, result):
        """
        This function is automatically called when the task has
        completed (successfully or not).
        You implement finished() to do whatever follow-up stuff
        should happen after the task is complete.
        finished is always called from the main thread, so it's safe
        to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """
        QgsMessageLog.logMessage(
            f'Running finished', MESSAGE_CATEGORY, Qgis.Info)
        if result:

            QgsMessageLog.logMessage(
                'Task "{name}" completed\n'
                'Total: {total} (with {iterations} '
                'iterations)'.format(
                    name=self.description(),
                    total=self.total,
                    iterations=self.iterations),
                MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Task "{name}" not successful but without '
                    'exception (probably the task was manually '
                    'canceled by the user)'.format(
                        name=self.description()),
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(
                    'Task "{name}" Exception: {exception}'.format(
                        name=self.description(),
                        exception=self.exception),
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage(
            'Task "{name}" was canceled'.format(
                name=self.description()),
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

    def setLoadPath(self):
        project = QgsProject.instance()

        if QgsExpressionContextUtils.projectScope(project).variable('project_importpath') == None:
            QgsExpressionContextUtils.setProjectVariable(project,
                                                         'project_importpath', 'C:\\Users\\timc7\\Dropbox (Personal)\\Tim\\Employment\\WestWind Energy\\Work\\Projects\\GPWF\\GIS\\VectorData')
            # C:\\Users\\timc7\\Dropbox (Personal)\\Tim\\Employment\\WestWind Energy\\Work\\Projects\\GPWF\\GIS\\VectorData
            # P:\\P158_GPWF_GoldenPlainsWindFarm\\GIS_Maps\\VectorData

        path = QgsExpressionContextUtils.projectScope(
            project).variable('project_importpath')
        QgsMessageLog.logMessage(
            f'SetLoadpath 11 ', MESSAGE_CATEGORY, Qgis.Info)
        vectorPath = self.dockWidget.lineEdit.text()
        QgsMessageLog.logMessage(
            f'SetLoadpath 12 ', MESSAGE_CATEGORY, Qgis.Info)
        return vectorPath

    def checkForVersion(self, name):
        regA = re.compile(
            '(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*)')
        result = regA.match(name)
        # if result:
        #     print(result)
        return result

    def copyLatestLayerStyle(self, existingLayers, newLayer):
        matchedLayers = []
        latestVersion = 0
        latestVersionLayer = None
        #QgsMessageLog.logMessage(f'Copying Layer styles', MESSAGE_CATEGORY, Qgis.Info)
        for layer in existingLayers:

            if layer.disciplineName == newLayer.disciplineName and layer.additionalInfo == newLayer.additionalInfo:
                matchedLayers.append(layer)

        if not matchedLayers:
            #QgsMessageLog.logMessage(f'matched layers found', MESSAGE_CATEGORY, Qgis.Info)
            return
        for _layer in matchedLayers:
            QgsMessageLog.logMessage(
                f'Copying Layer styles 3 {_layer.versionNum}', MESSAGE_CATEGORY, Qgis.Info)
            if _layer.versionNum > latestVersion:
                latestVersion = _layer.versionNum
                latestVersionLayer = _layer
                #QgsMessageLog.logMessage(f'Latest Layer found', MESSAGE_CATEGORY, Qgis.Info)

        newLayerStyle = QgsMapLayerStyle()
        #QgsMessageLog.logMessage(f'Layer Style Check', MESSAGE_CATEGORY, Qgis.Info)

        if latestVersionLayer != None:

            newLayerStyle.readFromLayer(latestVersionLayer.layerObject.layer())

        if newLayerStyle.isValid():

            newLayer.setLayerStyle(newLayerStyle)

    def translate(self, value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)


class importExistingLayersListTask(QgsTask):
    addLayerToProject = pyqtSignal(object)
    updateLabel = pyqtSignal(str)
    updateLogText = pyqtSignal(list)
    """This shows how to subclass QgsTask"""

    def __init__(self, description, _layerObjectList, _dockWidget):
        super().__init__(description, QgsTask.CanCancel)
        self.dockWidget = _dockWidget
        self.total = 0
        self.iterations = 0
        self.exception = None
        self.layerObjectList = _layerObjectList
        # self.specialValue=0
        # self.source=_source
        #self.list = ["value 1","value 2", "value 3"]

    def run(self):
        QgsMessageLog.logMessage(
            f'Starting to import layers', MESSAGE_CATEGORY, Qgis.Info)
        self.logText = []
        QgsMessageLog.logMessage(f'Here A', MESSAGE_CATEGORY, Qgis.Info)
        self.logText.append(str('Import executed %s') %
                            datetime.datetime.now())
        QgsMessageLog.logMessage(f'Here B', MESSAGE_CATEGORY, Qgis.Info)

        QgsMessageLog.logMessage(f'Here z', MESSAGE_CATEGORY, Qgis.Info)
        step = 1
        QgsMessageLog.logMessage(f'Here z', MESSAGE_CATEGORY, Qgis.Info)
        self.progressCount = 0
        QgsMessageLog.logMessage(
            f'Here z {len(self.layerObjectList)}', MESSAGE_CATEGORY, Qgis.Info)
        if self.isCanceled():
            QgsMessageLog.logMessage(f'cANCELLED', MESSAGE_CATEGORY, Qgis.Info)
            return False
        QgsMessageLog.logMessage(f'Here z', MESSAGE_CATEGORY, Qgis.Info)
        if len(self.layerObjectList) == 0:

            self.logText.append('No new layers were added!')
            QgsMessageLog.logMessage(f'Here SDF', MESSAGE_CATEGORY, Qgis.Info)
            self.updateLabel.emit('No new layers imported!')

            return False
        else:
            QgsMessageLog.logMessage(f'Here C', MESSAGE_CATEGORY, Qgis.Info)
            for layerObject in self.layerObjectList:

                sleep(0.3)
                if self.isCanceled():
                    return False

                self.addLayerToProject.emit(layerObject)

                self.progressCount = self.progressCount + 1

                if step == 0 or self.progressCount % step == 0:

                    self.setProgress(
                        int(100*self.progressCount/len(self.layerObjectList)))

                # self.logText.append(clone.name())

            self.updateLabel.emit('Layers imported!')
            return True

    def finished(self, result):
        """
        This function is automatically called when the task has
        completed (successfully or not).
        You implement finished() to do whatever follow-up stuff
        should happen after the task is complete.
        finished is always called from the main thread, so it's safe
        to do GUI operations and raise Python exceptions here.
        result is the return value from self.run.
        """
        QgsMessageLog.logMessage(
            f'Running finished', MESSAGE_CATEGORY, Qgis.Info)
        if result:
            self.updateLogText.emit(self.logText)

            QgsMessageLog.logMessage(
                'Task "{name}" completed\n'
                'Total: {total} (with {iterations} '
                'iterations)'.format(
                    name=self.description(),
                    total=self.total,
                    iterations=self.iterations),
                MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Task "{name}" not successful but without '
                    'exception (probably the task was manually '
                    'canceled by the user)'.format(
                        name=self.description()),
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(
                    'Task "{name}" Exception: {exception}'.format(
                        name=self.description(),
                        exception=self.exception),
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage(
            'Task "{name}" was canceled'.format(
                name=self.description()),
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
