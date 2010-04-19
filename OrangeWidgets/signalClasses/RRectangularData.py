# Abstract rectangular data class RRectangularData, base class for objects such as data.frame and matrix
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from RvarClasses import RVariable

class RRectangularData(RVariable):
    def __init__(self, data, cm = None, parent = None, checkVal = True):
        RVariable.__init__(self, data = data, parent = parent, checkVal = False)
        #if checkVal and self.getClass_data() != 'data.frame':
            #raise Exception # there this isn't the right kind of data for me to get !!!!!
        self.cm = cm
        self.reserved.append('cm')
    def copy(self):
        newVariable = RRectangularData(data = self.data, parent = self.parent, cm = self.cm)
        newVariable.dictAttrs = self.dictAttrs
        return newVariable
    def convertToClass(self, varClass):
        if varClass == RVariable:
            return self._convertToVariable()
        else:
            raise Exception
    def _convertToVariable(self):
        return self.copy()
        
    def getSimpleOutput(self, subsetting = '[1:5, 1:5]'):
        # return the text for a simple output of this variable
        text = 'Simple Output\n\n'
        text += 'Class: '+self.getClass_data()+'\n\n'
        text += self._simpleOutput(subsetting)
        return text
    def _fullOutput(self, subsetting = ''):
        text = self._simpleOutput()+'\n\n'
        text += 'R Data Variable Value: '+self.getAttrOutput_data('data', subsetting)+'\n\n'
        dims = self.getDims_data()
        text += 'R Data Variable Size: '+str(dims[0])+' Rows and '+str(dims[1])+' Columns\n\n'
        text += 'R Parent Variable Name: '+self.parent+'\n\n'
        text += 'R Parent Variable Value: '+self.getAttrOutput_data('parent', subsetting)+'\n\n'
        text += 'Class Dictionary: '+str(self.dictAttrs)+'\n\n'
        return text
    def getRownames_call(self):
        return 'rownames('+self.data+')'
    def getRownames_data(self):
        return self.R(self.getRownames_call(), wantType = 'list', silent = True)
    def getItem_call(self, item):
        if type(item) in [int, float, long]:
            item = int(item)
            return self.data+'[,'+str(item)+']'
        elif type(item) in [str]:
            return self.data+'[,\''+str(item)+'\']'
        elif type(item) in [list]:
            newItemList = []
            for i in item:
                if type(i) in [int, float, long]:
                    newItemList.append(str(int(i)))
                elif type(i) in [str]:
                    newItemList.append('\"'+str(i)+'\"')
            return self.data+'[,c('+str(newItemList)[1:-1]+')]'
        else:
            return self.data #just return all of the data and hope the widget picks up from there
    def getItem_data(self, item, wantType = 'dict'): # native functionality is to return a dict (this is what lists do)
        call = self.getItem_call(item)
        if call != None:
            if type(item) in [int, str, long, float]:
                return self.R(call, wantType = wantType, silent = True) # returns a single column
            elif type(item) in [list] and wantType not in ['array', 'list']: # returns a dict
                return self.R(call, wantType = wantType, silent = True)
                
            elif type(item) in [list] and wantType in  ['array', 'list']: # returns a list of lists
                return self.R('as.matrix('+call+')', wantType = wantType, silent = True)
        else:
            print 'No data to return'
            return {}
    def getColumnnames_call(self):
        return self.getNames_call()
    def getColumnnames_data(self):
        return self.getNames_data()
    def getRange_call(self, rowRange = None, colRange = None):
        if rowRange == None and colRange == None:
            return self.data
        if rowRange:
            rr = str(rowRange)
        else:
            rr = ''
        if colRange:
            cr = str(colRange)
        else:
            cr = ''
        return self.data+'['+rr+','+cr+']'
    def getRowData_call(self, item):
        if type(item) in [int, float, long]:
            item = int(item)
            return self.data+'['+str(item)+',]'
        elif type(item) in [str]:
            return self.data+'[\''+str(item)+'\',]'
        elif type(item) in [list]:
            newItemList = []
            for i in item:
                if type(i) in [int, float, long]:
                    newItemList.append(str(int(i)))
                elif type(i) in [str]:
                    newItemList.append('\"'+str(i)+'\"')
            return self.data+'[c('+str(newItemList)[1:-1]+'),]'
        else:
            return self.data #just return all of the data and hope the widget picks up from there
    def getRowData_data(self, item):
        output = self.R(self.getRowData_call(item), wantType = 'list', silent = True)
        return output
        
    def getDims_data(self):
        return self.R(self.getDims_call(), wantType = 'list')
        
    def getDims_call(self):
        return 'dim('+self.data+')'