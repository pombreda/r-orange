"""Scroll Area

Generates an area in which the user can scroll to items that are not visible.  Useful if there are many options stacked.

"""

from redRGUI import widgetState
from libraries.base.qtWidgets.widgetBox import widgetBox
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import redRi18n
_ = redRi18n.get_(package = 'base')
        
class scrollArea(QScrollArea,widgetState):
    def __init__(self,widget, orientation=QVBoxLayout(), addSpace=False, 
    margin = -1, spacing = -1, addToLayout = 1, **kwargs):
        kwargs.setdefault('includeInReports', True)
        kwargs.setdefault('sizePolicy', QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        widgetState.__init__(self,widget, 'scrollArea',**kwargs)
        QScrollArea.__init__(self,self.controlArea)
            
        if margin == -1: margin = 0
        self.controlArea.layout().addWidget(self)
        
        try:
            if isinstance(orientation, QLayout):
                self.setLayout(orientation)
            elif orientation == 'horizontal' or not orientation:
                self.setLayout(QHBoxLayout())
            else:
                self.setLayout(QVBoxLayout())
        except:
            self.setLayout(QVBoxLayout())
            
        if self.layout() == 0 or self.layout() == None:
            self.setLayout(QVBoxLayout())

        
        if spacing == -1: spacing = 4
        self.layout().setSpacing(spacing)
        if margin != -1:
            self.layout().setMargin(margin)

        if addSpace and isinstance(addSpace, int):
            separator(widget, 0, addSpace)
        elif addSpace:
            separator(widget)
	