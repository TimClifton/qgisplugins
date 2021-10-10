import random
from time import sleep
from PyQt5.QtCore import QEvent, Qt, pyqtSignal
from itertools import chain
import os
from qgis.core import *

MESSAGE_CATEGORY = 'Layer Locator'

class FindIntersectingGeometriesTask(QgsTask):
    """This shows how to subclass QgsTask"""
    myObjectSignal = pyqtSignal(object)
    def __init__(self,  description, duration,  features, treeLayers):
        super().__init__(description, QgsTask.CanCancel)

        self.treeLayers = treeLayers
        self.duration = duration
        self.features = features      
        self.total = 0
        self.iterations = 0
        self.exception = None
        self.intersectingFeatures=[]
        QgsMessageLog.logMessage(f'Initialising task "{self.description()}" ', MESSAGE_CATEGORY, Qgis.Info)

    def run(self):
        """Here you implement your heavy lifting.
        Should periodically test for isCanceled() to gracefully
        abort.
        This method MUST return True or False.
        Raising exceptions will crash QGIS, so we handle them
        internally and raise them in self.finished
        """
        QgsMessageLog.logMessage(f'Started task "{self.description()}"', MESSAGE_CATEGORY, Qgis.Info)

        # a = False

        # if a:

        #     QgsMessageLog.logMessage(f'Returning', MESSAGE_CATEGORY, Qgis.Info)
        #     return False

        # else:

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
        return True

        # for treeLayer in self.treeLayers:

        #     tCheckedFeaturesGeometry = QgsGeometry(checkedFeaturesGeometry)

        #     layer = treeLayer.layer()

        #     if layer.type() != QgsMapLayerType.VectorLayer:
        #         continue

        #     geometryType = layer.geometryType()
        #     layerCRSID = layer.sourceCrs().authid()

        #     checkedFeaturesCRSID = selectedLayer.sourceCrs().authid()

        #     #print(f'Layer CRS {layerCRSID}. Checked layer CRS {checkedFeaturesCRSID} ')

        #     tCheckedFeaturesGeometry.transform(QgsCoordinateTransform(QgsCoordinateReferenceSystem(checkedFeaturesCRSID),QgsCoordinateReferenceSystem(layerCRSID),QgsProject.instance()))

        #     self.checkGeometry=tCheckedFeaturesGeometry.buffer(bufferDistance,36)

        #     tempLayer = None
        #     uri= None
        #     if geometryType == QgsWkbTypes.PolygonGeometry:

        #         #print(geometryType)
        #         uri = f'polygon?crs={layerCRSID}'

        #     elif geometryType == QgsWkbTypes.LineGeometry:

        #         #print(geometryType)
        #         uri = f'linestring?crs={layerCRSID}'

        #     elif geometryType == QgsWkbTypes.PointGeometry:

        #         #print(geometryType)
        #         uri = f'point?crs={layerCRSID}'

        #     if uri:

        #         layerFields = layer.dataProvider().fields()

        #         layerStyle = QgsMapLayerStyle()
        #         layerStyle.readFromLayer(layer)
                
        #         layerFeatures = list(layer.getFeatures())

        #         self.features = list(self.layer.getFeatures())

        #         increment = 100/len(self.features)

        #     QgsMessageLog.logMessage(f'Feature length is "{len(self.features)}" ', MESSAGE_CATEGORY, Qgis.Info)

        #     for i in range(0,len(self.features)):

        #         QgsMessageLog.logMessage(f'Checking Feature "{i}". Geometry is{str(self.features[i].geometry())} ', MESSAGE_CATEGORY, Qgis.Info)

        #         if self.checkGeometry.intersects(self.features[i].geometry()):
        #             #QgsMessageLog.logMessage(f'Adding Feature "{i}" ', MESSAGE_CATEGORY, Qgis.Info)
        #             self.intersectingFeatures.append(self.features[i])

        #         self.setProgress(i*increment)
                
        #         if self.isCanceled():
        #             return False

                    
        # self.myObjectSignal.emit(self)
        # return True

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
        if result:
            QgsMessageLog.logMessage(
                'RandomTask "{name}" completed\n' \
                'RandomTotal: {total} (with {iterations} '\
              'iterations)'.format(
                  name=self.description(),
                  total=self.total,
                  iterations=self.iterations),
              MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                
                QgsMessageLog.logMessage(
                    'RandomTask "{name}" not successful but without '\
                    'exception (probably the task was manually '\
                    'canceled by the user)'.format(
                    name=self.description()),
                    MESSAGE_CATEGORY, Qgis.Warning)
            
            else:
                QgsMessageLog.logMessage(
                    'RandomTask "{name}" Exception: {exception}'.format(
                        name=self.description(),
                        exception=self.exception),
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

    def cancel(self):
        QgsMessageLog.logMessage(
            'RandomTask "{name}" was canceled'.format(
                name=self.description()),
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()


