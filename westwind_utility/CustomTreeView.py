from PyQt5.QtCore import QEvent, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QTreeView, QMenu
from PyQt5.QtGui import QCursor
from layer_sourcechanger.mousePressEnum import mousePressEnum


class CustomTreeView(QTreeView):

    mousePressed = pyqtSignal(int)
    mouseReleased = pyqtSignal(int)

    def mousePressEvent(self, event):
        print("Emitting Signal")
        
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:

                self.mousePressed.emit(mousePressEnum.leftclick.value)
                #print( "Left click")
                
            elif event.button() == Qt.RightButton:
               
                self.mousePressed.emit(mousePressEnum.rightclick.value)

            elif event.button() == Qt.MiddleButton:
                print( "Middle click")
        super(CustomTreeView, self).mousePressEvent(event)


    def mouseReleaseEvent(self, event):
        print("Emitting Mouse Release Signal")
        
        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:

                self.mouseReleased.emit(mousePressEnum.leftclick.value)
                #print( "Left click")
                
            elif event.button() == Qt.RightButton:
               
                self.mouseReleased.emit(mousePressEnum.rightclick.value)

            elif event.button() == Qt.MiddleButton:
                print( "Middle click")
        super(CustomTreeView, self).mouseReleaseEvent(event)





    # @pyqtSlot(int)
    # def on_mousePressed(self, event):
    #     print("mouse event")

    # def createMenu(self,_event,parent=None):
    #     self.popupMenu = QMenu(parent)
    #     self.popupMenu.addAction("Action1")
    #     self.popupMenu.addAction("Action2")
    #     self.popupMenu.addAction("Action3")
    #     print("Menu")
    #     self.popupMenu.exec(QCursor.pos())