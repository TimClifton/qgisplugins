import random
from time import sleep
from PyQt5.QtCore import QEvent, Qt, pyqtSignal
from itertools import chain
import os
from qgis.core import (QgsApplication, QgsTask, QgsMessageLog, Qgis)
import ntpath
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

MESSAGE_CATEGORY = 'Layer Locator'

class RandomIntegerSumTask(QgsTask):
    mySignal = pyqtSignal(int)
    myListSignal = pyqtSignal(list)
    myObjectSignal = pyqtSignal(object)
    """This shows how to subclass QgsTask"""
    def __init__(self, description, duration):
        super().__init__(description, QgsTask.CanCancel)
        self.duration = duration
        self.total = 0
        self.iterations = 0
        self.exception = None
        self.specialValue=0
        self.list = ["value 1","value 2", "value 3"]
        

    def run(self):
        """Here you implement your heavy lifting.
        Should periodically test for isCanceled() to gracefully
        abort.
        This method MUST return True or False.
        Raising exceptions will crash QGIS, so we handle them
        internally and raise them in self.finished
        """
        QgsMessageLog.logMessage('Started task "{}"'.format(
                                      self.description()),
                                  MESSAGE_CATEGORY, Qgis.Info)
        self.iD = QgsApplication.taskManager().taskId(self)
        #print("running task")
        wait_time = self.duration / 100
        for i in range(100):
            sleep(wait_time)
            # use setProgress to report progress
            self.setProgress(i)
            arandominteger = random.randint(0, 500)
            self.total += arandominteger
            self.iterations += 1
            # check isCanceled() to handle cancellation
            if self.isCanceled():
                return False
            # simulate exceptions to show how to abort task
            if arandominteger == 42:
                # DO NOT raise Exception('bad value!')
                # this would crash QGIS
                self.exception = Exception('bad value!')
                return False
        QgsMessageLog.logMessage(f'Task is finishing',
                                  MESSAGE_CATEGORY, Qgis.Info)
        #QgsMessageLog.logMessage(f'Total value is {self.total}',MESSAGE_CATEGORY, Qgis.Info)

        self.specialValue = self.iterations

        self.mySignal.emit(self.total)
        self.myListSignal.emit(self.list)
        self.myObjectSignal.emit(self)
        return True
        #self.taskCompleted.emit()
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
        QgsMessageLog.logMessage(f'Running finished', MESSAGE_CATEGORY, Qgis.Info)
        if result:
            QgsMessageLog.logMessage(
                'Task "{name}" completed\n' \
                'Total: {total} (with {iterations} '\
              'iterations)'.format(
                  name=self.description(),
                  total=self.total,
                  iterations=self.iterations),
              MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Task "{name}" not successful but without '\
                    'exception (probably the task was manually '\
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


class locateLayerSources(QgsTask):

    myObjectSignal = pyqtSignal(object)
    """This shows how to subclass QgsTask"""
    def __init__(self, _description, _dockWidget,_iterator,_treeViewModel,_totalFiles):
        super().__init__(_description, QgsTask.CanCancel)
        #self.duration = _duration
        self.total = 0
        self.iterations = 0
        self.exception = None
        self.dockWidget=_dockWidget
        self.iterator = _iterator
        self.treeViewModel=_treeViewModel
        self.foundSources=[]
        self.totalFiles=_totalFiles
        self.layerId = self.treeViewModel.index(self.iterator,3).data()


    def run(self):
        """Here you implement your heavy lifting.
        Should periodically test for isCanceled() to gracefully
        abort.
        This method MUST return True or False.
        Raising exceptions will crash QGIS, so we handle them
        internally and raise them in self.finished
        """
        QgsMessageLog.logMessage('Started task "{}"'.format(
                                      self.description()),
                                  MESSAGE_CATEGORY, Qgis.Info)
        
        searchDirectories = self.dockWidget.locatorSearchDirectoriesTextEdit.toPlainText().split("\n")
        ignoreFolders=self.dockWidget.locatorIgnoreFoldersTextEdit.toPlainText().split("\n")
        missingSource = self.treeViewModel.index(self.iterator,1).data()
        missingSourceFullFileName=ntpath.basename(missingSource)
        missingSourceExt = os.path.splitext(missingSourceFullFileName)[1]
        self.progressCount=0
        
        #self.totalFiles = sum([len(files) for r, d, files in chain.from_iterable(os.walk(path) for path in searchDirectories)])

        stepRatio =100

        if self.totalFiles<40000:
            stepRatio = self.translate(self.totalFiles,0,40000,.001,50)

        #stepRatio =.01
        step = self.totalFiles//stepRatio

        sleepTime =0

        # if self.totalFiles<5000:
        #     sleepTime = self.translate(self.totalFiles,0,5000,.000001,0.0)
        
        QgsMessageLog.logMessage(f'Task sleep time is {sleepTime}', MESSAGE_CATEGORY, Qgis.Info)

        for roots, dirs, files in chain.from_iterable(os.walk(path) for path in searchDirectories):

            dirs[:] = [d for d in dirs if d not in ignoreFolders]

            #index = self.treeViewModel.index(self.iterator, 2)
            
            for file in files:
                self.checkRowLayerId()

                sleep(sleepTime)
                if self.isCanceled():
                    return False

                self.progressCount = self.progressCount+1
                if step == 0 or self.progressCount % step == 0:
                    #QgsMessageLog.logMessage(f'Updating Progress', MESSAGE_CATEGORY, Qgis.Info)
                    self.setProgress(
                        100*self.progressCount/self.totalFiles)

                if not self.dockWidget.locatorAllowDifferentExtensionsCheckbox.isChecked():
                    fileExt = os.path.splitext(file)[1]
                    if not missingSourceExt == fileExt:
                        continue
                #QgsMessageLog.logMessage(f'Check Status {self.dockWidget.locatorAllowFuzzyMatchCheckbox.isChecked()}', MESSAGE_CATEGORY, Qgis.Info)
                if self.dockWidget.locatorAllowFuzzyMatchCheckbox.isChecked():
                    ratio = fuzz.ratio(missingSourceFullFileName, file)
                    #QgsMessageLog.logMessage(f'Ratio is {ratio}', MESSAGE_CATEGORY, Qgis.Info)
                    if ratio > self.dockWidget.locatorFuzzyMatchSlider.value():
                        sourceItem = [roots+"\\"+file, ratio]
                        self.foundSources.append(sourceItem)
                else:
                    if missingSourceFullFileName == file:
                        sourceItem = [roots+"\\"+file, "NA"]

                        self.foundSources.append(sourceItem)
        self.taskId = QgsApplication.taskManager().taskId(self)
        QgsMessageLog.logMessage(f'Task is finishing task {self.taskId}', MESSAGE_CATEGORY, Qgis.Info)


        self.myObjectSignal.emit(self)


        return True
        #self.taskCompleted.emit()

    def translate(self,value, leftMin, leftMax, rightMin, rightMax):
        # Figure out how 'wide' each range is
        leftSpan = leftMax - leftMin
        rightSpan = rightMax - rightMin

        # Convert the left range into a 0-1 range (float)
        valueScaled = float(value - leftMin) / float(leftSpan)

        # Convert the 0-1 range into a value in the right range.
        return rightMin + (valueScaled * rightSpan)

    def checkRowLayerId(self):
        if self.treeViewModel.index(self.iterator,3).data() == self.layerId:
            return True
        else:
            for i in range(self.treeViewModel.rowCount()):
                id = self.treeViewModel.index(i,3).data()
                if id == self.layerId:
                    self.iterator=i

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
        QgsMessageLog.logMessage(f'Running finished', MESSAGE_CATEGORY, Qgis.Info)
        if result:
            QgsMessageLog.logMessage(
                'Task "{name}" completed\n' \
                'Total: {total} (with {iterations} '\
              'iterations)'.format(
                  name=self.description(),
                  total=self.total,
                  iterations=self.iterations),
              MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Task "{name}" not successful but without '\
                    'exception (probably the task was manually '\
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

class calculateFilesInDirectories(QgsTask):

    getTotalFiles = pyqtSignal(int)

    """This shows how to subclass QgsTask"""
    def __init__(self, _description, _dockWidget):
        super().__init__(_description, QgsTask.CanCancel)
        #self.duration = _duration
        self.total = 0
        self.iterations = 0
        self.exception = None
        self.dockWidget=_dockWidget
        self.totalFiles = 0

    def run(self):
        """Here you implement your heavy lifting.
        Should periodically test for isCanceled() to gracefully
        abort.
        This method MUST return True or False.
        Raising exceptions will crash QGIS, so we handle them
        internally and raise them in self.finished
        """
        QgsMessageLog.logMessage('Started task "{}"'.format(self.description()),MESSAGE_CATEGORY, Qgis.Info)
        
        searchDirectories = self.dockWidget.locatorSearchDirectoriesTextEdit.toPlainText().split("\n")
        ignoreFolders=self.dockWidget.locatorIgnoreFoldersTextEdit.toPlainText().split("\n")

        self.totalFiles = sum([len(files) for r, d, files in chain.from_iterable(os.walk(path) for path in searchDirectories)])

        self.getTotalFiles.emit(self.totalFiles)

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
        QgsMessageLog.logMessage(f'Running finished', MESSAGE_CATEGORY, Qgis.Info)
        if result:
            QgsMessageLog.logMessage(
                'Task "{name}" completed\n' \
                'Total: {total} (with {iterations} '\
              'iterations)'.format(
                  name=self.description(),
                  total=self.total,
                  iterations=self.iterations),
              MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Task "{name}" not successful but without '\
                    'exception (probably the task was manually '\
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
