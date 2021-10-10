import os
import datetime
import qgis.core
import re
from operator import itemgetter, attrgetter, methodcaller
#from .layer_importer_dockwidget import LayerImporterDockWidget
import PyQt5


class shpProcessedFileName:

    def __init__(self, _path, _fullName ):
        print(f"Processing Path {_path}")
        self.path = _path
        self.fullName = _fullName
        self.shortName = os.path.splitext(self.fullName)[0]
        self.ext = os.path.splitext(self.fullName)[1]


        regA = re.compile('(?P<name>\S*)_[vV](?P<majorversion>\d{2})-(?P<minorversion>\d{2})_*(?P<suffix>\S*).shp\Z')
        result = regA.match(self.fullName)
        if result is not None:
            self.version = 'v'+result.group('majorversion')+'-'+result.group('minorversion')
            self.versionNum = int(result.group('majorversion')+result.group('minorversion'))
            self.disciplineName = result.group('name')
            self.additionalInfo = result.group('suffix')
            """ The node that the layer is going to be added to """
            self.layerGroup = None
            self.layerStyle = None
        else:
            print("Result no valid")