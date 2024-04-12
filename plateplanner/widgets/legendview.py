import matplotlib.pyplot as plt
from PySide6 import QtCore,QtWidgets,QtGui
from matplotlib.axes import Axes
from matplotlib.patches import Circle, Polygon, Patch
from matplotlib.backends.backend_agg import FigureCanvasAgg
from plateplanner import core

class LegendView(QtWidgets.QListWidget):
    STYLE_ROLE=101
    HANDLE_ROLE=102
    def __init__(self, parent: QtWidgets.QWidget | None = ...) -> None:
        super().__init__(parent)
        self.setIconSize(QtCore.QSize(35,20))
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        #self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)

    def add(self, style:core.Style|str, label:str=None):
        if isinstance(style, str): style=core.Style.from_str(style)
        if label is None: label="group"

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
    def styles(self) -> list[core.StyleStr]:
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
    
    def as_dict(self) -> dict[core.StyleStr,str]:
        return dict(zip(self.styles,self.labels))
    
    def remove(self, style:core.Style) -> None:
        self.takeItem(self.styles.index(style))

    def clear_selection(self) -> None:
        for item in self.items:
            item.setSelected(False)
    
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