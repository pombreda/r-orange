# treeWidgetItem. implementation of the QTreeWidgetItem class

from redRGUI import widgetState
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class treeWidgetItem(QTreeWidgetItem, widgetState):
    def __init__(self, widget = None, stringList = None, toolTip = None):
        if stringList:
            QTreeWidgetItem.__init__(self, stringList)
        else:
            QTreeWidgetItem.__init__(self)
            
        if widget:
            widget.addTopLevelItem(self)
            
        if toolTip:
            self.setToolTip(toolTip)
            
    def getSettings(self):
        r = {}
        r['text'] = []
        for i in range(self.columnCount()):
            try:
                r['text'].append(self.text(i))
            except:
                r['text'].append(None)
            
        r['childSettings'] = []
        for i in range(self.childCount()):
            r['childSettings'].append(self.child(i).getSettings())
        return r
    def loadSettings(self, data):
        try:
            ## set the text
            for i in range(len(data['text'])):
                try:
                    if data['text'][i]:
                        self.setText(i, data['text'][i])
                except:
                    continue
        except Exception as inst:
            print inst, 'Error setting text'
        ## load the child items
        try:
            if len(data['childSettings']) > 0:
                for i in range(len(data['childSettings'])):
                    try:    
                        newItem = treeWidgetItem()
                        newItem.loadSettings(data['childSettings'][i])
                        self.addChild(newItem)
                    except:
                        continue
        except Exception as inst:
            print inst, 'Exception occured in loading child items.'
    def getReportText(self, fileDir):
        return 'Please see the Red-R .rrs file for more information on this widget element.\n\n'