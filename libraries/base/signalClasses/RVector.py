"""RVector
.. helpdoc::
This is the least generic signal.  Vectors can either represent single data points or sets of data points.  R treats these the same."""

"""
.. convertTo:: `base:RDataFrame, base:StructuredDict, base:UnstructuredDict, base:RMatrix, base:RVariable, base:RList`
.. convertFrom:: ``
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from RSession import Rcommand
from libraries.base.signalClasses.RMatrix import *
from libraries.base.signalClasses.RDataFrame import *
from libraries.base.signalClasses.StructuredDict import *
from libraries.base.signalClasses.UnstructuredDict import *

class RVector(RMatrix):
    convertToList = [RDataFrame, StructuredDict, UnstructuredDict, RMatrix, RVariable, RList]
    convertFromList = []
    def __init__(self, widget, data, parent = None, checkVal = True, **kwargs):
        RMatrix.__init__(self, widget = widget, data = data, parent = parent, checkVal = False, **kwargs)
        if checkVal:
            if self.R('class('+str(self.getData())+')', wantType = 'list')[0] not in ['complex', 'raw', 'numeric', 'factor', 'character', 'logical', 'integer', 'POSIXt', 'POSIXct']:
                raise Exception, 'Not vector data'
        self.StructuredDictSignal = None
        self.RDataFrameSignal = None
        self.RMatrixSignal = None
        self.RListSignal = None
    def convertToClass(self, varClass):
        if varClass == RList:
            return self._convertToList()
        elif varClass == RVariable:
            return self._convertToVariable()
        elif varClass == RDataFrame:
            return self._convertToDataFrame()
        elif varClass == RMatrix:
            return self._convertToMatrix()
        elif varClass == RVector:
            return self
        elif varClass == StructuredDict:
            return self._convertToStructuredDict()
        elif varClass == UnstructuredDict:
            return self._convertToStructuredDict()
        else:
            raise Exception
    def _convertToStructuredDict(self):
        if not self.StructuredDictSignal:
            data = self.R('as.data.frame('+str(self.getData())+')', wantType = 'dict')
            keys = ['row_names']
            keys += self.R('colnames(as.data.frame('+str(self.getData())+'))', wantType = 'list')
            rownames = self.R('rownames('+str(self.getData())+')', wantType = 'list')
            try:
                if rownames in [None, 'NULL', 'NA']:
                    rownames = [unicode(i+1) for i in range(len(data[data.keys()[0]]))]
            except:
                rownames = [unicode(i+1) for i in range(len(data[data.keys()[0]]))]
            data['row_names'] = rownames
            self.StructuredDictSignal = StructuredDict(widget = self.widget, data = data, parent = self, keys = keys)
            return self.StructuredDictSignal
        else:
            return self.StructuredDictSignal
    def _convertToMatrix(self):
        if not self.RMatrixSignal:
            self.RMatrixSignal = RMatrix(widget = self.widget, data = 'as.matrix('+self.data+')')
            self.RMatrixSignal.dictAttrs = self.dictAttrs.copy()
            return self.RMatrixSignal
        else:
            return self.RMatrixSignal
    def _convertToList(self):
        if not self.RListSignal:
            self.R('list_of_'+self.data+'<-as.list(as.data.frame('+self.data+'))', wantType = 'NoConversion')
            self.RListSignal = RList(widget = self.widget, data = 'list_of_'+self.data, parent = self.parent)
            self.RListSignal.dictAttrs = self.dictAttrs.copy()
            return self.RListSignal
        else:
            return self.RListSignal
    def _convertToDataFrame(self):
        if not self.RDataFrameSignal:
            self.RDataFrameSignal = RDataFrame(widget = self.widget, data = 'as.data.frame('+self.data+')', parent = self.parent)
            self.RDataFrameSignal.dictAttrs = self.dictAttrs.copy()
            return self.RDataFrameSignal
        else:
            return self.RDataFrameSignal
    def _convertToVariable(self):
        return self
        
    def getSimpleOutput(self, subsetting = '[1:5]'):
        # return the text for a simple output of this variable
        text = 'Simple Output\n\n'
        text += 'Class: '+self.getClass_data()+'\n\n'
        text += self._simpleOutput(subsetting)
        return text
    
    def getColumnnames_call(self):
        return self.getNames_call()
    def getColumnnames_data(self):
        return self.getNames_data()
    def getNames_call(self):
        return str(self.getData())
    def getNames_data(self):
        return str(self.getData()) # the only name to speek of the name of the variable

    def getRange_call(self, rowRange = None, colRange = None):
        if rowRange == None: return str(self.getData())
        else: return str(self.getData())+'['+unicode(rowRange)+']'
        
        