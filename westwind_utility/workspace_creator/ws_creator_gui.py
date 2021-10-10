from qgis.core import *
from qgis.core import QgsMapLayer, QgsMapLayerType
import os
import ntpath
from qgis.gui import *
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
from westwindutilitysettings import WestWindUtilitySettings

from workspace_creator.tasks import *

from layer_sourcechanger.mousePressEnum import mousePressEnum

MESSAGE_CATEGORY = 'WS Creator'
MESSAGE_CATEGORY_DEBUG = 'WS Creator'

import random
from time import sleep

class WSCreatorGui:

    def __init__(self,_dockWidget,_iface):
        print("Starting WSCreator")
        self.iface = _iface
        self.vectorPath = None
        self.project = QgsProject.instance()
        
        self.dockWidget = _dockWidget
        self.dockWidget.WSCreator_RunButton.clicked.connect(self.run)
        self.dockWidget.WSC_ExportStyles.clicked.connect(self.exportStyles)
        self.dockWidget.WSC_ImportStyles.clicked.connect(self.importStyles)
        #self.directory = 'E:\WWE\Proj - Files\P000_CHEP\GIS_Maps\VectorData\globaldata'
        self.directory = None

        self.directory = 'E:\WWE\Proj - Files\P000_CHEP\GIS_Maps\VectorData'

        self.fileName = os.path.abspath("E:\WWE\Proj - Files\GIS_Reference_Data\Scripts_Macros\Python\StateLayer_DownloadProcessing\settings.yaml")
        self.treeRoot = QgsProject.instance().layerTreeRoot()
        
        self.guiInitilize()


        #self.dockWidget.pushButton_5.clicked.connect(self.test)


    def test(self):
        print(QgsApplication.qgisSettingsDirPath())
        self.settings = WestWindUtilitySettings()
        self.settings.createDefaultSettings()

    def guiInitilize(self):

        #region Connect Actions
        self.dockWidget.WSC_SelectDir_Button.clicked.connect(self.selectDir)

        self.dockWidget.WSC_searchBar.textChanged.connect(lambda x: self.WSC_searchBar(x))

        self.dockWidget.WSC_layerSourceList.currentIndexChanged.connect(lambda x: self.loadFeatures(x))

        self.dockWidget.WSC_BufferDistance_LineEdit.textChanged.connect(self.createRuleStyle)

        self.dockWidget.WSC_ApplyRuleStyle_PushButton.clicked.connect(self.applyRuleStyle)

        self.dockWidget.WSC_LayerAttributeTable_TreeView.mouseReleased.connect(self.handleTreeViewMousePressed)

        self.dockWidget.WCS_onlyVisible_checkBox.clicked.connect(self.WSC_searchBar)

        self.dockWidget.CreateClippedLayers_PushButton.clicked.connect(self.createClippedLayers)

         #load layers into combo box
        self.WSC_searchBar()

        #region Useable Area

        #load layers into combo box
        self.UseableArea_searchBar()

        self.InitialiseCurrentFeatureTreeView()

        self.dockWidget.UseableArea_searchBar.textChanged.connect(lambda x: self.UseableArea_searchBar(x))
        
        self.dockWidget.WSC_layerSourceList.currentIndexChanged.connect(lambda x: self.UseableArea_loadFeatures(x))

        self.dockWidget.WCS_onlyVisible_checkBox.clicked.connect(self.UseableArea_searchBar)

        #endregion

        #endregion

    def exportStyles(self):
        layers = self.treeRoot.findLayers()
        print('here')
        settings = self.loadSettings(self.fileName)
        #print(settings)
        for layer in layers:
            mapLayer = layer.layer()
            stylemanager = mapLayer.styleManager()
            currentstylename = stylemanager.currentStyle()
            currentstyle = stylemanager.style(currentstylename)
            #print(currentstylename)
            #print(currentstyle.xmlData())
            source = mapLayer.source()
            
            settingsFiles = settings['files']

            for sf in settingsFiles:
                sfname= sf['name']

                if not 'QGISStyles' in sf:
                    sf['QGISStyles']=[]
                    sfStyles=[]
                else:
                    sfStyles= sf['QGISStyles']

                if sfname in source:
                    sfStyle = {'styleName': currentstylename,
                    'styleXML': currentstyle.xmlData()
                    }

                    sfStyles.append(sfStyle)
                    
                sf['QGISStyles'] = sfStyles

        self.saveSettings(settings,os.path.abspath("E:\WWE\Proj - Files\GIS_Reference_Data\Scripts_Macros\Python\StateLayer_DownloadProcessing\settings2.yaml"))
        
    def importStyles(self):

        layers = self.treeRoot.findLayers()
        print('here')
        fileName = os.path.abspath("E:\WWE\Proj - Files\GIS_Reference_Data\Scripts_Macros\Python\StateLayer_DownloadProcessing\settings2.yaml")
        settings = self.loadSettings(fileName)
        #print(settings)
        for layer in layers:
            mapLayer = layer.layer()
            stylemanager = mapLayer.styleManager()
            currentstylename = stylemanager.currentStyle()
            currentstyle = stylemanager.style(currentstylename)
            #print(currentstylename)
            #print(currentstyle.xmlData())
            source = mapLayer.source()
            
            settingsFiles = settings['files']

            for sf in settingsFiles:
                sfname= sf['name']

                if 'QGISStyles' in sf:
                    sfStyles= sf['QGISStyles']

                else:
                    print('missing style')
                    continue

                if sfname in source:
                    for style in sfStyles:
                        styleName = style['styleName']
                        styleXML = style['styleXML']
                        styleObject= QgsMapLayerStyle(styleXML)
                        
                        stylemanager.addStyle(styleName,styleObject)

                    print(f'Style {styleName} added to {mapLayer.name()}')
                    
    def saveSettings(self,data,_file):
        with open(_file, 'w') as file:
            documents = yaml.dump(data, file)


    def loadSettings(self,file):

        with open(file) as json_file:
            data = yaml.load(json_file, Loader=yaml.FullLoader)
            return data


    def run(self):

        ignoreFolders = ['workingDirectory']

        if not self.directory:

            if os.path.isdir(self.dockWidget.WSC_Directory_LineEdit.text()):
                self.directory = self.dockWidget.WSC_Directory_LineEdit.text()

            else:

                self.showDialog()
                return

        self.directory = os.path.abspath(self.directory)
        self.dockWidget.WSC_Directory_LineEdit.setText(self.directory)


        #baseGroupName = os.path.basename( self.directory)
        baseGroupName = 'L2'
        baseGroups=['L1', 'L2', 'L3']


        for name in baseGroups:

            globalDataGroup = self.treeRoot.findGroup(name)

            if not globalDataGroup:
                self.treeRoot.addGroup(name)


        globalDataGroup = self.treeRoot.findGroup(baseGroupName)

        for path, dirs, files in os.walk(self.directory):

            dirs[:] = [d for d in dirs if d not in ignoreFolders]

            for d in dirs:
                foundFolderPath = os.path.join(path, d)
                #print(foundFolderPath)
                dirRelativePath = foundFolderPath.replace(self.directory,'')
                #print(relativePath)
                #print(d)
                dirContents = os.listdir(foundFolderPath)
                #print(dirContents)

                containsFiles = any(os.path.isfile(foundFolderPath+'\\'+cF) for cF in dirContents)

                #print(containsFiles)

                if containsFiles:

                    for f in dirContents:
                        #print(f)
                        foundFile, foundFileExt = os.path.splitext(f)
                        foundFilePath = os.path.join(path, d, f)
                        print(foundFilePath)
                        
                        if foundFileExt == '.shp':
                            relativePath = foundFolderPath.replace(self.directory,'')
                            parentFolders = relativePath.split('\\')

                            if '' in parentFolders:
                                parentFolders.remove('')

                            #print(parentFolders)
                            parentGroup = globalDataGroup

                            for folder in parentFolders:
                                #Find if the group exists
                                result = parentGroup.findGroup(folder)

                                if not result:
                                    parentGroup = parentGroup.addGroup(folder)
                                
                                else:
                                    parentGroup = result

                            #Find all the layers that exist in the parent group
                            existingLayers = parentGroup.findLayers()
                            layerExists = False

                            for l in existingLayers:
                                existingLayerSource = l.layer().source()
                                if existingLayerSource == foundFilePath:
                                    layerExists = True

                            if not layerExists:
                                vectorLayer = QgsVectorLayer(foundFilePath, foundFile)
                                mapLayer = QgsProject.instance().addMapLayer(vectorLayer, False)

                                parentGroup.addLayer(vectorLayer)
                else:
                    
                    #if len(dirContents)>0:
                    parentGroup = globalDataGroup
                    #print(parentGroup)
                    #print(dirRelativePath + '\t' + path)
                    
                    parentFolders = dirRelativePath.split('\\')

                    print(parentFolders)
                    if '' in parentFolders:
                            parentFolders.remove('')

                    for folder in parentFolders:
                        #Find if the group exists
                        result = parentGroup.findGroup(folder)

                        if not result:
                            parentGroup = parentGroup.addGroup(folder)
                        
                        else:
                            parentGroup = result



            QgsMessageLog.logMessage(f'here', MESSAGE_CATEGORY_DEBUG, Qgis.Info)
            QgsMessageLog.logMessage(f'{path}', MESSAGE_CATEGORY_DEBUG, Qgis.Info)

    #region Processing Functions
    
    def createRuleStyle(self):
        checkedItems=[]

        self.dockWidget.ClippingRule_TextEdit.setPlainText('')

        combo = self.dockWidget.WSC_layerSourceList

        if self.dockWidget.WSC_LayerAttributeTable_TreeView.model() == None:
            return

        root = self.dockWidget.WSC_LayerAttributeTable_TreeView.model().invisibleRootItem()

        selectedLayerTreeLayer = combo.currentData(Qt.UserRole)

        if selectedLayerTreeLayer == None:

            return

        if self.dockWidget.WSC_BufferDistance_LineEdit.text().isnumeric():

            bufferDistance = int(self.dockWidget.WSC_BufferDistance_LineEdit.text())

        else:


            bufferDistance = '2000'

        selectedLayer = selectedLayerTreeLayer.layer()

        if selectedLayer.type() == QgsMapLayerType.VectorLayer:

            layerId = selectedLayer.id()
            layerCRS = selectedLayer.sourceCrs().authid()

        for item in self.iterItems(root):

            if item.checkState() == Qt.Checked : 
               
                checkedItems.append(item)

        displayText=''

        geometryExpressionArray=[]

        for chkItem in checkedItems:

            feature = chkItem.data(Qt.UserRole)

            displayText = displayText + str(feature.id())

            geometryExpression = f'transform(geometry(get_feature_by_id(\'{layerId}\',\'{feature.id()}\')),\'{layerCRS}\',\'layerCRS\')'

            geometryExpressionArray.append(geometryExpression)

        geometryExpressionCollection = ''

        for i in range(len( geometryExpressionArray)):

            #if len(geometryExpressionArray)=1:

            geometryExpressionCollection = geometryExpressionCollection + geometryExpressionArray[i]

            if i != len(geometryExpressionArray)-1:
                print(f'i is {i}. Length is {len(geometryExpressionArray)}')

                geometryExpressionCollection = geometryExpressionCollection +','

        finalExpression = f'intersects($geometry,buffer(collect_geometries({geometryExpressionCollection}),{bufferDistance}))'

        self.dockWidget.ClippingRule_TextEdit.setPlainText(finalExpression)

        self.geometryExpression = finalExpression

    def applyRuleStyle(self):


        node =self.iface.layerTreeView().currentNode()

        if self.project.layerTreeRoot().isGroup(node):
            treeLayers = node.findLayers()

            for treeLayer in treeLayers:

                layer = treeLayer.layer()

                layerCRS = layer.sourceCrs().authid()

                if layer.type() != QgsMapLayerType.VectorLayer:
                    continue

                if not self.geometryExpression:
                    continue

                geometryExpression = self.geometryExpression.replace('layerCRS',layerCRS)

                if self.dockWidget.ReplaceLayerStyle_CheckBox.isChecked():

                    symbol = QgsSymbol.defaultSymbol(layer.geometryType())

                    renderer = QgsRuleBasedRenderer(symbol)

                    root_rule = renderer.rootRule()

                    rule = root_rule.children()[0]

                    rule.setFilterExpression(geometryExpression)

                    layer.setRenderer(renderer)

                else:

                    renderer = layer.renderer()

                    if renderer.type() == 'RuleRenderer':
                        
                        root_rule = renderer.rootRule()
                        


                        rule = root_rule.children()[0]

                        print(f'The rule is {rule.label()}')

                        rule.setFilterExpression(geometryExpression)

                        layer.setRenderer(renderer)



        if self.project.layerTreeRoot().isLayer(node):

            layer = node.layer()

            if layer.type() != QgsMapLayerType.VectorLayer:
                return

            if not self.geometryExpression:
                return

            geometryExpression = self.geometryExpression.replace('layerCRS',layerCRS)

            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            renderer = QgsRuleBasedRenderer(symbol)

            root_rule = renderer.rootRule()

            rule = root_rule.children()[0]

            rule.setFilterExpression(geometryExpression)

            layer.setRenderer(renderer)

        # print(node)

        # print('here')

    def createClippedLayers(self):

        print('clipping layers')

        node =self.iface.layerTreeView().currentNode()

        checkedItems=[]

        combo = self.dockWidget.WSC_layerSourceList


        if self.dockWidget.WSC_LayerAttributeTable_TreeView.model() == None:
            return

        root = self.dockWidget.WSC_LayerAttributeTable_TreeView.model().invisibleRootItem()

        selectedLayerTreeLayer = combo.currentData(Qt.UserRole)


        if self.dockWidget.WSC_BufferDistance_LineEdit.text().isnumeric():

            bufferDistance = int(self.dockWidget.WSC_BufferDistance_LineEdit.text())

        else:

            bufferDistance = '2000'

        for item in self.iterItems(root):

            if item.checkState() == Qt.Checked : 
               
                checkedItems.append(item)

        if selectedLayerTreeLayer == None:
            return

        selectedLayer = selectedLayerTreeLayer.layer()

        checkedFeaturesGeometry = QgsGeometry()

        if (len(checkedItems)==1):

                feature = checkedItems[0].data(Qt.UserRole)
                #print(f'geometry is {feature.geometry()}')



                checkedFeaturesGeometry = feature.geometry()

        else:

            for i in range(0,len(checkedItems)):

                feature = checkedItems[i].data(Qt.UserRole)
                #print(f'geometry is {feature.geometry()}')

                checkedFeaturesGeometry = QgsGeometry.combine(checkedFeaturesGeometry,feature.geometry())


        #print(f'geometry is {checkedFeaturesGeometry}')
        saveDirectory = QgsApplication.qgisSettingsDirPath() +'/wweTempFiles'

        #saveDirectory = f'C:\\Users\\timc7\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\wweTempFiles'

        if not os.path.isdir(saveDirectory):
            try:
                os.mkdir(saveDirectory)
            except OSError:
                print ("Creation of the directory %s failed" % saveDirectory)
            else:
                print ("Successfully created the directory %s " % saveDirectory)
        
        pendingTasks=[]

        if self.project.layerTreeRoot().isGroup(node):
            treeLayers = node.findLayers()

            # taskNumber = 1

            # longtask = FindIntersectingGeometriesTask('Calculate Intersecting Features', 4, 'featureList', 'treeLayers')
            # print('taskcreated')
            # #longtask.myObjectSignal.connect(self.handleObjectSignal)
            # print('task connected')
            
            # QgsApplication.taskManager().addTask(longtask)

            for treeLayer in treeLayers:

                tCheckedFeaturesGeometry = QgsGeometry(checkedFeaturesGeometry)

                layer = treeLayer.layer()

                if layer.type() != QgsMapLayerType.VectorLayer:
                    continue

                geometryType = layer.geometryType()
                layerCRSID = layer.sourceCrs().authid()

                checkedFeaturesCRSID = selectedLayer.sourceCrs().authid()

                print(f'Layer CRS {layerCRSID}. Checked layer CRS {checkedFeaturesCRSID} ')

                tCheckedFeaturesGeometry.transform(QgsCoordinateTransform(QgsCoordinateReferenceSystem(checkedFeaturesCRSID),QgsCoordinateReferenceSystem(layerCRSID),QgsProject.instance()))

                tCheckedFeaturesGeometry=tCheckedFeaturesGeometry.buffer(bufferDistance,36)

                tempLayer = None
                uri= None
                if geometryType == QgsWkbTypes.PolygonGeometry:

                    print(geometryType)
                    uri = f'polygon?crs={layerCRSID}'

                elif geometryType == QgsWkbTypes.LineGeometry:

                    print(geometryType)
                    uri = f'linestring?crs={layerCRSID}'

                elif geometryType == QgsWkbTypes.PointGeometry:

                    print(geometryType)
                    uri = f'point?crs={layerCRSID}'

                if uri:

                    layerFields = layer.dataProvider().fields()

                    layerStyle = QgsMapLayerStyle()
                    layerStyle.readFromLayer(layer)
                    
                    layerFeatures = list(layer.getFeatures())

                    intersectingFeatures=[]

                    for i in range(0,len(layerFeatures)):

                        if tCheckedFeaturesGeometry.intersects(layerFeatures[i].geometry()):

                            intersectingFeatures.append(layerFeatures[i])
                            print(f'Feature {i} intersected')


                    
                    saveDirectory = QgsApplication.qgisSettingsDirPath() +'/wweTempFiles'

                    layerCRS = layer.sourceCrs()

                    saveOptions = QgsVectorFileWriter.SaveVectorOptions()

                    WKBType = layer.wkbType()

                    saveOptions.driverName = 'ESRI Shapefile'
                    saveOptions.fileEncoding='UTF-8'

                    transformContext = self.project.transformContext()

                    saveExtension = '.shp'

                    saveName = f'{layer.name()}_wweTemp'
                    savePath = os.path.join(saveDirectory, saveName + saveExtension)

                    writer = QgsVectorFileWriter.create(savePath, layerFields, WKBType, layerCRS, transformContext, saveOptions)

                    if writer.hasError() != QgsVectorFileWriter.NoError:
                        print("Error when creating shapefile: ",  writer.errorMessage())

                    writer.addFeatures(intersectingFeatures)

                    del writer

                    print(f'Adding vector layer name {saveName}')

                    #mapLayer = QgsMapLayer(QgsMapLayerType.VectorLayer,saveName,savePath)

                    vLayer = QgsVectorLayer(savePath,saveName,"ogr")

                    #newLayer = self.iface.addVectorLayer(savePath, '' , "ogr")

                    if not vLayer.isValid():

                        print("Layer failed to load!")

                    else:

                        newlayer = QgsProject.instance().addMapLayer(vLayer)

                        newLayerId = newlayer.id()

                        newLayerTree = QgsProject.instance().layerTreeRoot().findLayer(newLayerId)

                        newlayerMapLayer = newLayerTree.layer()

                        print(newlayer)

                        parentNode = treeLayer.parent()
                        
                        print(parentNode)

                        print(newLayerTree.parent())

                        

                        clone = newLayerTree.clone()

                        #mapLayer=self.project.layerTreeRoot().findLayer(vLayer)

                        parentNode.insertChildNode(0,clone)

                        newLayerTree.parent().removeChildNode(newLayerTree)

                        layerStyle.writeToLayer(vLayer)


                #     print(f'Lenght of intersecting features is {len(intersectingFeatures)}')

                #     print('Task in manager')


                #     print('Creating Task')
                   

                #     task = QgsTask.fromFunction(f'Create temp layer {taskNumber}', 
                #     self.findIntersectingGeometries(tCheckedFeaturesGeometry,layerFeatures), 
                #     on_finished=self.exportDataAndAddLayers() )

                #     checkGeometry = tCheckedFeaturesGeometry,
                #     features = layerFeatures 

                # #     print('Task Created')

                #     QgsApplication.taskManager().addTask(task)

                #     print('Task added to mananger')
                #    task.run()

                #     taskNumber = taskNumber + 1

                #     print(f'Task status is {task.status()}')

                #    print("End of fuinction")

                #     task1 = QgsTask.fromFunction('Waste cpu 1', self.findIntersectingGeometries, on_finished=self.exportDataAndAddLayers, wait_time=4)
                #     task2 = QgsTask.fromFunction('Waste cpu 2', self.findIntersectingGeometries, on_finished=self.exportDataAndAddLayers, wait_time=3)
                #     QgsApplication.taskManager().addTask(task1)
                #     QgsApplication.taskManager().addTask(task2)

                #     intersectingFeatures=[]

                #     for i in range(0,len(layerFeatures)):

                #         if tCheckedFeaturesGeometry.intersects(layerFeatures[i].geometry()):

                #             intersectingFeatures.append(layerFeatures[i])
                #             print(f'Feature {i} intersected')

        # QgsMessageLog.logMessage(f'{len(pendingTasks)} tasks ready ready to process',MESSAGE_CATEGORY, Qgis.Info)

        # QgsApplication.taskManager().statusChanged.connect(self.taskStatusChanged)
        # QgsApplication.taskManager().allTasksFinished.connect(self.allTasksFinished)

        # for task in pendingTasks:
        #     QgsMessageLog.logMessage(f"Starting task {task.description()}. status:{task.status()}",MESSAGE_CATEGORY, Qgis.Info)

            
        #     #task.hold()
        #     QgsApplication.taskManager().addTask(task)
            

        #     onholdTasks = [task for task in QgsApplication.taskManager().tasks() if task.status()==1]

        #     QgsMessageLog.logMessage(f'Tasks on hold {len(onholdTasks)}',MESSAGE_CATEGORY, Qgis.Info)

        #     for t in onholdTasks:
        #         queuedTaskCount = len([task for task in QgsApplication.taskManager().tasks() if task.status()==0])
        #         runningTaskCount = len([task for task in QgsApplication.taskManager().tasks() if task.status()==2])
        #         combinedTaskCount= queuedTaskCount + runningTaskCount

        #         if combinedTaskCount<4:
        #             QgsMessageLog.logMessage(f"Releasing Task {t.description()}",MESSAGE_CATEGORY, Qgis.Info)
        #             t.unhold()
                    #t.run()

    #endregion



    #region Gui Functions

    def WSC_searchBar(self,searchValue=''):
        """Populate the source list combobox"""

        searchValue = self.dockWidget.WSC_searchBar.text()

        combo = self.dockWidget.WSC_layerSourceList
        
        layerIds=[]
        treeLayers = self.project.layerTreeRoot().findLayers()
        treeLayers.sort(key=lambda x: ntpath.basename(x.layer().name()))

        for treeLayer in treeLayers:
            if self.dockWidget.WCS_onlyVisible_checkBox.isChecked():
                if not (treeLayer.isVisible()):
                   
                    continue            
            layerId=treeLayer.layer().id()

            combinedName =treeLayer.layer().name() +' - ' + layerId

            if not any(x[0] == layerId for x in layerIds):
                _myTuple = combinedName,treeLayer
                layerIds.append(_myTuple)


        matches = [x for x in layerIds if (searchValue in x[1].layer().name())]
        combo.clear()
        if len(matches)<1:
            combo.addItem(f"No layer sources contain {searchValue}. Try searching something else")
        else:
            for match in matches:
                combo.addItem(match[0],match[1])
        #print(matches)

        self.loadFeatures()

    def loadFeatures(self, index=0):

        combo = self.dockWidget.WSC_layerSourceList

        selectedLayerTreeLayer = combo.currentData(Qt.UserRole)

        if selectedLayerTreeLayer == None:

            return

        selectedLayer = selectedLayerTreeLayer.layer()

        if selectedLayer.type() == QgsMapLayerType.VectorLayer:

            fields = selectedLayer.fields()

            fieldsDisplayNames = [f.displayName() for f in fields]

            fieldsDisplayNames.insert(0,'FID')

            model = QStandardItemModel(0,len(fields),self.dockWidget.WSC_LayerAttributeTable_TreeView)

            for i in range(0,len(fieldsDisplayNames)):
                
                model.setHeaderData(i,Qt.Horizontal,fieldsDisplayNames[i])

            
            self.dockWidget.WSC_LayerAttributeTable_TreeView.setModel(model)



            features = selectedLayer.getFeatures()

            count=0
            for f in features:
                if count>500:
                    print('Over 500 features')
                    break
                row = []

                for i in range(len(fieldsDisplayNames)) :
                    #print(f'index is {i}' )

                    if i ==0:

                        value = f.id()
                       # print(f'Id is {value}')
                    else:
                        value = f.attribute(fieldsDisplayNames[i])

                   # print(value)

                    item = QStandardItem(0,i)
                    item.setData(value, Qt.DisplayRole)

                    row.append(item)
                    if i ==0:
                        item.setData(f,Qt.UserRole)
                        item.setCheckable(True)

                model.appendRow(row)
                count = count+1

            self.reconnect(self.dockWidget.WSC_LayerAttributeTable_TreeView.selectionModel().selectionChanged, self.createRuleStyle)
        #combo.setModel(model)

    def iterItems(self, root):
        if root is not None:
            stack = [root]
            while stack:
                parent = stack.pop(0)
                for row in range(parent.rowCount()):

                    child = parent.child(row, 0)
                    yield child
                    if child.hasChildren():
                        stack.append(child)        

    def showDialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)

        msg.setText("Vector data path has not been set")
        msg.setInformativeText("Please set the vector data path before running the import. This only has to be set once")
        msg.setWindowTitle("Path not Set")

        msg.setStandardButtons(QMessageBox.Open)
 
        retval = msg.exec_()
        print ("value of pressed message box button:", retval )
        
        if (retval==8192):
            self.selectDir()

    def selectDir(self):
        """ Open a dialog for the user to choose a starting directory """

        self.directory = QFileDialog.getExistingDirectory(self.dockWidget, 'Select vector data path', '/home', QFileDialog.ShowDirsOnly)
        self.directory = os.path.abspath(self.directory)
        self.dockWidget.WSC_Directory_LineEdit.setText(self.directory)

    def reconnect(self, signal, newhandler=None, oldhandler=None):
        print(f'reconnecting {signal} {newhandler} {oldhandler}')        
        try:
            if oldhandler is not None:
                while True:
                    signal.disconnect(oldhandler)
            else:
                signal.disconnect()
        except TypeError:
            pass
        if newhandler is not None:
            print('connectinghandler')
            signal.connect(newhandler)

    def handleTreeViewMousePressed(self,value):

        if value is mousePressEnum.leftclick.value:
            #self.dockWidget.WSC_LayerAttributeTable_TreeView.layoutChanged()
            self.createRuleStyle()

    #region Useable Area

    def UseableArea_searchBar(self,searchValue=''):
        """Populate the source list combobox"""

        searchValue = self.dockWidget.UseableArea_searchBar.text()

        combo = self.dockWidget.UseableArea_layerSourceList
        
        layerIds=[]
        treeLayers = self.project.layerTreeRoot().findLayers()
        treeLayers.sort(key=lambda x: ntpath.basename(x.layer().name()))

        for treeLayer in treeLayers:
            if self.dockWidget.UseableArea_onlyVisible_checkBox.isChecked():
                if not (treeLayer.isVisible()):
                   
                    continue            
            layerId=treeLayer.layer().id()

            combinedName =treeLayer.layer().name() +' - ' + layerId

            if not any(x[0] == layerId for x in layerIds):
                _myTuple = combinedName,treeLayer
                layerIds.append(_myTuple)


        matches = [x for x in layerIds if (searchValue in x[1].layer().name())]
        combo.clear()
        if len(matches)<1:
            combo.addItem(f"No layer sources contain {searchValue}. Try searching something else")
        else:
            for match in matches:
                combo.addItem(match[0],match[1])
        #print(matches)

        self.UseableArea_loadFeatures()

    def UseableArea_loadFeatures(self, index=0):

        combo = self.dockWidget.UseableArea_layerSourceList

        selectedLayerTreeLayer = combo.currentData(Qt.UserRole)

        if selectedLayerTreeLayer == None:
            print('selectedLayer is None')

            return

        selectedLayer = selectedLayerTreeLayer.layer()

        if selectedLayer.type() == QgsMapLayerType.VectorLayer:
            print('vectorLayer')

            fields = selectedLayer.fields()

            fieldsDisplayNames = [f.displayName() for f in fields]

            fieldsDisplayNames.insert(0,'FID')

            model = QStandardItemModel(0,len(fields),self.dockWidget.UseableArea_LayerAttributeTable_TreeView)

            for i in range(0,len(fieldsDisplayNames)):
                
                model.setHeaderData(i,Qt.Horizontal,fieldsDisplayNames[i])

            
            self.dockWidget.UseableArea_LayerAttributeTable_TreeView.setModel(model)



            features = selectedLayer.getFeatures()

            count=0
            for f in features:
                if count>500:
                    print('Over 500 features')
                    break
                row = []

                for i in range(len(fieldsDisplayNames)) :
                    #print(f'index is {i}' )

                    if i ==0:

                        value = f.id()
                       # print(f'Id is {value}')
                    else:
                        value = f.attribute(fieldsDisplayNames[i])

                   # print(value)

                    item = QStandardItem(0,i)
                    item.setData(value, Qt.DisplayRole)

                    row.append(item)
                    if i ==0:
                        item.setData(f,Qt.UserRole)
                        item.setCheckable(True)

                model.appendRow(row)
                count = count+1

            self.reconnect(self.dockWidget.UseableArea_LayerAttributeTable_TreeView.selectionModel().selectionChanged, self.createRuleStyle)
        #combo.setModel(model)

    def InitialiseCurrentFeatureTreeView(self):

        treeViewHeaders=['Type','Layer Name','FID']

        model = QStandardItemModel(0,len(treeViewHeaders),self.dockWidget.UseableArea_currentFeatures_treeView)

        for i in range(0,len(treeViewHeaders)):
            
            model.setHeaderData(i,Qt.Horizontal,treeViewHeaders[i])

        self.dockWidget.UseableArea_currentFeatures_treeView.setModel(model)

    def AddItemToUseableArea(self):

        print('')

    #endregion


    #endregion


    #region Tasks

    def taskStatusChanged(self, taskId, status):

        QgsMessageLog.logMessage(f"Task Status Changed ID: {taskId} to Status {status}",MESSAGE_CATEGORY, Qgis.Info)

        changedTask=QgsApplication.taskManager().task(taskId)
        string = str(changedTask.description())
        if not "Geometry Interecting" in string:
            return

        QgsMessageLog.logMessage(f"Task description accepted",MESSAGE_CATEGORY, Qgis.Info)

        onholdTasks = [task for task in QgsApplication.taskManager().tasks() if task.status()==1]

        for t in onholdTasks:
            queuedTaskCount = len([task for task in QgsApplication.taskManager().tasks() if task.status()==0])
            runningTaskCount = len([task for task in QgsApplication.taskManager().tasks() if task.status()==2])
            combinedTaskCount= queuedTaskCount + runningTaskCount
            if combinedTaskCount<4:
                QgsMessageLog.logMessage(f"Releasing Task {t.description()}",MESSAGE_CATEGORY, Qgis.Info)
                t.unhold()
            else:
                break

        if changedTask.status() == 3:
            changedTask=QgsApplication.taskManager().task(taskId)
            changedTask.cancel()


        else:
            return

    def allTasksFinished(self):
        self.dockWidget.locateSourcesButton.setText("Locate Missing Sources")
        QgsMessageLog.logMessage(f'Disconnecting tasks from all tasks finished',MESSAGE_CATEGORY_DEBUG, Qgis.Info)
        try:
            QgsApplication.taskManager().statusChanged.disconnect()
            #QgsApplication.taskManager().progressChanged.disconnect()
            QgsApplication.taskManager().allTasksFinished.disconnect()
            QgsApplication.taskManager().cancelAll()

            
        except TypeError:
            pass

        finally:
            QgsApplication.taskManager().cancelAll()
            QgsMessageLog.logMessage(f'Still {len(QgsApplication.taskManager().tasks())} being tracked ',MESSAGE_CATEGORY_DEBUG, Qgis.Warning)

    def handleObjectSignal(self,task):

        QgsMessageLog.logMessage(f'Task "{task.description()} found {len(task.intersectingFeatures)} features intersecting. Current status is {task.status()}', MESSAGE_CATEGORY, Qgis.Success)  

        # QgsMessageLog.logMessage(f'Task finsihed setting progress to 100', MESSAGE_CATEGORY, Qgis.Success)  
        # task.setProgress(100)
        # task.cancel()


    def findIntersectingGeometries1(task,checkGeometry,features):
        """
        Raises an exception to abort the task.
        Returns a result if success.
        The result will be passed, together with the exception (None in
        the case of success), to the on_finished method.
        If there is an exception, there will be no result.
        """

        QgsMessageLog.logMessage('Started task {}'.format(task.description()), MESSAGE_CATEGORY, Qgis.Info)
        print('Finding intersecting layers')

        intersectingFeatures=[]

        increment = 100/len(features)

        for i in range(0,len(features)):

            if checkGeometry.intersects(features[i].geometry()):

                intersectingFeatures.append(features[i])
                print(f'Feature {i} intersected')

            #if increment%i == 0:
            print(f'Setting Progress to {i * increment}')
            task.setProgress(i * increment)
                

            if task.isCanceled():
                stopped(task)
                return None

        print('returning')
        return {'intersectingFeatures': intersectingFeatures}


    def exportDataAndAddLayers1(exception, result=None):

            """This is called when doSomething is finished.
            Exception is not None if doSomething raises an exception.
            result is the return value of doSomething."""
            print('in the export parts')
            if exception is None:
                if result is None:
                    QgsMessageLog.logMessage(
                        'Completed with no exception and no result '\
                        '(probably manually canceled by the user)',
                        MESSAGE_CATEGORY, Qgis.Warning)
                else:

                    print(result['intersectingFeatures'])
            else:
                QgsMessageLog.logMessage("Exception: {}".format(exception), MESSAGE_CATEGORY, Qgis.Critical)
                raise exception



            print('success')

            print(result)

            saveDirectory = QgsApplication.qgisSettingsDirPath() +'/wweTempFiles'

            layerCRS = layer.sourceCrs()

            saveOptions = QgsVectorFileWriter.SaveVectorOptions()

            WKBType = layer.wkbType()

            saveOptions.driverName = 'ESRI Shapefile'
            saveOptions.fileEncoding='UTF-8'

            transformContext = self.project.transformContext()

            saveExtension = '.shp'

            saveName = f'{layer.name()}_wweTemp'
            savePath = os.path.join(saveDirectory, saveName + saveExtension)

            writer = QgsVectorFileWriter.create(savePath, layerFields, WKBType, layerCRS, transformContext, saveOptions)

            if writer.hasError() != QgsVectorFileWriter.NoError:
                print("Error when creating shapefile: ",  writer.errorMessage())

            writer.addFeatures(intersectingFeatures)

            del writer

            print(f'Adding vector layer name {saveName}')

            newLayer = self.iface.addVectorLayer(savePath, '' , "ogr")

            layerStyle.writeToLayer(newLayer)



        #print(task.checkGeometry) 

        #print(task.intersectingFeatures)     

    #end Region



    #region Testing


#MESSAGE_CATEGORY = 'TaskFromFunction'

    def findIntersectingGeometries(self, task, wait_time):
        """
        Raises an exception to abort the task.
        Returns a result if success.
        The result will be passed, together with the exception (None in
        the case of success), to the on_finished method.
        If there is an exception, there will be no result.
        """
        QgsMessageLog.logMessage('Started task {}'.format(task.description()),
                                MESSAGE_CATEGORY, Qgis.Info)
        wait_time = wait_time / 100
        total = 0
        iterations = 0
        for i in range(100):
            sleep(wait_time)
            # use task.setProgress to report progress
            task.setProgress(i)
            arandominteger = random.randint(0, 500)
            total += arandominteger
            iterations += 1
            # check task.isCanceled() to handle cancellation
            if task.isCanceled():
                stopped(task)
                return None
            # raise an exception to abort the task
            if arandominteger == 42:
                raise Exception('bad value!')
        print('task complete')
        return {'total': total, 'iterations': iterations,
                'task': task.description()}

    def stopped(self, task):
        QgsMessageLog.logMessage(
            'Task "{name}" was canceled'.format(
                name=task.description()),
            MESSAGE_CATEGORY, Qgis.Info)

    def exportDataAndAddLayers(self, exception, result=None):
        """This is called when doSomething is finished.
        Exception is not None if doSomething raises an exception.
        result is the return value of doSomething."""
        print(f'Finishing up Task. Result is {result}')
        #QgsMessageLog.logMessage(f'Finished task {result}', MESSAGE_CATEGORY, Qgis.Info)
        if exception is None:
            if result is None:
                QgsMessageLog.logMessage(
                    'Completed with no exception and no result '\
                    '(probably manually canceled by the user)',
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(
                    'Task {name} completed\n'
                    'Total: {total} ( with {iterations} '
                    'iterations)'.format(
                        name=result['task'],
                        total=result['total'],
                        iterations=result['iterations']),
                    MESSAGE_CATEGORY, Qgis.Info)
        else:
            print('exception found')
            QgsMessageLog.logMessage("Exception: {}".format(exception),
                                    MESSAGE_CATEGORY, Qgis.Critical)
            raise exception

    # Create a few tasks



    #endregion