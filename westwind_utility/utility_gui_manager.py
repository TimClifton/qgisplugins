import os
from .utility_core_dockwidget import UtilityDockWidget
from .layer_sourcechanger.sourcechanger_gui import SourceChangerGui
from .layer_importer.importer_gui import ImporterGui
from .layer_locator.locator_gui import LocatorGui
from .workspace_creator.ws_creator_gui import WSCreatorGui
from .westwindutilitysettings import WestWindUtilitySettings
from .directory_comparer.comparer_gui import DirectoryComparerGui
#from .mytreeview import mytreeview

class UtilityGuiManager:
    
    def __init__(self,_iface):
        self.iface=_iface

        self.dockWidget = UtilityDockWidget()
        self.importer = ImporterGui(self.dockWidget)
        self.sourcechanger_gui= SourceChangerGui(self.dockWidget,self.importer)
        self.locator = LocatorGui(self.dockWidget)
        self.wscreator = WSCreatorGui(self.dockWidget,self.iface)
        self.comparer = DirectoryComparerGui(self.dockWidget)
        self.settings = WestWindUtilitySettings(self.dockWidget)
        


