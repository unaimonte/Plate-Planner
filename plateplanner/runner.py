from PySide6 import QtCore, QtGui, QtWidgets
from plateplanner.mainwindow import MainWindow
from plateplanner.core import PlateDesign
from plateplanner.resources import resources_rc
from plateplanner import PLATEDIR
import json
import sys
import os


PLATE_OPTIONS=os.path.join(PLATEDIR,"plates.json")

def run():
    app = QtWidgets.QApplication(sys.argv)
    file=QtCore.QFile(":/files/stylesheet.qss")
    file.open(QtCore.QFile.ReadOnly)
    ss=file.readAll().toStdString()
    app.setStyleSheet(ss)

    with open(PLATE_OPTIONS, "r") as file:
        plate_json:dict[dict]=json.load(file)

    plate_options:dict[str,PlateDesign]={name:PlateDesign(**kwargs) for name, kwargs in plate_json.items()}

    window=MainWindow(plate_options)
    window.show()
    app.exec()

if __name__=="__main__":
    run()