from qgis.core import *
import os
import ntpath
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from .helperclasses.shpProcessedFileName import shpProcessedFileName
import re
from itertools import chain
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import datetime
import time
import random
from .helperclasses.tasks import RandomIntegerSumTask, locateLayerSources, calculateFilesInDirectories
import multiprocessing

MESSAGE_CATEGORY = 'Layer Locator'
MESSAGE_CATEGORY_DEBUG = 'Layer Locator Debug'

class LocatorGui:

    def __init__(self,_dockWidget):
        print("Starting Locator")
        self.vectorPath = None
        self.project = QgsProject.instance()
        
        self.dockWidget = _dockWidget
        self.treeView = self.dockWidget.locatorTreeView
        self.setProgressBarStart()
        self.populateMissingFiles()

        self.dockWidget.locatorFuzzyMatchSlider.valueChanged.connect(self.handleSliderUpdate)

        self.dockWidget.locatorAllowFuzzyMatchCheckbox.stateChanged.connect(self.handleFuzzyMatchingCheckbox)

        self.dockWidget.locatorRefreshButton.clicked.connect(self.populateMissingFiles)
        self.dockWidget.pushButton_2.clicked.connect(self.testing)

        self.dockWidget.pushButton_3.clicked.connect(self.testing2)

        self.dockWidget.locateSourcesButton.clicked.connect(self.locateMissingFiles)
        self.dockWidget.updateSourcesButton.clicked.connect(self.updateSources)

        self.handleFuzzyMatchingCheckbox()
        
        self.readSettings()
        
        self.taskIds=[]

        self.completedTaskInfo=[]
        self.completedTaskCount=0
        self.dockWidget.locatorThreadCountSpinBox.setMaximum(multiprocessing.cpu_count())
        #self.consecutiveTaskLimit = self.dockWidget.locatorThreadCountSpinBox.value()
        



    def taskStatusChanged(self, taskId, status):

        changedTask=QgsApplication.taskManager().task(taskId)
        string = str(changedTask.description())
        if not "Locator Row" in string:
            return

        onholdTasks = [task for task in QgsApplication.taskManager().tasks() if task.status()==1]

        for t in onholdTasks:
            queuedTaskCount = len([task for task in QgsApplication.taskManager().tasks() if task.status()==0])
            runningTaskCount = len([task for task in QgsApplication.taskManager().tasks() if task.status()==2])
            combinedTaskCount= queuedTaskCount + runningTaskCount
            if combinedTaskCount<self.dockWidget.locatorThreadCountSpinBox.value():
                #QgsMessageLog.logMessage(f"Releasing Task {t.description()}",MESSAGE_CATEGORY, Qgis.Info)
                t.unhold()
            else:
                break

        if status == 3:
            #QgsMessageLog.logMessage(f'Status {status} Completed Task Count BEFORE {self.completedTaskCount}',MESSAGE_CATEGORY_DEBUG, Qgis.Info)
            self.completedTaskCount = self.completedTaskCount +1
            #QgsMessageLog.logMessage(f'Completed Task Count AFTER {self.completedTaskCount}',MESSAGE_CATEGORY_DEBUG, Qgis.Info)
            for info in self.completedTaskInfo:
                infoId = info['taskId']

                if infoId == taskId:
                    self.updateLocateMissingFilesGui(info)
                    self.completedTaskInfo.remove(info)
                    self.dockWidget.repaint()

        else:
            return

 

    def printer(self,value):
        #print('here is the value')
        #print(value)
        self.dockWidget.progressBar_2.setValue(value)

    def handleSignal(self,value):
        QgsMessageLog.logMessage(f'From my signal the total is {value}',MESSAGE_CATEGORY, Qgis.Info)

    def handleListSignal(self,value):
        #QgsMessageLog.logMessage(f'From my listSignal the value is {value}',MESSAGE_CATEGORY, Qgis.Info)
        return value

    def handleObjectSignal(self,task):

        info={'foundSources':task.foundSources,'iterator':task.iterator,'taskId' :task.taskId}
        self.completedTaskInfo.append(info)


    def allTasksFinished(self):
        self.dockWidget.locateSourcesButton.setText("Locate Missing Sources")
        QgsMessageLog.logMessage(f'Disconnecting tasks from all tasks finished',MESSAGE_CATEGORY_DEBUG, Qgis.Info)
        try:
            QgsApplication.taskManager().statusChanged.disconnect()
            QgsApplication.taskManager().progressChanged.disconnect()
            QgsApplication.taskManager().allTasksFinished.disconnect()
            self.dockWidget.locatorProgressBar.valueChanged.disconnect()
            QgsApplication.taskManager().cancelAll()
        except TypeError:
            pass

    def remainingTimeEstimator(self,progressBarValue):
        
        if progressBarValue==0:

            self.dockWidget.timeEstimateLabel.setText(f"Estimating...")
        else:
            currentTime = time.time()
            elapsed = currentTime-self.locateFilesStart

            estimate = round((elapsed/progressBarValue*100) - elapsed,1)
            if estimate <0:
                estimate =0
            self.dockWidget.timeEstimateLabel.setText(f"{estimate}s")

    def taskManagerProgressChanged(self,taskId, progress):

        changedTask=QgsApplication.taskManager().task(taskId)
        string = str(changedTask.description())
        if not "Locator Row" in string:
            return

        layerId = changedTask.layerId

        for i in range(self.treeViewModel.rowCount()):
            id = self.treeViewModel.index(i,3).data()
            if id == layerId:
                index = self.treeViewModel.index(i,2)
                break

        self.treeViewModel.setData(index,f"{changedTask.progressCount}/{changedTask.totalFiles}")

        currentProgress = self.completedTaskCount*100/self.newTaskCount

        bulkAdditionalProgress =0

        for task in QgsApplication.taskManager().tasks():
            bulkAdditionalProgress = task.progress()+bulkAdditionalProgress

        additionalProgress = bulkAdditionalProgress/(self.newTaskCount)

        cumulativeProgress= currentProgress +additionalProgress

        #QgsMessageLog.logMessage(f'Updating progressbar : {cumulativeProgress} and {additionalProgress} count is {self.newTaskCount}',MESSAGE_CATEGORY, Qgis.Info)
        self.dockWidget.locatorProgressBar.setValue(cumulativeProgress)

    def testing2(self):
        #QgsMessageLog.logMessage(f'From my object signal the total is {self.myTask.total}',MESSAGE_CATEGORY, Qgis.Info)
        self.dockWidget.progressBar_2.setValue(0)

    def testing(self):
        print("testing")



    def handleSliderUpdate(self):
        value = self.dockWidget.locatorFuzzyMatchSlider.value()
        self.dockWidget.locatorFuzzyMatchLabel.setText(str(value))

    def handleFuzzyMatchingCheckbox(self,state=Qt.CheckState.Unchecked):
        print(state)
        if not self.dockWidget.locatorAllowFuzzyMatchCheckbox.isChecked():
            print("hiding")
            self.dockWidget.locatorFuzzyMatchLabel.hide()
            self.dockWidget.locatorFuzzyMatchSlider.hide()


        elif self.dockWidget.locatorAllowFuzzyMatchCheckbox.isChecked():
            self.dockWidget.locatorFuzzyMatchLabel.show()
            self.dockWidget.locatorFuzzyMatchSlider.show()

    def updateSources(self):
        print("updating sources")
        self.updateProgressBarLabel("Updating Layer Sources")

        duplicateFiles = False

        for i in range(self.treeViewModel.rowCount()):
            item = self.treeViewModel.item(i)
            if item.hasChildren():
                duplicateFiles=True
                break
        sourceUpdated = False
        if duplicateFiles:
            val = self.showDialog("Have you checked the sources properly?","This cannot be undone")
            print(val)
            if val == 65536:
                self.updateProgressBarLabel("Please revise the sources")
            else:
                
                for i in range(self.treeViewModel.rowCount()):
                    itemUpdated=False
                    index = self.treeViewModel.index(i,3)
                    layerId = self.treeViewModel.data(index)
                    #print(layerId)
                    item = self.treeViewModel.item(i)
                    #print(f"The row count is {item.rowCount()}")
                    if item.rowCount() > 0:
                        
                        for j in range(item.rowCount()):

                            if itemUpdated:
                                break
                            checkState=item.takeChild(j,0).checkState()
                            print(f"the Check state is {checkState}")
                            
                            if checkState == 2:
                                itemUpdated=True
                                sourceUpdated = True
                                newSource = item.takeChild(j,1).text()
                                treeLayers = self.project.layerTreeRoot().findLayers()
                                for treeLayer in treeLayers:
                                    if treeLayer.layerId() == layerId:
                                        source=treeLayer.layer().source()
                                        providerName = treeLayer.layer().dataProvider().name()
                                        
                                        treeLayer.layer().setDataSource(newSource,treeLayer.layer().name(),providerName)

                    else:
                        print("too many sources found")
        self.updateProgressBarLabel("Layer Sources Updated")
        if sourceUpdated:
            self.populateMissingFiles()




    def addLocateMissingFilesTasks(self,totalFiles):
        #self.setProgressBarStart()
        self.totalFilesInDirectories = totalFiles
        #QgsMessageLog.logMessage(f'Total Files is {totalFiles}',MESSAGE_CATEGORY, Qgis.Info)
        self.setProgressBarStart()
        foundFilesCount=0
        self.newTaskCount = 0
        self.tasksToBeManaged = []
        self.completedTaskInfo=[]
        self.completedTaskCount = 0

        QgsApplication.taskManager().statusChanged.connect(self.taskStatusChanged)
        QgsApplication.taskManager().progressChanged.connect(self.taskManagerProgressChanged)
        QgsApplication.taskManager().allTasksFinished.connect(self.allTasksFinished)



        self.locateFilesStart = time.time()

        for i in range(self.treeViewModel.rowCount()):

            locateSourceTask = locateLayerSources(f'Locator Row {i}',self.dockWidget,i,self.treeViewModel,self.totalFilesInDirectories)
            locateSourceTask.hold()
            #QgsMessageLog.logMessage(f"Task status{locateSourceTask.status()}",MESSAGE_CATEGORY, Qgis.Info)

            locateSourceTask.myObjectSignal.connect(self.handleObjectSignal)

            self.tasksToBeManaged.append(locateSourceTask)
            QgsApplication.taskManager().addTask(locateSourceTask)
            
            self.newTaskCount = self.newTaskCount+1


        onholdTasks = [task for task in QgsApplication.taskManager().tasks() if task.status()==1]

        for t in onholdTasks:
            queuedTaskCount = len([task for task in QgsApplication.taskManager().tasks() if task.status()==0])
            runningTaskCount = len([task for task in QgsApplication.taskManager().tasks() if task.status()==2])
            combinedTaskCount= queuedTaskCount + runningTaskCount
            if combinedTaskCount<self.dockWidget.locatorThreadCountSpinBox.value():
                #QgsMessageLog.logMessage(f"Releasing Task {t.description()}",MESSAGE_CATEGORY, Qgis.Info)
                t.unhold()


    def locateMissingFiles(self):
        if QgsApplication.taskManager().countActiveTasks()>0:
            self.dockWidget.locateSourcesButton.setText("Please Wait...")
            return

        self.completedTaskCount=0
        self.taskIds=[]
        self.completedTaskInfo=[]
        self.newTaskCount = 0
        self.tasksToBeManaged = []



        self.dockWidget.locatorProgressBar.valueChanged.connect(self.remainingTimeEstimator)
        self.dockWidget.timeEstimateLabel.setText(f"Estimating...")

        self.totalFilesInDirectories=0
        #print('locating Missing files')
        self.updateProgressBarLabel("Locating Missing Files")

        searchDirectories = self.dockWidget.locatorSearchDirectoriesTextEdit.toPlainText().split("\n")
        ignoreFolders=self.dockWidget.locatorIgnoreFoldersTextEdit.toPlainText().split("\n")

        self.setProgressBarBusy()

        calculateFilesTask = calculateFilesInDirectories("TotalFiles",self.dockWidget)
        calculateFilesTask.getTotalFiles.connect(self.addLocateMissingFilesTasks)

        #QgsMessageLog.logMessage("Adding find file source task",MESSAGE_CATEGORY, Qgis.Info)

        locateSourceTask = locateLayerSources(f'Locator Row {1}',self.dockWidget,1,self.treeViewModel,self.totalFilesInDirectories)

        QgsApplication.taskManager().addTask(calculateFilesTask)
        QgsMessageLog.logMessage("Task Added",MESSAGE_CATEGORY, Qgis.Info)

        #self.totalFilesInDirectories = sum([len(files) for r, d, files in chain.from_iterable(os.walk(path) for path in searchDirectories)])





        
        
    
    def updateLocateMissingFilesGui(self,_info):
        #time.sleep(0.01)
        #QgsMessageLog.logMessage(f'Updating the Gui',MESSAGE_CATEGORY_DEBUG, Qgis.Info)
        foundSources = _info['foundSources']
        i = _info['iterator']
        index = self.treeViewModel.index(i,2)
        foundFilesCount =0
        #QgsMessageLog.logMessage(f'found {len(foundSources)} sources',MESSAGE_CATEGORY_DEBUG, Qgis.Info)
        if len(foundSources) >0:
            self.treeViewModel.setData(index,f"Found {len(foundSources)}")
            item = self.treeViewModel.item(i)

            if item.hasChildren():
                print(f"Root item has {item.rowCount()} rows")
                item.removeRows(0,item.rowCount())
                print(f"Now there are {item.rowCount()} rows")

            firstElement=True

            foundSources.sort(key=lambda x: x[1],reverse=True)

            for element in foundSources:
                

                newItem=QStandardItem(0,0)
                newItem_2 = QStandardItem(0,1)
                newItem.setCheckable(True)
                newItem.setEditable(False)
                newItem_2.setEditable(False)
                if firstElement is True:
                    newItem.setCheckState(2)
                    firstElement = False

                newItem.setData(ntpath.basename(element[0]),Qt.DisplayRole)
                newItem_2.setData( element[0],Qt.DisplayRole)
                newItem_2.setEditable(False)

                newItem.setToolTip(ntpath.basename(element[0]))
                newItem_2.setToolTip(element[0])

                row=[newItem,newItem_2]

                if self.dockWidget.locatorAllowFuzzyMatchCheckbox.isChecked():
                    newItem_3 = QStandardItem(0,2)
                    newItem_3.setData( element[1],Qt.DisplayRole)
                    newItem_3.setEditable(False)
                    row.append(newItem_3)

                item.appendRow(row)
                foundFilesCount=foundFilesCount +1
            if not item.hasChildren():
                QgsMessageLog.logMessage(f'ADDING ROW FAILED!!!',MESSAGE_CATEGORY_DEBUG, Qgis.Info)
                #self.updateLocateMissingFilesGui(_info)
            

        else:
            self.treeViewModel.setData(index,"Still Missing")
    
        #self.setProgressBarComplete()
        self.updateProgressBarLabel(f"Complete. {foundFilesCount} matches for {self.treeViewModel.index(i,0).data()} ")


    def locateMissingFiles_old(self):
        print('locating Missing files')
        self.updateProgressBarLabel("Locating Missing Files")
        #if self.dockWidget.locatorSearchDirectoriesTextEdit.toPlainText
        searchDirectories = self.dockWidget.locatorSearchDirectoriesTextEdit.toPlainText().split("\n")
        ignoreFolders=self.dockWidget.locatorIgnoreFoldersTextEdit.toPlainText().split("\n")
        self.setProgressBarBusy()
        foundFilesCount=0

        for i in range(self.treeViewModel.rowCount()):
            missingSource = self.treeViewModel.index(i,1).data()
            missingSourceFullFileName=ntpath.basename(missingSource)
            missingSourceExt = os.path.splitext(missingSourceFullFileName)[1]
            #walkData = os.walk(vectorDataPath, topdown=True)
            foundSources =[]
            count = 0
            self.updateProgressBarLabel(f"Searching for file {self.treeViewModel.index(i,0).data()}")
            for roots, dirs, files in chain.from_iterable(os.walk(path) for path in searchDirectories):

                dirs[:] = [d for d in dirs if d not in ignoreFolders]

                index = self.treeViewModel.index(i,2)

                for file in files:
                    count = count+1

                    if not self.dockWidget.locatorAllowDifferentExtensionsCheckbox.isChecked():
                        fileExt=os.path.splitext(file)[1]
                        if not missingSourceExt == fileExt:
                            continue


                    if self.dockWidget.locatorAllowFuzzyMatchCheckbox.isChecked():
                        ratio = fuzz.ratio(missingSourceFullFileName, file)
                        if ratio>self.dockWidget.locatorFuzzyMatchSlider.value():
                            sourceItem = [roots+"\\"+file,ratio]
                            foundSources.append(sourceItem)
                    else:
                        if missingSourceFullFileName == file:
                            sourceItem = [roots+"\\"+file,"NA"]

                            foundSources.append(sourceItem)

                        
            if len(foundSources) >0:
                self.treeViewModel.setData(index,f"Found {len(foundSources)}")
                item = self.treeViewModel.item(i)

                if item.hasChildren():
                    print(f"Root item has {item.rowCount()} rows")
                    item.removeRows(0,item.rowCount())
                    print(f"Now there are {item.rowCount()} rows")

                firstElement=True

                foundSources.sort(key=lambda x: x[1],reverse=True)

                for element in foundSources:
                    

                    newItem=QStandardItem(0,0)
                    newItem_2 = QStandardItem(0,1)
                    newItem.setCheckable(True)
                    newItem.setEditable(False)
                    newItem_2.setEditable(False)
                    if firstElement is True:
                        newItem.setCheckState(2)
                        firstElement = False

                    newItem.setData(ntpath.basename(element[0]),Qt.DisplayRole)
                    newItem_2.setData( element[0],Qt.DisplayRole)
                    newItem_2.setEditable(False)

                    newItem.setToolTip(ntpath.basename(element[0]))
                    newItem_2.setToolTip(element[0])

                    row=[newItem,newItem_2]

                    if self.dockWidget.locatorAllowFuzzyMatchCheckbox.isChecked():
                        newItem_3 = QStandardItem(0,2)
                        newItem_3.setData( element[1],Qt.DisplayRole)
                        newItem_3.setEditable(False)
                        row.append(newItem_3)

                    item.appendRow(row)
                    foundFilesCount=foundFilesCount +1
                    
            else:
                self.treeViewModel.setData(index,"Still Missing")
        self.setProgressBarComplete()
        self.updateProgressBarLabel(f"File searching complete. {foundFilesCount} missing files were located for {self.treeViewModel.rowCount()} layers")

    def updateProgressBarLabel(self,text):
        self.dockWidget.locatorProgessBarLabel.setText(text)
        now=datetime.datetime.now()
        self.dockWidget.locatorLogTextEdit.append("{:<70} {:>0s}".format(text,f"{now}"))

    def populateMissingFiles(self):
        missingFileTreeLayers = self.findMissingFiles()
        self.treeViewModel = self.createModel(missingFileTreeLayers)
        self.treeView.setModel(self.treeViewModel)
        self.treeView.setSortingEnabled(True)
        self.updateProgressBarLabel(f"{self.treeViewModel.rowCount()} layers were found with missing files")

    def findMissingFiles(self):
        self.updateProgressBarLabel("Finding layers with missing sources")
        missingFileTreeLayers =[]
        treeLayers = self.project.layerTreeRoot().findLayers()

        for treeLayer in treeLayers:
            source=treeLayer.layer().source()
            cleanSource=source
            reg = re.compile('.*\..*(?=\|)')
            result = reg.match(source)
            if result:
                cleanSource = result[0]


            if not os.path.exists(cleanSource):
                missingFileTreeLayers.append(treeLayer)
                if result:
                    print(source)
                    print(result[0])
                    print(cleanSource)

        return missingFileTreeLayers

    def createModel(self,layerTrees):
        print("creating model")
        #itemModel = myItemModel(0,4,self.treeView)
        itemModel=QStandardItemModel(0, 4, self.treeView)
        #itemModel.setFlags(Qt.NoItemFlags)
        itemModel.setHeaderData(0, Qt.Horizontal, "Layer Name")
        itemModel.setHeaderData(1, Qt.Horizontal, "Layer Source")
        itemModel.setHeaderData(2, Qt.Horizontal, "Status")
        itemModel.setHeaderData(3, Qt.Horizontal, "LayerId")

        for layerTree in layerTrees:
            name = layerTree.name()
            source = layerTree.layer().source()
            reg = re.compile('.*\..*(?=\|)')
            result = reg.match(source)

            if result:
                source = result[0]
            
            layerId = layerTree.layerId()

            itemModel.insertRow(0)
            itemModel.setData(itemModel.index(0, 0), name)
            itemModel.item(0,0).setFlags(Qt.ItemIsEnabled )
            itemModel.item(0,0).setToolTip(name)

            itemModel.setData(itemModel.index(0, 1), source)
            itemModel.item(0,1).setFlags(Qt.ItemIsEnabled and Qt.ItemIsSelectable)
            itemModel.item(0,1).setToolTip(source)

            itemModel.setData(itemModel.index(0, 2), "Not Found")
            itemModel.item(0,2).setFlags(Qt.ItemIsEnabled and Qt.ItemIsSelectable)

            itemModel.setData(itemModel.index(0, 3), layerId)
            itemModel.item(0,3).setFlags(Qt.ItemIsEnabled and Qt.ItemIsSelectable)
        
        return itemModel
            #data=[name,source,"Not Found",layerId]
            #dataList.append(data)

    def showDialog(self,text_1,text_2):
        print("showing dialog")
        #msg = QMessageBox.question(self.dockWidget, text_1,text_2,QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)

        msg.setText(text_1)
        msg.setInformativeText(text_2)
        msg.setWindowTitle("Warning")
        #msg.setDetailedText("The details are as follows:")
        #msg.addButton(QPushButton)
        msg.setStandardButtons(QMessageBox.Yes )
        msg.addButton(QMessageBox.No)
        #msg.buttonClicked.connect(msgbtn)
        retval = msg.exec_()
        print ("value of pressed message box button:", retval )
        return retval
        #if (retval==8192):

    def setProgressBarBusy(self):
        self.dockWidget.locatorProgressBar.setMinimum(0)
        self.dockWidget.locatorProgressBar.setMaximum(0)
        self.dockWidget.locatorProgressBar.setValue(0)

    def setProgressBarComplete(self):
        self.dockWidget.locatorProgressBar.setMinimum(0)
        self.dockWidget.locatorProgressBar.setMaximum(100)
        self.dockWidget.locatorProgressBar.setValue(100)

    def setProgressBarStart(self):
        self.dockWidget.locatorProgressBar.setMinimum(0)
        self.dockWidget.locatorProgressBar.setMaximum(100)
        self.dockWidget.locatorProgressBar.setValue(0)

    def storeSettings(self):
        s=QgsSettings()
        print("Storing Locator Settings")
        s.setValue("layerlocator/ignorefolders",self.dockWidget.locatorIgnoreFoldersTextEdit.toPlainText())
        s.setValue("layerlocator/searchdirectories",self.dockWidget.locatorSearchDirectoriesTextEdit.toPlainText())
        s.setValue("layerlocator/allowfuzzymatching",self.dockWidget.locatorAllowFuzzyMatchCheckbox.checkState())
        s.setValue("layerlocator/fuzzymatchingvalue",self.dockWidget.locatorFuzzyMatchSlider.value())
        s.setValue("layerlocator/asktoresolverduplicates",self.dockWidget.locatorResolveDuplicateFilesCheckbox.checkState())
    
    def readSettings(self):
        s=QgsSettings()
        print("Reading Locator Settings")
        self.dockWidget.locatorIgnoreFoldersTextEdit.setText(s.value("layerlocator/ignorefolders","workingFiles\nmapworkingData"))
        self.dockWidget.locatorSearchDirectoriesTextEdit.setText(s.value("layerlocator/searchdirectories","workingFiles\nmapworkingData"))
        self.dockWidget.locatorAllowFuzzyMatchCheckbox.setCheckState(int(s.value("layerlocator/allowfuzzymatching","0")))
        self.dockWidget.locatorFuzzyMatchSlider.setValue(int(s.value("layerlocator/fuzzymatchingvalue","100")))
        self.dockWidget.locatorResolveDuplicateFilesCheckbox.setCheckState(int(s.value("layerlocator/asktoresolverduplicates","0")))


class myItemModel (QStandardItemModel):
    def __init__(self, row, col, parent, *args):
        QAbstractItemModel.__init__(self,parent, *args)


    def data(self, index, role):
        row = index.row()
        col = index.column()
        #role = Qt.EditRole
        #print(role)
        if not index.isValid():
            return None

        elif role != Qt.DisplayRole:
            return None
            

        return self.mylist[row][col]


    def setData(self,index, value, role=Qt.EditRole):
        print("setting Data")
        if (not index.isValid() and role != Qt.EditRole):
            return false

        #self.mylist[index.row()][index.column()] = str(value)
        self.dataChanged.emit(index, index)
        return True






