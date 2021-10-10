import os

from PyQt5.QtWidgets import QFileDialog

from .comparer_core import DirectoryComparerCore as core





class DirectoryComparerGui:

    def __init__(self, _dockwidget):

        self.dockwidget = _dockwidget

        self.originalDirectory = None
        self.comparisonDirectory = None

        #self.core = DirectoryComparerCore()





        self.guiInitialize()


    



    def guiInitialize (self):

        #Connect listeners
        self.dockwidget.Comparer_SelectOriginalDirectory_PushButton.clicked.connect(self.selectOriginalDirectory)
        self.dockwidget.Comparer_SelectComparisonDirectory_PushButton.clicked.connect(self.selectComparisonDirectory)
        self.dockwidget.DC_Compare_Pushbutton.clicked.connect(self.compareFiles)
        




    def selectOriginalDirectory(self):
        """ Open a dialog for the user to choose a starting directory """
        print('here')

        if not self.dockwidget.Comparer_OriginalDirectory_LineEdit.text():
            opendirectory = '/home'

        elif not os.path.isdir(self.dockwidget.Comparer_OriginalDirectory_LineEdit.text()):
            opendirectory = '/home'

        else:
            opendirectory = self.dockwidget.Comparer_OriginalDirectory_LineEdit.text()



        directory = QFileDialog.getExistingDirectory(self.dockwidget, 'Select original directory', opendirectory, QFileDialog.ShowDirsOnly)
        directory = os.path.abspath(directory)

        self.dockwidget.Comparer_OriginalDirectory_LineEdit.setText(directory)
        self.directory = directory

        #return directory

    def selectComparisonDirectory( self ):
        """ Open a dialog for the user to choose a starting directory """
        print('here')

        if not self.dockwidget.Comparer_ComparisonDirectory_LineEdit.text():
            opendirectory = '/home'

        elif not os.path.isdir(self.dockwidget.Comparer_ComparisonDirectory_LineEdit.text()):
            opendirectory = '/home'

        else:
            opendirectory = self.dockwidget.Comparer_ComparisonDirectory_LineEdit.text()



        directory = QFileDialog.getExistingDirectory(self.dockwidget, 'Select comparison directory', opendirectory, QFileDialog.ShowDirsOnly)
        directory = os.path.abspath(directory)

        self.dockwidget.Comparer_ComparisonDirectory_LineEdit.setText(directory)
        self.comparisonDirectory = directory
       
        #return directory


    def compareFiles (self):

        self.originalDirectory = self.dockwidget.Comparer_OriginalDirectory_LineEdit.text()
        self.comparisonDirectory = self.dockwidget.Comparer_ComparisonDirectory_LineEdit.text()


        if self.originalDirectory is None or not os.path.isdir(self.originalDirectory):

            return

        if self.comparisonDirectory is None or not os.path.isdir(self.comparisonDirectory):

            return

        self.core = core(self.originalDirectory,self.comparisonDirectory)

    
        log = self.core.compareFiles()

        for item in log:

            print(item)


