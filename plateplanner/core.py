import os
import matplotlib.pyplot as plt
import pandas as pd
import json
import pathlib
from dataclasses import dataclass
from typing import override,Optional,Self
from PySide6 import QtCore,QtWidgets,QtGui
from matplotlib.colors import to_hex
from matplotlib.typing import ColorType
from matplotlib.patches import Circle
from matplotlib.backend_bases import PickEvent
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from plateplanner import PLATEDIR

VERSION="1.1.0"

FACECOLOR="#ffffff"
EDGECOLOR="#000000"
HATCHING=""
LINEWIDTH=1

StyleStr=str

plt.rcParams["legend.frameon"]=False
plt.rcParams["legend.fontsize"]=8
plt.rcParams["legend.handlelength"]=2

@dataclass
class PlateDesign:
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
    id:str="custom"
    background_image:Optional[str]=None
    #background_dpi:int=200

    def __post_init__(self):
        if self.background_image is not None:
            self.background_image=os.path.join(PLATEDIR,self.background_image)

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

class Well(Circle):
    def __init__(self,pos:tuple[float,float], design:PlateDesign, style:Style|str=None):
        self.design=design
        if style is None: style=Style()
        elif isinstance(style, str): style=Style.from_str(style)
        self.style=style
        super().__init__(
            xy=pos,
            radius=design.d/2,
            linewidth=LINEWIDTH, 
            facecolor=style.facecolor,
            edgecolor=style.edgecolor,
            hatch=style.hatching,
            picker=True,
        )

    @property
    def facecolor(self) -> str:
        return self.style.facecolor
    
    @facecolor.setter
    def facecolor(self, c:ColorType):
        self.style.facecolor=c
        self.set_facecolor(self.style.facecolor)
    
    @property
    def edgecolor(self) -> str:
        return self.style.edgecolor
    
    @edgecolor.setter
    def edgecolor(self, c:ColorType):
        self.style.edgecolor=c
        self.set_edgecolor(self.style.edgecolor)

    @property
    def hatching(self) -> str:
        return self.style.hatching
    
    @hatching.setter
    def hatching(self, h:str):
        self.style.hatching=h
        self.set_hatch(self.style.hatching)
        
    def __str__(self) -> StyleStr:
        return str(self.style)
    
    def __hash__(self) -> int:
        return hash(self.style)

    def __eq__(self,other) -> bool:
        return str(self) == str(other)
    


class Canvas(FigureCanvasQTAgg, QtWidgets.QWidget):
    start_pos:QtCore.QPoint|None=None
    current_pos:QtCore.QPoint|None=None
    areaSelected=QtCore.Signal(QtCore.QPoint,QtCore.QPoint)
    editStarted=QtCore.Signal(QtCore.QRect,str,int)
    editEnded=QtCore.Signal()
    wellPicked=QtCore.Signal(Well)
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
        self.wellPicked.emit(event.artist)
        
class FileManager:
    path:pathlib.Path=None
    def __init__(self, parent:QtWidgets.QWidget):
        self.parent=parent

    def set_path(self,path:pathlib.Path):
        self.path=path

    def save(self, data: dict):
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

