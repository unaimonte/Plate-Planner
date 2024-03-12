from PySide6 import QtWidgets,QtGui,QtCore
from PySide6.QtCore import Signal
from PySide6.QtGui import QPaintEvent, QPalette
import numpy as np
from matplotlib.colors import to_hex,to_rgb,rgb_to_hsv,hsv_to_rgb

class ColorButton(QtWidgets.QPushButton):
    colorChanged = Signal(object)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.command=None
        self._color=None
        self._textColor=None
        self._palette=QtGui.QPalette()
        
        self.clicked.connect(self.onColorPicker)
    
    def onColorPicker(self):
        '''
        Show color-picker dialog to select color.

        Qt will use the native dialog by default.

        '''
        dlg = QtWidgets.QColorDialog(self)
        color = dlg.getColor(QtGui.QColor.fromRgbF(*self._color))
        if color.isValid():
            color=color.getRgbF()
        else:
            return
        

        if color != self._color: self.colorChanged.emit(color)
        self.setColor(color)
        
    def textColor(self,color):
        brightness=np.mean(color)
        if brightness<0.5:
            return [1,1,1]
        else:
            return [0,0,0]
        
    def hoverColor(self,color):
        hsv=rgb_to_hsv(color)
        if hsv[2]>=0.7:
            hsv[2] -= 0.07
        else:
            hsv[2] += 0.15
        return hsv_to_rgb(hsv)
    
    def sunkenColor(self,color):
        hsv=rgb_to_hsv(color)
        if hsv[2]>=0.7:
            hsv[2] -= 0.15
        else:
            hsv[2] += 0.1
        return hsv_to_rgb(hsv)

    def setColor(self,color):
        if isinstance(color,list): color=color[0]
        self._color=to_rgb(color)
        self.buttonFormat()
        self.setText(self.getColorHex())

    def getColorRGB(self):
        return self._color

    def getColorHex(self):
        return to_hex(self._color)
    
    def buttonFormat(self):
        disabled_opacity=0.3

        base_color=QtGui.QColor.fromRgbF(*self._color)
        text_color=QtGui.QColor.fromRgbF(*self.textColor(self._color))
        hover_color=QtGui.QColor.fromRgbF(*self.hoverColor(self._color))
        sunken_color=QtGui.QColor.fromRgbF(*self.sunkenColor(self._color))

        disabled_color=QtGui.QColor(base_color)
        disabled_color.setAlphaF(disabled_opacity)
        disabled_textcolor=QtGui.QColor(text_color)
        disabled_textcolor.setAlphaF(disabled_opacity)

        self._palette.setBrush(QtGui.QPalette.Button,base_color)
        self._palette.setBrush(QtGui.QPalette.ButtonText,text_color)
        self._palette.setBrush(QtGui.QPalette.Highlight,hover_color)
        self._palette.setBrush(QtGui.QPalette.Dark,sunken_color)
        self._palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.Button,disabled_color)
        self._palette.setBrush(QtGui.QPalette.Disabled,QtGui.QPalette.ButtonText,disabled_textcolor)

    def paintEvent(self, arg__1: QPaintEvent) -> None:
        option=QtWidgets.QStyleOptionButton()
        self.initStyleOption(option)
        p=QtWidgets.QStylePainter(self)
        p.setPen(QtCore.Qt.NoPen)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        
        if option.state & QtWidgets.QStyle.State_Enabled:
            if option.state & QtWidgets.QStyle.State_Sunken:
                brush=self._palette.brush(QtGui.QPalette.Dark)
            elif option.state & QtWidgets.QStyle.State_MouseOver:
                brush=self._palette.brush(QtGui.QPalette.Highlight)
            else:
                brush=self._palette.brush(QtGui.QPalette.Button)
        else:
            brush=self._palette.brush(QtGui.QPalette.Disabled,QtGui.QPalette.Button)
        p.setBrush(brush)
        p.drawRoundedRect(option.rect,4,4)

        if option.state & QtWidgets.QStyle.State_Enabled:
            p.setPen(self._palette.color(QtGui.QPalette.ButtonText))
        else:
            p.setPen(self._palette.color(QtGui.QPalette.Disabled,QtGui.QPalette.ButtonText))
        p.drawText(option.rect,QtCore.Qt.AlignCenter,option.text)

def main():
    cb=ColorButton(window)
    cb.setDisabled(True)
    layout.addWidget(cb,0,0)
    cb.setColor("cyan")

if __name__=="__main__":
    import sys
    import resources_rc
    app = QtWidgets.QApplication(sys.argv)
    stylesheet=open("my_theme.qss","r")
    app.setStyleSheet(stylesheet.read())
    window=QtWidgets.QWidget()
    layout=QtWidgets.QGridLayout()

    main()
    window.show()
    app.exec()
