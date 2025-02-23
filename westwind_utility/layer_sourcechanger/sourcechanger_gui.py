from qgis.core import *
import ntpath
import re

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt, pyqtSignal, QEvent, pyqtSlot
from PyQt5.QtGui import QIcon, QStandardItemModel, QCursor, QMouseEvent
from PyQt5.QtWidgets import QAction, QApplication, QDialog, QFileDialog, QMessageBox, QMenu, QTreeView, QSizePolicy, QLayout, QVBoxLayout

from .helperclasses.shpProcessedFileName import shpProcessedFileName
#from .layer_importer.importer_gui import ImporterGui
from layer_sourcechanger.mousePressEnum import mousePressEnum

from .gui.editingManyLayersWarningDialog import editingManyLayersWarningDialog
import os.path

class SourceChangerGui:
    """Gui Manager """
    def __init__(self,_dockWidget,_importer):
        """Constructor """
        self.dockWidget = _dockWidget
        self.project = QgsProject.instance()

        #Connect to listeners
        self.dockWidget.updateAllButton.clicked.connect(self.autoUpdateAllLayerSources)
        self.dockWidget.browseNewSource.clicked.connect(self.browseNewSource)
        self.dockWidget.refreshComboBox.clicked.connect(self.refreshComboBox)
        self.dockWidget.searchBar.textChanged.connect(lambda x: self.searchBar(x))
        self.dockWidget.onlyVisibleCheckbox.stateChanged.connect(self.visibleCheckboxSignalHandler)
        self.dockWidget.layerSourceList.currentIndexChanged.connect(self.showSourceInfo)
        self.dockWidget.updateSelectedButton.clicked.connect(self.autoUpdateSelectedLayerSource)

        self.dockWidget.pushButton_8.clicked.connect(self.test)

        self.dockWidget.treeView.mousePressed.connect(self.handleTreeViewMousePressed)

        self.populateSourceList()
        self.handleLSC_specificVersionCheckbox()
        self.dockWidget.LSC_specificVersionCheckbox.stateChanged.connect(lambda x: self.handleLSC_specificVersionCheckbox(x))
        self.dockWidget.LSC_minorVersionCheckbox.stateChanged.connect(lambda x: self.handleLSC_minorVersionCheckbox(x))
        self.dockWidget.LSC_majorVersionSpinbox.valueChanged.connect(self.renameUpdateButton)
        self.dockWidget.LSC_minorVersionSpinbox.valueChanged.connect(self.renameUpdateButton)
 
        self.dockWidget.treeView.setEnabled(True)
        self.dockWidget.treeView.setMouseTracking(True)
        self.dockWidget.treeView.installEventFilter(self.dockWidget.treeView)

    def test(self):
        print(self.dockWidget.LSC_majorVersionSpinbox.value())
        majorVersion=self.dockWidget.LSC_majorVersionSpinbox.value()
        minorVersion=self.dockWidget.LSC_minorVersionSpinbox.value()
        combinedVersion=int(f"{majorVersion}{minorVersion}")
        print(combinedVersion)
        combo = self.dockWidget.layerSourceList
        selectedLayerTreeLayer= combo.currentData()
        source=selectedLayerTreeLayer.layer().source()
        currentSourceFileNameInformation = shpProcessedFileName(source,ntpath.basename(source))
        print(currentSourceFileNameInformation.versionNum)


    def renameUpdateButton(self):
        if  self.dockWidget.LSC_specificVersionCheckbox.isChecked():
            if self.dockWidget.LSC_minorVersionCheckbox.isChecked():
                majorVersionText = f"{self.dockWidget.LSC_majorVersionSpinbox.prefix()}"+'{0:02d}'.format(self.dockWidget.LSC_majorVersionSpinbox.value())
                minorVersionText = '{0:02d}'.format(self.dockWidget.LSC_minorVersionSpinbox.value())
                versionText= f"{majorVersionText}-{minorVersionText}"
                self.dockWidget.updateAllButton.setText(f"All to {versionText}")
                self.dockWidget.updateSelectedButton.setText(f"Selected to {versionText}")
            elif not self.dockWidget.LSC_minorVersionCheckbox.isChecked():
                majorVersionText = f"{self.dockWidget.LSC_majorVersionSpinbox.prefix()}"+'{0:02d}'.format(self.dockWidget.LSC_majorVersionSpinbox.value())
                self.dockWidget.updateAllButton.setText(f"All to {majorVersionText}")
                self.dockWidget.updateSelectedButton.setText(f"Selected to {majorVersionText}")
        else:
            self.dockWidget.updateAllButton.setText(f"Update All")
            self.dockWidget.updateSelectedButton.setText("Update Selected")

    def handleLSC_minorVersionCheckbox(self, state=Qt.CheckState.Unchecked):
        print(f"The minor version check state is {state}")

        if not self.dockWidget.LSC_minorVersionCheckbox.isChecked():
            print("disabling")
            self.dockWidget.LSC_minorVersionSpinbox.setEnabled(False)
            self.renameUpdateButton()

        elif self.dockWidget.LSC_specificVersionCheckbox.isChecked() and self.dockWidget.LSC_minorVersionCheckbox.isChecked():
            self.dockWidget.LSC_minorVersionSpinbox.setEnabled(True)
            self.renameUpdateButton()

    def handleLSC_specificVersionCheckbox(self, state=Qt.CheckState.Unchecked):
        print(f"The check state is {state}")
        if not self.dockWidget.LSC_specificVersionCheckbox.isChecked():
            print("hiding")
            self.dockWidget.LSC_majorVersionSpinbox.hide()
            self.dockWidget.LSC_majorVersionLabel.hide()
            self.dockWidget.LSC_minorVersionSpinbox.hide()
            self.dockWidget.LSC_minorVersionCheckbox.hide()
            self.renameUpdateButton()

        elif self.dockWidget.LSC_specificVersionCheckbox.isChecked():
            self.dockWidget.LSC_majorVersionSpinbox.show()
            self.dockWidget.LSC_majorVersionLabel.show()
            self.dockWidget.LSC_minorVersionSpinbox.show()
            self.dockWidget.LSC_minorVersionCheckbox.show()
            self.renameUpdateButton()

    def handleTreeViewMousePressed(self,value):
        
        if value is mousePressEnum.rightclick.value:
            
            self.createMenu()

    def showWarningDialogBox(self):
        self.warningDialog.show()

    def visibleCheckboxSignalHandler(self):
        searchValue = self.dockWidget.searchBar.text()
        if (not searchValue and searchValue is None):
            return
        self.searchBar(searchValue)

    def updateSelectedTreeViewLayerSource(self):
        selected = self.dockWidget.treeView.selectedIndexes()
        layerId = selected[2].data()
        layerTreeLayer = self.project.layerTreeRoot().findLayer(layerId)
            #print(i.model().item(i.row(),0).text())
        #print(layerTreeLayer.layer().source())
        self.browseNewSource(layerTreeLayer)

    def createMenu(self,parent=None):
        self.popupMenu = QMenu(parent)
        self.popupMenu.addAction("Update Single Layer Source", self.updateSelectedTreeViewLayerSource)
        #print("Menu")
        self.popupMenu.exec(QCursor.pos())

    def searchBar(self,searchValue):
        """Populate the source list combobox"""
        #print(searchValue)
        if (not searchValue and searchValue is None):
            self.populateSourceList
            return
        combo = self.dockWidget.layerSourceList
        
        layerSources=[]
        treeLayers = self.project.layerTreeRoot().findLayers()
        treeLayers.sort(key=lambda x: ntpath.basename(x.layer().source()))
        #print('Filtering for searching')
        #print('Layer Count %d' %(len(treeLayers)))

        for treeLayer in treeLayers:
            if self.dockWidget.onlyVisibleCheckbox.isChecked():
                if not (treeLayer.isVisible()):
                    #print(f"{treeLayer.name()} is not Visible")
                    continue            
            source=treeLayer.layer().source()
            baseName = ntpath.basename(source)
            if not any(x[0] == source for x in layerSources):
                _myTuple = source,treeLayer
                layerSources.append(_myTuple)

        matches = [x for x in layerSources if (searchValue in x[1].layer().name())]
        combo.clear()
        if len(matches)<1:
            combo.addItem(f"No layer sources contain {searchValue}. Try searching something else")
        else:
            for match in matches:
                combo.addItem(ntpath.basename(match[0]),match[1])
        #print(matches)

    def getDockWidget():
        """"""
        if self.dockWidget is not None:
            return self.dockWidget
        else:
            return None

    def showSourceInfo(self):
        combo = self.dockWidget.layerSourceList
        selectedLayerTreeLayer= combo.currentData()
        model = self.createTreeViewLayerModel(self.dockWidget.treeView)
        
        self.dockWidget.treeView.setModel(model)
        count=0
        if selectedLayerTreeLayer is not None:
            selectedLayerSource=selectedLayerTreeLayer.layer().source()
            regexResult = self.checkForVersion(ntpath.basename(selectedLayerTreeLayer.layer().source()))
            treeLayers = self.project.layerTreeRoot().findLayers()
            for treeLayer in treeLayers:
                layer = treeLayer.layer()
                layerSource = layer.source()
                #print(layerSource)
                if layerSource == selectedLayerSource:
                    visibility='Not Visible'
                    layerName = layer.name()
                    if treeLayer.isVisible():
                        visibility='Visible'
                        
                    #print(layerName)
                    self.addTreeViewItem(model, layerName, visibility, layer.id(),treeLayer)
                    count= count + 1
                else:
                    print('Layer Source didnt match')

            #self.changeSourceToLatestVersion(layerSource)
            #print('ToDO')
        else:
            print('There is no source available')
        if count is 1:
            self.dockWidget.sourceInformationLabel.setToolTip(f"{count} layer uses the selected source")
        else:
            self.dockWidget.sourceInformationLabel.setToolTip(f"{count} layers use the selected source")
        #self.dockWidget.treeView.setColumnWidth(0,200)

    def layerAdded(self,layerName):
        print(f"{layerName} was added to the project. Updating combolist")
        self.populateSourceList()

    def layerRemoved(self,layerName):
        print(f"{layerName} was removed from the project. Updating combobox")     
        self.populateSourceList()

    def refreshComboBox(self):
        print('Refreshing')
        searchValue = self.dockWidget.searchBar.text()
        if (not searchValue and searchValue is None):
            self.populateSourceList()
        else:
            self.searchBar(searchValue)
        
    def populateSourceList(self):
        """Populate the source list combobox"""
        print('Populating combobox')
        combo = self.dockWidget.layerSourceList
        combo.clear()
        layerSources=[]
        treeLayers = self.project.layerTreeRoot().findLayers()

        for t in treeLayers:
            print(t.layer())
            if t.layer() == None:
                print(f'This one is NONE SFDDFDFSDFSDF {t}')

        tree_empty_all = list(t for t in treeLayers if t.layer() == None)

        # print(tree_empty_all)
        # tree_empty=tree_empty_all[0]

        # print(f'the empty layer is {tree_empty}. {tree_empty.layerId()} Name {tree_empty.name()}')

        treeLayers.sort(key=lambda x: ntpath.basename(x.layer().source()))
        print('Layer Count %d' %(len(treeLayers)))
        for treeLayer in treeLayers:
            if self.dockWidget.onlyVisibleCheckbox.isChecked():
                if not (treeLayer.isVisible()):
                    print(f"{treeLayer.name()} is not Visible")
                    continue
            source=treeLayer.layer().source()
            baseName = ntpath.basename(source)
            if source not in layerSources:
                layerSources.append(source)
                print(baseName)
                combo.addItem(baseName,treeLayer)
            else:
                print('This source is already here')

    def browseNewSource(self,singleUpdate=False):
        """ Open a dialog for the user to choose a new source for the layer"""
        combo = self.dockWidget.layerSourceList
        newSource = None
        currentSource = None
        print(f"SingleUpdate Value {singleUpdate}")
        if combo.currentData() is not None and singleUpdate is False:
            currentSource = combo.currentData().layer().source()
            layerDir = ntpath.dirname(currentSource)
            layerFileName, layerExtension = os.path.splitext(currentSource)
            newSource,_filter = QFileDialog.getOpenFileName(self.dockWidget, 'Select the new data source path', layerDir, f"Shape files (*{layerExtension});; All Files (*.*)")
            print(f'The new source is: {newSource}')

            if (newSource and newSource is not None):
                print(f'New source selected, updating layer to {newSource}')

                self.updateAllLayerSources(newSource,currentSource)
                print('Layer updated')
                self.refreshComboBox()
            else:
                print('New source not chosen')
                print(self.dockWidget.searchBar.text())
                self.searchBar(self.dockWidget.searchBar.text())
        elif singleUpdate is not False:
            currentSource= singleUpdate.layer().source()
            layerDir = ntpath.dirname(currentSource)
            layerFileName, layerExtension = os.path.splitext(currentSource)
            newSource,_filter = QFileDialog.getOpenFileName(self.dockWidget, 'Select the new data source path', layerDir, f"Shape files (*{layerExtension});; All Files (*.*)")
            print(f'The new source is: {newSource}')

            if (newSource and newSource is not None):
                print(f'New source selected, updating layer to {newSource}')

                self.updateSingleLayerSource(newSource,currentSource,singleUpdate)
                print('Layer updated')
                self.refreshComboBox()
            else:
                print('New source not chosen')

        else:
            print('There is no source available')
           
    def updateAllLayerSources(self,newSourcePath, currentSourcePath):
        """Updated all the layers with the selected source"""
        treeLayers = self.project.layerTreeRoot().findLayers()
        print(f'The current source is {currentSourcePath}')
        print(f'The new source is {newSourcePath}')
        for treeLayer in treeLayers:
            layer = treeLayer.layer()
            layerSource = layer.source()
            print(layerSource)
            if layerSource == currentSourcePath:

                layerName = layer.name()
                print(layerName)
                currentSourceFileName = os.path.splitext(ntpath.basename(currentSourcePath))[0] #without the extension
                newSourceFileName = os.path.splitext(ntpath.basename(newSourcePath))[0]
                if currentSourceFileName in layerName:
                    newLayerName = layerName.replace(currentSourceFileName,newSourceFileName)
                else:
                    newLayerName = layerName
                    print('LayerName not found')
                
                providerName = layer.dataProvider().name()
                layer.setDataSource(newSourcePath,newLayerName,providerName)
            else:
                print('Layer Source didnt match')
  
    def updateSingleLayerSource(self,newSourcePath, currentSourcePath,treeLayer):
        """Updated all the layers with the selected source"""
        print(f'The current source is {currentSourcePath}')
        layer = treeLayer.layer()
        layerSource = layer.source()
        print(layerSource)
        if layerSource == currentSourcePath:

            layerName = layer.name()
            print(layerName)
            currentSourceFileName = os.path.splitext(ntpath.basename(currentSourcePath))[0] #without the extension
            newSourceFileName = os.path.splitext(ntpath.basename(newSourcePath))[0]
            if currentSourceFileName in layerName:
                newLayerName = layerName.replace(currentSourceFileName,newSourceFileName)
            else:
                print('LayerName not found')
                
            providerName = layer.dataProvider().name()
            layer.setDataSource(newSourcePath,newLayerName,providerName)
        else:
            print('Layer Source didnt match')

    def checkForVersion(self, name):
        """Get the version of a layer """
        regA = re.compile('(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*).shp\Z')
        result= regA.match(name)

        return result

    def getLatestVersion(self,processedFileNames):
        """Gets the latest version given a list of processed filenames"""

        latestVersion =-99999
        lastestVersionFile=None
        for file in processedFileNames:
            versionNum = file.versionNum
            if versionNum>latestVersion:
                latestVersion = versionNum
                lastestVersionFile = file

        return lastestVersionFile

    def createTreeViewLayerModel(self,parent):
        model = QStandardItemModel(0, 3, parent)
        model.setHeaderData(0, Qt.Horizontal, "Layer Name")
        model.setHeaderData(1, Qt.Horizontal, "Visibility")
        model.setHeaderData(2, Qt.Horizontal, "Layer ID")
        
        return model

    def createDialogTreeViewLayerModel(self,parent):
        model = QStandardItemModel(0, 3, parent)
        model.setHeaderData(0, Qt.Horizontal, "Layer Name")
        model.setHeaderData(1, Qt.Horizontal, "Current Version")
        model.setHeaderData(2, Qt.Horizontal, "New Version")
        
        return model

    def addTreeViewItem(self,model, layerName, visibility,layerId,modelData):
        model.insertRow(0)
        
        print(f"Model Data is {modelData.layer().name()}")
        model.setData(model.index(0, 0), layerName)
        model.setData(model.index(0, 1), visibility)
        model.setData(model.index(0, 2), layerId)

    def addDialogTreeViewItem(self,model, layerName, currentVersion,newVersion,modelData):
        model.insertRow(0)
        
        model.setData(model.index(0, 0), layerName)
        model.setData(model.index(0, 1), currentVersion)
        model.setData(model.index(0, 2), newVersion)

    def autoUpdateAllLayerSources(self):
        combo = self.dockWidget.layerSourceList
        allItems = [combo.itemData(i) for i in range(combo.count())]
        sourcetoLayerTupleList = []
        self.warningDialog = editingManyLayersWarningDialog()
        model = self.createDialogTreeViewLayerModel(self.warningDialog)
        #result = self.warningDialog.show()
        self.warningDialog.dialogTreeView.setModel(model)
        for item in allItems:   
            source=item.layer().source()
            sourceFullFileName=ntpath.basename(source)
            #print(sourceFullFileName)
            if self.checkForVersion(sourceFullFileName) is not None:
                sourcetoLayerTuple = tuple((source,self.getLayersUsingSource(source)))
                print(f"{len(sourcetoLayerTuple[1])} is the lenth of layers using this source {source}")
                #print(item.layer().source())
                sourcetoLayerTupleList.append(sourcetoLayerTuple)
            else:
                print(f"{source} doesnt have a valid version")

        for item in sourcetoLayerTupleList:
            source = item[0]
            treeLayerList = item[1]
            latestSourceFile = self.autoUpdateProcessing(source,True)
            latestSourceVersion = latestSourceFile.version
            currentSourceFileNameInformation = shpProcessedFileName(source,ntpath.basename(source))
            for treeLayer in treeLayerList:
                layerName= treeLayer.layer().name()
                #print("adding item to tree view")
                self.addDialogTreeViewItem(model, layerName, currentSourceFileNameInformation.version, latestSourceVersion,treeLayer)
        
        result = self.warningDialog.exec()
        #print(result)
        
        if result is 1:
            for item in allItems:
                if self.checkForVersion(ntpath.basename(item.layer().source())) is not None:
                    self.autoUpdateProcessing(item.layer().source())
                    #print(item.layer().source())
        else:
            print("Cancelled Auto Update")

    def getSelectedVersion(self,targetVersion, processedFileNames):
        """Get the specific version that is displayed in dockwidget scroll boxes"""
        closestVersion =-99999
        closestVersionFile=None
        currentDifference = 1000000

        if self.dockWidget.LSC_requireExactVersionMatchCheckbox.isChecked():
            count = 0
            versionFound = False
            for file in processedFileNames:

                versionNum = file.versionNum
                if versionNum is targetVersion:
                    count= count +1
                    closestVersion = versionNum
                    closestVersionFile = file
                    versionFound=True
            if versionFound is False:
                return None
            elif count>0:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Multiple files with that version number")
                msg.setInformativeText(f"Mutiple files were found with the version {versionNum}")
                msg.setWindowTitle("Multiple version found")
                msg.setStandardButtons(QMessageBox.Open)
                return lastestVersionFile
            else:
                return latestVersionFile
        else:
            count = 0
            versionFound = False
            for file in processedFileNames:
                
                versionNum = file.versionNum
                difference = targetVersion-versionNum
                if difference< currentDifference:
                    closestVersion = versionNum
                    closestVersionFile = file
                    versionFound=True
            if versionFound is False:
                return None
            else:
                return closestVersionFile

    def autoUpdateSelectedLayerSource(self):
        """Auto Update the selected Layer Source to the latest version"""
        combo = self.dockWidget.layerSourceList

        currentSource = None
        if combo.currentData() is not None:

            if self.dockWidget.LSC_specificVersionCheckbox.isChecked():
                print("Todo")

            else:
                currentSource = combo.currentData().layer().source()
                self.autoUpdateProcessing(currentSource)
        else:
            print('There is no source available')
  
    def autoUpdateProcessing(self, sourcePath, returnLatestVersionFile = False):
        newSource = None
        layerDir = ntpath.dirname(sourcePath)
        currentSourcePathName, currentSourceExtension= os.path.splitext(sourcePath)
        currentSourceFileName = os.path.splitext(ntpath.basename(sourcePath))[0]
        print (f"{currentSourcePathName} and {currentSourceExtension}")
        print (f"Current source {currentSourceFileName}")
        currentSourceFileNameInformation = shpProcessedFileName(currentSourcePathName+currentSourceExtension,currentSourceFileName+currentSourceExtension)
        walkData = os.walk(layerDir, topdown=True)
        #print(currentSourceFileNameInformation.version)
        processedFileNameList =[]
        for roots, dirs, files in walkData:      
            for file in files:
                #print(file)
                #print(self.checkForVersion(file))
                if self.checkForVersion(file) is not None:
                    fileNameInfo = shpProcessedFileName(roots +"\\"+file, file)

                    if (currentSourceFileNameInformation.disciplineName == fileNameInfo.disciplineName 
                    and currentSourceFileNameInformation.additionalInfo == fileNameInfo.additionalInfo):
                        processedFileNameList.append(fileNameInfo)

        if self.dockWidget.LSC_specificVersionCheckbox.isChecked():
            if self.dockWidget.LSC_minorVersionCheckbox.isChecked():
                majorVersion=self.dockWidget.LSC_majorVersionSpinbox.value()
                minorVersion=self.dockWidget.LSC_minorVersionSpinbox.value()
                combinedVersion=int(f"{majorVersion}{minorVersion}")
            else:
                print()
        else:
            latestVersionFile = self.getLatestVersion(processedFileNameList)
            newSource = latestVersionFile.path
            if returnLatestVersionFile:
                return latestVersionFile
            else:
                self.updateAllLayerSources(newSource,sourcePath)
                self.searchBar(self.dockWidget.searchBar.text())

    def getLayersUsingSource(self,source):
        """Returns all the tree layer objects using a given source"""
        treeLayers = self.project.layerTreeRoot().findLayers()
        #print(f'The current source is {source}')
        treeLayerList=[]
        for treeLayer in treeLayers:
            layerSource = treeLayer.layer().source()
            #print(layerSource)
            if layerSource == source:
                treeLayerList.append(treeLayer)
                #print("matched layer")
            # else:
            #     print('Layer Source didnt match')

        return treeLayerList


