"""Stacked Widget

Controls a set of value stacks that show different widgets at different times.
"""
from redRGUI import widgetState
from libraries.base.qtWidgets.widgetBox import widgetBox as redRWidgetBox

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import redRi18n
_ = redRi18n.get_(package = 'base')


class stackedWidget(QStackedWidget, widgetState):
    def __init__(self, widget, label = None, displayLabel = False,**kwargs):
        kwargs.setdefault('includeInReports', False)
        kwargs.setdefault('sizePolicy', QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        widgetState.__init__(self,widget, 'stackedWidget',**kwargs)
        QStackedWidget.__init__(self, self.controlArea)
        self.controlArea.layout().addWidget(self)
        self.stackIndex = []
    def createWidgetBox(self, orientation = 'vertical'):
        """Creates and returns a new widgetBox in the stack with orientation orientation"""
        newBox = redRWidgetBox(self, orientation = orientation)
        print self.addWidget(newBox)
        return newBox

    def getSettings(self):
        r = {'currentIndex':self.currentIndex()}
        return r

    def loadSettings(self, r):
        self.setCurrentIndex(r['currentIndex'])