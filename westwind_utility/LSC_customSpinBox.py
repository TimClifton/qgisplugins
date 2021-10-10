from PyQt5.QtCore import QEvent, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QSpinBox
from PyQt5.QtGui import QCursor
from layer_sourcechanger.mousePressEnum import mousePressEnum


class LSC_customSpinBox(QSpinBox):
    def __init__(self, *args):
        QSpinBox.__init__(self, *args)


    def textFromValue(self,value):
        #super(LSC_customSpinBox, self).textFromValue(self,value)
        s = '{0:02d}'.format(value)
        return s