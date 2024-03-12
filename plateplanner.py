import os
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf #SI SE ELIMINA NO SE INCLUYE EN EL PAQUETE!!!!!
import matplotlib.backends.backend_svg #SI SE ELIMINA NO SE INCLUYE EN EL PAQUETE!!!!!
import numpy as np
import pandas as pd
import json
import pathlib
from dataclasses import dataclass
from typing import override,Optional,Self
from PySide6 import QtCore,QtWidgets,QtGui
from matplotlib.axes import Axes
from matplotlib.colors import to_hex
from matplotlib.typing import ColorType
from matplotlib.figure import Figure
from matplotlib.patches import Circle, Polygon, Patch
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backend_bases import PickEvent
import matplotlib.image as mpimg
from qt_colorbutton import ColorButton


basedir = os.path.dirname(__file__)

VERSION="1.1.0"

L_LEGEND=30
EDITOR_WIDTH=100
EDITOR_HEIGHT=20

FACECOLOR="#ffffff"
EDGECOLOR="#000000"
LINEWIDTH=1
HATCHING=""

plt.rcParams["legend.frameon"]=False
plt.rcParams["legend.fontsize"]=8
plt.rcParams["legend.handlelength"]=2

@dataclass
class PlateDesign:
    id:str
    cols:int
    rows:int
    length:float
    width:float
    p1:float
    p2:float
    p3:float
    p4:float
    d:float
    scale:float=1
    background_image:Optional[pathlib.Path]=None
    #background_dpi:int=200

plate_options={
    "96-well":PlateDesign(
        id="96-well",
        cols=12,
        rows=8,
        length=127.8,
        width=85.5,
        p1=14.4,
        p2=9.0,
        p3=11.2,
        p4=9.0,
        d=7.0,
        background_image=os.path.join(basedir,"plateplanner","96well.png")
    ),
    "24-well":PlateDesign(
        id="24-well",
        cols=6,
        rows=4,
        length=127.8,
        width=85.5,
        p1=16.4,
        p2=19.0,
        p3=14.2,
        p4=19.0,
        d=16.5,
        background_image=os.path.join(basedir,"plateplanner","24well.png")
    ),
}

StyleStr=str

@dataclass(slots=True)
class Style:
    _facecolor: ColorType = FACECOLOR
    _edgecolor: ColorType = EDGECOLOR
    _hatching: str = HATCHING

    @property
    def facecolor(self) -> str:
        return to_hex(self._facecolor)
    
    @facecolor.setter
    def facecolor(self, c:ColorType):
        self._facecolor=c
    
    @property
    def edgecolor(self) -> str:
        return to_hex(self._edgecolor)
    
    @edgecolor.setter
    def edgecolor(self, c:ColorType):
        self._edgecolor=c

    @property
    def hatching(self) -> str:
        return self._hatching
    
    @hatching.setter
    def hatching(self, h:str):
        self._hatching=h
    
    def __str__(self) -> StyleStr:
        return f"{self.facecolor}:{self.edgecolor}:{self.hatching}"
    
    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self,other) -> bool:
        return str(self) == str(other)

    @classmethod
    def from_str(cls, s:str)->Self:
        return cls(*s.split(":"))

class StyleEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Style):
            return str(obj)
        return super().default(obj)

class LegendView(QtWidgets.QListWidget):
    STYLE_ROLE=101
    HANDLE_ROLE=102
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.setIconSize(QtCore.QSize(35,20))
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)

    def add(self, style:Style|str, label:str="group"):
        if isinstance(style, str): style=Style.from_str(style)

        handle,pm=self.create_handle(
                size=self.iconSize(),
                linewidth=2,
                facecolor=style.facecolor,
                hatch=style.hatching,
                edgecolor=style.edgecolor,
                )
            
        item=QtWidgets.QListWidgetItem(pm,label,self)
        item.setData(self.STYLE_ROLE,str(style))
        item.setData(self.HANDLE_ROLE,handle)

        item.setFlags(item.flags()|QtCore.Qt.ItemFlag.ItemIsEditable)
        self.addItem(item)
    
    @property
    def styles(self) -> list[StyleStr]:
        return [self.item(i).data(self.STYLE_ROLE) for i in range(self.count())]
    
    @property
    def items(self) -> list[QtWidgets.QListWidgetItem]:
        return [self.item(i) for i in range(self.count())]
    
    @property
    def handles(self) -> list[Patch]:
        return [self.item(i).data(self.HANDLE_ROLE) for i in range(self.count())]
    
    @property
    def labels(self) -> list[str]:
        return [self.item(i).text() for i in range(self.count())]
    
    def as_dict(self) -> dict[StyleStr,str]:
        return dict(zip(self.styles,self.labels))
    
    def remove(self, style:Style) -> None:
        self.takeItem(self.styles.index(style))
    
    @staticmethod
    def create_handle(size:QtCore.QSize, dpi=100, **kwargs)->tuple[Patch,QtGui.QPixmap]:
        fig = plt.figure(figsize=(size.width()/dpi, size.height()/dpi),dpi=dpi*2)
        fig.set_canvas(FigureCanvasAgg(fig))

        ax:Axes = fig.add_axes([0, 0, 1, 1])
        ax.patch.set(**kwargs)
        plt.close()
        fig.canvas.draw()

        buf, size_pixels = fig.canvas.print_to_buffer()
        qimage = QtGui.QImage.rgbSwapped(QtGui.QImage(buf, size_pixels[0], size_pixels[1], QtGui.QImage.Format_ARGB32))
        qpixmap = QtGui.QPixmap(qimage)

        return (ax.patch, qpixmap)

class MainWindow(QtWidgets.QMainWindow):
    selected:list[tuple[int]]
    def __init__(self, design: Optional[PlateDesign]=None) -> None:
        super().__init__()
        if design is None:
            dlg=ChoosePlateDialog(self)
            if dlg.exec():
                self.design=dlg.get_plate()
            else:
                QtWidgets.QApplication.instance().quit()
        else:
            self.design=design
        self.filemanager=FileManager(self)
        self.wells=pd.DataFrame()
        self.selected=[]
        self.setWindowTitle("Multiwell Plate Planner")
        self.setWindowIcon(QtGui.QIcon(os.path.join(basedir,"plateplanner","icon.ico")))
        self.setCentralWidget(QtWidgets.QWidget(self))
        self.central_layout=QtWidgets.QGridLayout(self.centralWidget())
        self.sidepanel=QtWidgets.QGroupBox(self)
        self.sidepanel_layout=QtWidgets.QVBoxLayout(self.sidepanel)
        self.central_layout.addWidget(self.sidepanel,0,0)
        self.form_layout=QtWidgets.QFormLayout()
        self.sidepanel_layout.addLayout(self.form_layout)
        self.sidepanel.setTitle("Plate planner")

        self.bottom_text=QtWidgets.QLabel(self)
        self.bottom_text.setText("Drag to select wells. Click on legend labels to edit them.")
        self.central_layout.addWidget(self.bottom_text,1,0,1,2,QtCore.Qt.AlignmentFlag.AlignTop)

        self.signature=QtWidgets.QLabel(self)
        self.signature.setStyleSheet("QLabel{font-size: 10px; color: #888888}")
        self.signature.setText(f"Plate Planner {VERSION} by Unai Montejo")
        self.central_layout.addWidget(self.signature,1,0,1,2,QtCore.Qt.AlignmentFlag.AlignBottom|QtCore.Qt.AlignmentFlag.AlignRight)

        self.fill_button=ColorButton(self)
        self.fill_button.setMinimumWidth(100)
        self.fill_button.setColor("w")
        self.fill_button.colorChanged.connect(self.paint_fill)
        self.form_layout.addRow("Fill",self.fill_button)

        self.edge_button=ColorButton(self)
        self.edge_button.setMinimumWidth(100)
        self.edge_button.setColor("k")
        self.edge_button.colorChanged.connect(self.paint_edge)
        self.form_layout.addRow("Edge",self.edge_button)

        self.hatch_cb=QtWidgets.QComboBox(self)
        self.hatch_cb.setMinimumWidth(100)
        self.hatch_cb.addItems(["","////","xxxx","ooo","oo"])
        self.hatch_cb.currentTextChanged.connect(self.paint_hatches)
        self.form_layout.addRow("Hatching",self.hatch_cb)

        self.export_button=QtWidgets.QPushButton("Export",self)
        self.export_button.clicked.connect(self.export)
        self.sidepanel_layout.addWidget(self.export_button)

        self.save_button=QtWidgets.QPushButton("Save as",self)
        self.save_button.clicked.connect(self.save_as)
        self.sidepanel_layout.addWidget(self.save_button)

        self.canvas=Canvas(parent=self)
        self.canvas.areaSelected.connect(self.select_area)
        self.central_layout.addWidget(self.canvas,0,1)

        self.legendview=LegendView(self)
        self.central_layout.addWidget(self.legendview,0,2)

        file_menu=self.menuBar().addMenu("File")
        export_action=QtGui.QAction("Export...",self)
        export_action.triggered.connect(self.export)
        save_as_action=QtGui.QAction("Save as...",self)
        save_as_action.triggered.connect(self.save_as)
        save_action=QtGui.QAction("Save",self)
        save_action.triggered.connect(self.save)
        open_action=QtGui.QAction("Open...",self)
        open_action.triggered.connect(self.open)
        file_menu.addActions([export_action,save_as_action,save_action,open_action])

        edit_menu=self.menuBar().addMenu("Edit")
        copy_action=QtGui.QAction("Copy to clipboard",self)
        export_action.triggered.connect(self.to_clipboard)
        edit_menu.addActions([copy_action])

        self.create_plate()
        self.update_legend()

    def update_legend(self):
        current_styles=self.wells["style"].unique()

        #add newly created styles to LegendView
        for s in current_styles:
            if s in self.legendview.styles: continue
            self.legendview.add(s)
        
        #remove unused styles from legendview
        for s in self.legendview.styles:
            if s not in current_styles:
                self.legendview.remove(s)
        

    def select_area(self,p0:QtCore.QPoint,p1:QtCore.QPoint):
        dpi=self.physicalDpiX()

        left=min(p0.x(),p1.x())
        right=max(p0.x(),p1.x())
        top=min(p0.y(),p1.y())
        bottom=max(p0.y(),p1.y())

        p1_px=self.design.p1/25.4*dpi
        p2_px=self.design.p2/25.4*dpi
        p3_px=self.design.p3/25.4*dpi
        p4_px=self.design.p4/25.4*dpi

        min_col=int((left-p1_px)//p2_px+1)
        max_col=int((right-p1_px)//p2_px+1)
        min_row=int((top-p3_px)//p4_px+1)
        max_row=int((bottom-p3_px)//p4_px+1)

        if min_col<0: min_col=0
        if max_col>self.design.cols: max_col=self.design.cols
        if min_row<0: min_row=0
        if max_row>self.design.rows: max_row=self.design.rows

        selection=[]
        for right in range(min_row,max_row):
            for c in range(min_col,max_col):
                selection.append((right,c))

        self.select_wells(selection)
                
    def select_wells(self,selection:list[tuple[int]]):
        for i in self.selected:
            self.wells.loc[i,"artist"].set_linestyle("solid")

        self.selected=selection
        for i in selection:
            well=self.wells.loc[i]["artist"]
            well.set_linestyle("dashed")

        self.canvas.draw_idle()

    def export(self):
        self.select_wells([])
        export_path = QtWidgets.QFileDialog.getSaveFileName(
            self, 
            caption="Export figure",
            dir=os.path.expanduser("~/Desktop"),
            filter="Images (*.png *.jpg);;Vector images (*.svg);;PDF file (*.pdf)",
            selectedFilter="Images (*.png *.jpg)",
            )[0]
        if export_path != "":
            size_inches=((self.design.length+L_LEGEND)/25.4,self.design.width/25.4)
            fig=plt.figure(figsize=size_inches,dpi=200)
            fig.gca().set_position((0,0,1-L_LEGEND/(L_LEGEND+self.design.length),1))
            self.init_figure(fig,self.wells["style"].map(str))

            fig.gca().legend(handles=self.legendview.handles,labels=self.legendview.labels,loc="upper left",bbox_to_anchor=(1,1))
            fig.savefig(export_path,dpi=300,pad_inches=0,metadata={"Creator": "Plate Planner"})

    def save_as(self):
        path = pathlib.Path(QtWidgets.QFileDialog.getSaveFileName(
            self, 
            caption="Save plate",
            dir=os.path.expanduser("~/Desktop"),
            filter="Plate (*.plate)",
            )[0])
        if path != "":
            self.filemanager.set_path(path)
            self.setWindowTitle(path.name)
            self.filemanager.save()
    
    def save(self):
        if self.filemanager.path is None:
            self.save_as()
        else:
            self.filemanager.save()

    def open(self):
        path=pathlib.Path(QtWidgets.QFileDialog.getOpenFileName(
            self, 
            caption="Open Plate Planner file",
            dir=os.path.expanduser("~/Desktop"),
            filter="Plate (*.plate)",
            )[0])
        if path !="":
            self.select_wells([])
            data=self.filemanager.open(path)
            self.design=plate_options[data["plate"]]
            self.create_plate(data["wells"])
            self.figure.set_dpi(self.physicalDpiX()*self.devicePixelRatio())
            
            self.legendview.clear()
            for s,l in data["legend"].items():
                self.legendview.add(s,l)

            self.setWindowTitle(path.name)

    def to_clipboard(self):
        buf, size = self.canvas.print_to_buffer()
        qimage = QtGui.QImage.rgbSwapped(QtGui.QImage(buf, size[0], size[1], QtGui.QImage.Format_ARGB32))
        QtWidgets.QApplication.clipboard().setImage(qimage)

    def paint_fill(self, color:ColorType):
        for i in self.selected:
            self.wells.loc[i,"artist"].set_facecolor(color)
            self.wells.loc[i,"style"].facecolor=color
        self.select_wells([])
        self.update_legend()

    def paint_edge(self, color:ColorType):
        color=to_hex(color)
        for i in self.selected:
            self.wells.loc[i,"artist"].set_edgecolor(color)
            self.wells.loc[i,"style"].edgecolor=color
        self.select_wells([])
        self.update_legend()

    def paint_hatches(self, hatch:str):
        for i in self.selected:
            self.wells.loc[i,"artist"].set_hatch(hatch)
            self.wells.loc[i,"style"].hatching=hatch
        self.select_wells([])
        self.update_legend()

    def create_plate(self,wells:pd.Series=None):
        fig,ax=plt.subplots()
        ax.set_position((0,0,1,1))
        size_inches=(self.design.length/25.4,self.design.width/25.4)
        fig.set_size_inches(size_inches,forward=True)
        fig.set_dpi(self.physicalDpiX())
        self.figure=fig
        self.canvas.figure=fig
        items=self.init_figure(fig,wells=wells)
        self.wells=pd.DataFrame(items).set_index(["row","column"])

    def init_figure(self,fig:Figure, wells:pd.Series=None)->list[dict]:
        ax=fig.gca()
        ax.axis('off')

        corner=Polygon(
            ((0,0),
             (0,0.05*self.design.width),
             (0.05*self.design.width,0)
            ),
            closed=True,
            facecolor="k",
            linewidth=0,
            transform=ax.transData
        )

        ax.add_artist(corner)
        ax.patch.set_facecolor(None)
        fig.patch.set_facecolor("none")

        if self.design.background_image is not None: #TODO: usar SVGs en vez bitmaps
            img = mpimg.imread(self.design.background_image)
            ax.imshow(img, aspect="auto", interpolation="antialiased", extent=(0,self.design.length,self.design.width,0))

        items=[]
        for row in range(self.design.rows):
            for col in range(self.design.cols):
                x=self.design.p2*col+self.design.p1
                y=self.design.p4*row+self.design.p3
                if wells is None:
                    style=Style()
                else:
                    style=Style.from_str(wells.loc[row,col])
                cir=plt.Circle(
                    (x,y),
                    self.design.d/2,
                    linewidth=LINEWIDTH, 
                    facecolor=style.facecolor,
                    edgecolor=style.edgecolor,
                    hatch=style.hatching,
                    )
                ax.add_artist(cir)
                items.append(dict(
                    row=row,
                    column=col,
                    artist=cir,
                    style=style
                ))
        ax.set_xlim(0,self.design.length)
        ax.set_ylim(self.design.width,0)
        return items
    
class Canvas(FigureCanvasQTAgg, QtWidgets.QWidget):
    start_pos:QtCore.QPoint|None=None
    current_pos:QtCore.QPoint|None=None
    areaSelected=QtCore.Signal(QtCore.QPoint,QtCore.QPoint)
    editStarted=QtCore.Signal(QtCore.QRect,str,int)
    editEnded=QtCore.Signal()
    editing=False

    def __init__(self, figure=None, parent=QtWidgets.QWidget|None):
        super().__init__(figure)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        self.setParent(parent)
        self.setMouseTracking(False)
        self.mpl_connect('pick_event', self.on_pick)  

    @override
    def mousePressEvent(self, event:QtGui.QMouseEvent):
        pos=event.position().toPoint()
        self.editEnded.emit()
        self.start_pos=pos
        return super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event:QtGui.QMouseEvent):
        self.current_pos=event.position().toPoint()
        self.update()
        
    @override
    def mouseReleaseEvent(self, event:QtGui.QMouseEvent):
        self.end_selection(event)
        self.update()
        return super().mouseReleaseEvent(event)

    @override
    def leaveEvent(self, event:QtGui.QMouseEvent):
        self.end_selection(event)
        self.update()
        return super().leaveEvent(event)
    
    def end_selection(self,event:QtGui.QMouseEvent):
        if self.start_pos is not None:
            self.areaSelected.emit(self.start_pos,event.position().toPoint())
            self.start_pos=None
            self.current_pos=None
    
    @override
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.start_pos and self.current_pos is not None:
            p=QtGui.QPainter(self)
            selection_rect=QtCore.QRect(self.start_pos,self.current_pos)
            pen=QtGui.QPen(QtCore.Qt.black,1)
            p.setPen(pen)
            p.drawRect(selection_rect)

    def on_pick(self,event:PickEvent):
        self.start_pos=None
        self.current_pos=None
        labels=self.figure.gca().get_legend().get_texts()
        handles=self.figure.gca().get_legend().legend_handles
        if event.artist in labels:
            index=labels.index(event.artist)
        elif event.artist in handles:
            index=handles.index(event.artist)
        else:
            return
        
        handle=handles[index]
        label=labels[index]
        
        text=label.get_text()
        bbox=handle.get_tightbbox(self.get_renderer())
        x0=bbox.xmax/self.devicePixelRatio()+10
        y0=self.height()-bbox.ymin/self.devicePixelRatio()-EDITOR_HEIGHT+5
        label.set_text("")
        rect=QtCore.QRect(x0,y0,EDITOR_WIDTH,EDITOR_HEIGHT)
        self.editStarted.emit(rect,text,index)

        self.draw_idle()

    def showEvent(self, event):
        super().showEvent(event)

class ChoosePlateDialog(QtWidgets.QDialog):
    CUSTOM="Custom"
    def __init__(self, parent=None):
        super().__init__(parent)
        layout=QtWidgets.QVBoxLayout(self)
        self.l1=QtWidgets.QLabel("Choose plate type",self)
        layout.addWidget(self.l1)
        self.combobox=QtWidgets.QComboBox(self)
        self.combobox.setMinimumWidth(130)
        self.combobox.addItems(list(plate_options.keys()))
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
        if option!=self.CUSTOM: return plate_options[option]
        else:
            plate=PlateDesign(
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
        
class FileManager:
    path:pathlib.Path=None
    def __init__(self, parent:MainWindow):
        self.parent=parent

    def set_path(self,path:pathlib.Path):
        self.path=path

    def save(self):
        data={
            "plate": self.parent.design.id,
            "legend": self.parent.legendview.as_dict(),
            "wells": self.parent.wells["style"].unstack().to_dict()
        }
        with open(self.path, "w") as file:
            json.dump(data,file,indent=4,cls=StyleEncoder)

    def open(self,path:pathlib.Path)->dict:
        self.set_path(path)
        with open(path, "r") as file:
            data=json.load(file)
        wells=pd.DataFrame.from_dict(data["wells"])
        wells.index=wells.index.map(int)
        wells.columns=wells.columns.map(int)
        data["wells"]=wells.stack()
        return data

def main():
    import sys
    import resources_rc
    app = QtWidgets.QApplication(sys.argv)
    file=QtCore.QFile(":/files/stylesheet.qss")
    file.open(QtCore.QFile.ReadOnly)
    ss=file.readAll().toStdString()
    app.setStyleSheet(ss)
    window=MainWindow()
    window.show()
    app.exec()

if __name__=="__main__":
    main()