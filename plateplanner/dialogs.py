from PySide6 import QtWidgets, QtCore, QtGui
from plateplanner import core

class ChoosePlateDialog(QtWidgets.QDialog):
    CUSTOM="Custom"
    def __init__(self,options:dict[str,core.PlateDesign], parent=None):
        super().__init__(parent)
        layout=QtWidgets.QVBoxLayout(self)
        self.plate_options=options
        self.l1=QtWidgets.QLabel("Choose plate type",self)
        layout.addWidget(self.l1)
        self.combobox=QtWidgets.QComboBox(self)
        self.combobox.setMinimumWidth(130)
        self.combobox.addItems(list(options.keys()))
        self.combobox.addItem(self.CUSTOM)
        self.combobox.currentTextChanged.connect(self.cb_callback)
        layout.addWidget(self.combobox)

        self.custom_groupbox=QtWidgets.QGroupBox("Custom",self)
        self.custom_groupbox.setDisabled(True)
        layout.addWidget(self.custom_groupbox)

        formlayout=QtWidgets.QFormLayout(self.custom_groupbox)
        self.row_widget=QtWidgets.QSpinBox(self)
        self.row_widget.setValue(8)
        formlayout.addRow("Rows", self.row_widget)
        self.col_widget=QtWidgets.QSpinBox(self)
        self.col_widget.setValue(12)
        formlayout.addRow("Columns", self.col_widget)
        self.l_widget=QtWidgets.QLineEdit(self)
        self.l_widget.setText("127.8")
        self.l_widget.setValidator(QtGui.QDoubleValidator())
        formlayout.addRow("Length (mm)", self.l_widget)
        self.w_widget=QtWidgets.QLineEdit(self)
        self.w_widget.setText("85.5")
        self.w_widget.setValidator(QtGui.QDoubleValidator())
        formlayout.addRow("Width (mm)", self.w_widget)
        self.p1_widget=QtWidgets.QLineEdit(self)
        self.p1_widget.setText("14.4")
        self.p1_widget.setValidator(QtGui.QDoubleValidator())
        formlayout.addRow("Left margin (mm)", self.p1_widget)
        self.p2_widget=QtWidgets.QLineEdit(self)
        self.p2_widget.setText("9.0")
        self.p2_widget.setValidator(QtGui.QDoubleValidator())
        formlayout.addRow("Horizontal spacing (mm)", self.p2_widget)
        self.p3_widget=QtWidgets.QLineEdit(self)
        self.p3_widget.setText("11.2")
        self.p3_widget.setValidator(QtGui.QDoubleValidator())
        formlayout.addRow("Top margin (mm)", self.p3_widget)
        self.p4_widget=QtWidgets.QLineEdit(self)
        self.p4_widget.setText("9.0")
        self.p4_widget.setValidator(QtGui.QDoubleValidator())
        formlayout.addRow("Vertical spacing (mm)", self.p4_widget)
        self.d_widget=QtWidgets.QLineEdit(self)
        self.d_widget.setText("7.0")
        self.d_widget.setValidator(QtGui.QDoubleValidator())
        formlayout.addRow("Diameter (mm)", self.d_widget)

        self.buttonbox=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Save,self)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        layout.addWidget(self.buttonbox)

    def cb_callback(self,s:str):
        if s==self.CUSTOM:
            self.custom_groupbox.setDisabled(False)
        else:
            self.custom_groupbox.setDisabled(True)

    def get_plate(self):
        option=self.combobox.currentText()
        if option!=self.CUSTOM: return self.plate_options[option]
        else:
            plate=core.PlateDesign(
                cols=self.col_widget.value(),
                rows=self.row_widget.value(),
                length=float(self.l_widget.text()),
                width=float(self.w_widget.text()),
                p1=float(self.p1_widget.text()),
                p2=float(self.p2_widget.text()),
                p3=float(self.p3_widget.text()),
                p4=float(self.p4_widget.text()),
                d=float(self.d_widget.text()),
            )
            return plate