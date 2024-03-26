import os
import pandas as pd
import pathlib
from typing import Optional
from PySide6 import QtWidgets, QtCore, QtGui
from matplotlib.typing import ColorType
from matplotlib.figure import Figure
from matplotlib import colors, patches
from enum import Enum,auto
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf #SI SE ELIMINA NO SE INCLUYE EN EL PAQUETE!!!!!
import matplotlib.backends.backend_svg #SI SE ELIMINA NO SE INCLUYE EN EL PAQUETE!!!!!
from plateplanner import core,dialogs
from plateplanner.widgets.colorbutton import ColorButton
from plateplanner.widgets.legendview import LegendView

L_LEGEND=30

class MainWindow(QtWidgets.QMainWindow):
    class SelectionMode(Enum):
        WELLS=auto()
        GROUPS=auto()
    selected:list[tuple[int]]
    selection_mode:SelectionMode=SelectionMode.WELLS
    def __init__(self, options:dict[str,core.PlateDesign], design: Optional[core.PlateDesign]=None) -> None:
        super().__init__()
        if design is None:
            dlg=dialogs.ChoosePlateDialog(options,parent=self)
            if dlg.exec():
                self.design=dlg.get_plate()
            else:
                QtWidgets.QApplication.instance().quit()
        else:
            self.design=design

        self.plate_options=options
        self.filemanager=core.FileManager(self)
        self.wells=pd.DataFrame()
        self.selected=[]
        self.setWindowTitle("Multiwell Plate Planner")
        self.setWindowIcon(QtGui.QIcon(":/icons/icon.ico"))
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
        self.signature.setText(f"Plate Planner {core.VERSION} by Unai Montejo")
        self.central_layout.addWidget(self.signature,1,0,1,3,QtCore.Qt.AlignmentFlag.AlignBottom|QtCore.Qt.AlignmentFlag.AlignRight)

        self.fill_button=ColorButton(self)
        self.fill_button.setMinimumWidth(100)
        self.fill_button.setColor("w")
        self.fill_button.colorChanged.connect(self.paint_face)
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

        self.selection_mode_cb=QtWidgets.QComboBox(self)
        self.selection_mode_cb.addItems(["Wells","Groups"])
        self.selection_mode_cb.currentIndexChanged.connect(self.selection_mode_changed)

        self.canvas=core.Canvas(parent=self)
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

    def selection_mode_changed(self, index):
        self.selection_mode=index

    def update_legend(self):
        current_styles=[well.style for well in self.wells.unique()]

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
            self.wells.loc[i].set_linestyle("solid")

        self.selected=selection
        for i in selection:
            self.wells.loc[i].set_linestyle("dashed")

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
            self.save()
    
    def save(self):
        if self.filemanager.path is None:
            self.save_as()
        else:
            data={
                "plate": self.design.id,
                "legend": self.legendview.as_dict(),
                "wells": self.wells["style"].unstack().to_dict()
            }
            self.filemanager.save(data)

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
            self.design=self.plate_options[data["plate"]]
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

    def paint_face(self, color:ColorType):
        for i in self.selected:
            self.wells.loc[i].facecolor=color
        self.select_wells([])
        self.update_legend()

    def paint_edge(self, color:ColorType):
        color=colors.to_hex(color)
        for i in self.selected:
            self.wells.loc[i].edgecolor=color
        self.select_wells([])
        self.update_legend()

    def paint_hatches(self, hatch:str):
        for i in self.selected:
            self.wells.loc[i].hatching=hatch
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
        self.wells=self.init_figure(fig,wells=wells)

    def init_figure(self,fig:Figure, wells:pd.Series=None)->pd.DataFrame:
        ax=fig.gca()
        ax.axis('off')

        corner=patches.Polygon(
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
            img = plt.imread(self.design.background_image)
            ax.imshow(img, aspect="auto", interpolation="antialiased", extent=(0,self.design.length,self.design.width,0))

        rows=[]
        for row in range(self.design.rows):
            column=[]
            for col in range(self.design.cols):
                x=self.design.p2*col+self.design.p1
                y=self.design.p4*row+self.design.p3
                if wells is None:
                    style=None
                else:
                    style=wells.loc[row,col]
                well=core.Well(
                    pos=(x,y),
                    design=self.design,
                    style=style
                    )
                ax.add_artist(well)
                column.append(well)
            rows.append(column)
        ax.set_xlim(0,self.design.length)
        ax.set_ylim(self.design.width,0)
        return pd.DataFrame(rows).stack()