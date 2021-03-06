"""
.. helpdoc::
Generates a table that is identical to the input table but with a new column added that contains the names of a series of selected columns that is either the greatest of the selected columns or the least of the selected columns.  This only works on numbers.
"""

"""
<widgetXML>    
    <name>Column Matcher</name>
    <icon>default.png</icon>
    <tags> 
        <tag>Data Manipulation</tag> 
    </tags>
    <summary>Generates a table that is identical to the input table but with a new column added that contains the names of a series of selected columns that is either the greatest of the selected columns or the least of the selected columns.  This only works on numbers.</summary>
    <author>
        <authorname>Red-R Core Development Team</authorname>
        <authorcontact>www.red-r.org</authorcontact>
    </author>
</widgetXML>
"""

"""
<name>Column Matcher (Max/Min Column)</name>
<author>Kyle R Covington kyle@red-r.org</author>
<description>Generates a table that is identical to the input table but with a new column added that contains the names of a series of selected columns that is either the greatest of the selected columns or the least of the selected columns.  This only works on numbers.</description>
<RFunctions>graphics:hist</RFunctions>
<tags>Data Manipulation</tags>
<icon></icon>
"""
from OWRpy import * 
import redRGUI, signals
import OWGUI 
import redRi18n
_ = redRi18n.get_(package = 'base')
class colMatcher(OWRpy): 
    def __init__(self, **kwargs):
        OWRpy.__init__(self, **kwargs)
        self.RFunctionParam_x = ''
        self.setRvariableNames(['newmat', 'compColumn'])
        
        """.. rrsignals::"""
        self.inputs.addInput('id0', _('Data Table'), signals.base.RDataFrame, self.processx)
        
        """.. rrsignals::"""
        self.outputs.addOutput('data', _('Data Table'), signals.base.RDataFrame)

        
        box = redRGUI.base.groupBox(self.controlArea, _("Column Selector"))
        self.columnBox = redRGUI.base.listBox(box, label = _('Column Box'), toolTip = _('Select the columns to find the largest or smallest value'))
        self.columnBox.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.glSelector = redRGUI.base.radioButtons(box, label = _('Comarison Selection'), buttons = [_('Greater Than'), _('Less Than')], setChecked = _('Greater Than'))

        redRGUI.base.commitButton(self.bottomAreaRight, _("Commit"), callback = self.commitFunction)
    def processx(self, data):
        if data:
            self.RFunctionParam_x=data.getData()
            #self.commitFunction()
            self.columnBox.update(self.R('colnames('+self.RFunctionParam_x+')', wantType = 'list'))
            self.commitFunction()
            
        else:
            self.RFunctionParam_x = ''
    def commitFunction(self):
        if self.RFunctionParam_x == '': return
        if len(self.columnBox.selectedItems()) < 2: return  # must select at least two columns to compare.
        ## make a new column that has the names of the columns that are greatest.
        if str(self.glSelector.getChecked()) == _('Greater Than'):
            gl = 0
        else:
            gl = 1
        self.R(self.Rvariables['compColumn']+'<-NULL', wantType = 'NoConversion')
        names = [str(i.text()) for i in self.columnBox.selectedItems()]
        compMatrix = self.R('as.matrix('+self.RFunctionParam_x+'[,c("'+'","'.join(names)+'")])')
        for l in compMatrix:
            for i in range(len(l)):
                if gl:
                    if l[i] == mim(l):
                        self.R(self.Rvariables['compColumn']+'<-c('+self.Rvariables['compColumn']+', "'+names[i]+'")', wantType = 'NoConversion')
                else:
                    if l[i] == max(l):
                        self.R(self.Rvariables['compColumn']+'<-c('+self.Rvariables['compColumn']+', "'+names[i]+'")', wantType = 'NoConversion')
        
        self.R(self.Rvariables['newmat']+'<-cbind('+self.RFunctionParam_x+', '+self.Rvariables['compColumn']+')', wantType = 'NoConversion')
        newData = signals.base.RDataFrame(self, data = self.Rvariables['newmat'])
        self.R('rm('+self.Rvariables['compColumn']+')', wantType = 'NoConversion')
        self.rSend('data', newData)
    