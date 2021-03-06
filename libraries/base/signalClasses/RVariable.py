"""RVariable
.. helpdoc::
This signal class is the most generic.  All R signals should inherit from this class.
"""

"""
.. convertTo:: ``
.. convertFrom:: ``
"""

from signals import BaseRedRVariable
from RSession import Rcommand
from RSession import require_librarys
from RSession import assign

class RVariable(BaseRedRVariable): 
    convertToList = []
    convertFromList = []
    def __init__(self, widget, data, parent = None, checkVal = False, **kwargs):
        BaseRedRVariable.__init__(self,widget = widget, data = data, **kwargs)
        if not parent:
            parent = data
        self.parent = parent
        self.R = Rcommand
        self.assignR = assign
        self.require_librarys = require_librarys
        self.reserved = ['data', 'parent', 'R', 'dictAttrs']
        self.__package__ = 'base'
    def __str__(self):
        ## print output for the class
        
        return '###Signal Class: '+unicode(self.__class__)+'; Data: '+str(self.getData())+'; Parent: '+self.parent+'; Attributes: '+unicode(self.dictAttrs)
    def getClass_call(self):
        return 'class('+str(self.getData())+')'
        
    def getClass_data(self):
        return self.R(self.getClass_call(), silent = True)
    def _simpleOutput(self, subsetting = ''):
        text = 'R Data Variable Name: '+str(self.getData())+'\n\n'
        return text
    def getData(self):
        self.widget.expandData() # this exapnds the data of the parent widget at the time that the data is requested.  This will exapnd all widget variables.
        print "Returning string of data"
        return str(self.data)
    def summary(self):
        return '\n'.join(self.R('capture.output(summary('+str(self.getData())+'))', wantType = 'list'))
    def _fullOutput(self, subsetting = ''):
        text = self._simpleOutput()+'\n\n'
        text += 'R Data Variable Value: '+self.R('paste(capture.output('+str(self.getData())+subsetting+'), collapse = "\n")')+'\n\n'
        text += 'R Parent Variable Name: '+self.parent+'\n\n'
        text += 'R Parent Variable Value: '+self.R('paste(capture.output('+self.parent+subsetting+'), collapse = "\n")')+'\n\n'
        text += 'Class Dictionary: '+unicode(self.dictAttrs)+'\n\n'
        return text
    # def getAttrOutput_call(self, item, subsetting = ''):
        # print '|#|', item, subsetting
        # call = 'paste(capture.output('+self.__getitem__(item)+subsetting+'), collapse = "\n")'
        # return call
    # def getAttrOutput_data(self, item, subsetting = ''):
        # return self.R(self.getAttrOutput_call(item = item, subsetting = subsetting))
    def getSimpleOutput(self, subsetting = ''):
        # return the text for a simple output of this variable
        text = 'Simple Output\n\n'
        text += 'Class: '+self.getClass_data()+'\n\n'
        text += self._simpleOutput(subsetting)
        return text
    def getFullOutput(self, subsetting = ''):
        text = 'Full Output\n\n'
        text += 'Class: '+self.getClass_data()+'\n\n'
        text += self._fullOutput(subsetting)
        return text
    def _convertToVariable(self):
        return self
    def convertToClass(self, varClass):
        return self
    def getData(self):
        return RVarStr(self.widgetID, self.data)
        
import redRRObjects

class RVarStr():
    def __init__(self, widgetID, data):
        self.widgetID = widgetID
        self.data = data
        
    def __str__(self):
        redRRObjects.ensureVars(self.widgetID)
        return str(self.data)