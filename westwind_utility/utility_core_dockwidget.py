# -*- coding: utf-8 -*-
"""
/***************************************************************************
 WWEutilityDockWidget
                                 A QGIS plugin
 Plugin to simply task at Westwind
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-07-12
        git sha              : $Format:%H$
        copyright            : (C) 2019 by T Clifton
        email                : tclifton3330@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import sys
from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, Qt

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__),'bin\\fuzzywuzzy'))
sys.path.append(os.path.join(os.path.dirname(__file__),'bin\\python_Levenshtein'))
sys.path.append(os.path.join(os.path.dirname(__file__),'bin\\PyYAML'))

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'utility_core_dockwidget_base.ui'))



class UtilityDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        
        super(UtilityDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.settings = None

    def closeEvent(self, event):
        print('closing')
        self.closingPlugin.emit()

        if self.settings != None:
            self.settings.guisave()
        event.accept()
        
    # def mousePressEvent(self, QMouseEvent):
    #     if QMouseEvent.button() == Qt.LeftButton:
    #         print("Left Button Clicked")
    #     elif QMouseEvent.button() == Qt.RightButton:
    #         #do what you want here
    #         print("Right Button Clicked")
