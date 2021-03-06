"""
.. helpdoc::
The apply function takes an array (an n-dimentional rectangular datasets) as an input object and applies the function specified either by the 'Select Function' box or any arbitrary function in the 'Function' box.  Any additional parameters to the function can be input in the 'Additional Parameters' line.  

Users can use either the 'To' box or the 'Array Index' box to specify the index on which the function will be applied.

The result is an (n-1)-dimentional array containing the results of the function applied across the array.

For example:<br />
Apply the function max across the following array, with index 1 (Rows).

    [[1, 2, 3]
     [4, 5, 6]
     [7, 8, 9]]
     
Results in this vector; [3, 6, 9]
    
While applied across the columns would result in: [7, 8, 9].
"""

"""
<widgetXML>    
    <name>Apply</name>
    <icon>default.png</icon>
    <tags> 
        <tag>Data Manipulation</tag> 
    </tags>
    <summary>Apply a function across an matrix or array.</summary>
    <author>
        <authorname>Red-R Core Development Team</authorname>
        <authorcontact>www.red-r.org</authorcontact>
    </author>
</widgetXML>
"""
from OWRpy import * 
import redRGUI, signals 

from libraries.base.widgetImport import *
import redRi18n
_ = redRi18n.get_(package = 'base')
class apply(OWRpy): 
    globalSettingsList = ['commit']
    def __init__(self, **kwargs):
        OWRpy.__init__(self, **kwargs)
        self.setRvariableNames(["apply"])
        self.numDims = 2
        self.data=None
        
        """.. rrsignals::"""
        self.inputs.addInput('id0', _('X'), [signals.base.RMatrix, signals.base.RDataFrame], self.processX)

        """.. rrsignals::"""
        self.outputs.addOutput('id0', _('apply Output'), signals.base.RDataFrame)

        
        area = redRGUI.base.widgetBox(self.controlArea,orientation='vertical')       
        
        box = redRGUI.base.widgetBox(area)
        box.setMinimumWidth(200)
        area.layout().setAlignment(box,Qt.AlignLeft)
        
        self.functions =  redRGUI.base.listBox(box,  label = _("Select Function"),
        items=['mean','median','max','min','sum','log2', 'log10', 'var', 'custom'],callback=self.functionSelect)
        self.functions.setSelectionMode(QAbstractItemView.SingleSelection)
        
        #redRGUI.base.separator(box,height=10)
        self.functionText = redRGUI.base.textEdit(box,label=_('Function:'), orientation='vertical')
        self.parameters = redRGUI.base.lineEdit(box,label=_('Additional Parameters:'), orientation='vertical')
        
        self.customFunctionText = redRGUI.base.textEdit(box, label = _('Custom Function'), orientation = 'vertical', toolTip = _('Takes the object data as it\'s parameters, this is the vector of data across the margin being used.  May cause errors in use that are not the fault of the widget developers.'))
        
        
        self.demension =  redRGUI.base.radioButtons(box, label = _("To:"), buttons = [_('All'), _('Rows'), _('Columns'),_('Other')],
        setChecked=_('Rows'), orientation='horizontal',callback= lambda: self.dimensionChange(1))
        self.indexSpinBox = redRGUI.base.spinBox(self.demension.box, label=_('Demension'), displayLabel=False,
        min = 1, value = 1, callback= lambda: self.dimensionChange(2))
        buttonBox = redRGUI.base.widgetBox(box,orientation='horizontal')
        
        
        self.commit = redRGUI.base.commitButton(buttonBox, _("Commit"), alignment=Qt.AlignLeft, 
        callback = self.commitFunction, processOnInput=True, processOnChange=True)
        
        self.dataTable = redRGUI.base.textEdit(area, label = _('Data Sample'))
        self.outputTable = redRGUI.base.filterTable(area,label=_('Results of Apply'), sortable=True)

    def dimensionChange(self,type):
        if type == 1:
            if self.demension.getChecked() ==_('Rows'):
                self.indexSpinBox.setValue(1)
            else:
                self.indexSpinBox.setValue(2)
        else:
            if self.indexSpinBox.value() == 1:
                self.demension.setChecked(_('Rows'))
            elif self.indexSpinBox.value() == 2:
                self.demension.setChecked(_('Columns'))
            else:
                self.demension.setChecked(_('Other'))
            
    def processX(self, data):
        if data:
            self.data=data.getData()
            self.numDims = self.R('length(dim(%s))' % self.data)
            self.indexSpinBox.setMaximum(self.numDims)
            self.dataTable.captureOutput('head(%s)' % self.data)
            if self.commit.processOnInput():
                self.commitFunction()
        else:
            self.data=None
    def functionSelect(self):
        selection = self.functions.currentSelection()
        f = selection[0].split('\n--')
        #print f
        self.functionText.setText(f[0])
        self.parameters.setText(', '.join(f[1:]))
        if self.commit.processOnChange():
            self.commitFunction()
    def commitFunction(self):
        func = unicode(self.functionText.toPlainText())
        paramText = unicode(self.parameters.text())
        if unicode(self.data) == None or func =='': return
        
        params = []
        for x in paramText.split(','):
            if x.strip() !='':
                params.append(x.strip())
            
        saveAs = func 
        if len(params):
            saveAs += '\n--' + '\n--'.join(params)
        
        if not self.functions.findItems(saveAs,Qt.MatchExactly):
            self.functions.addItem(saveAs, saveAs)
            self.saveGlobalSettings()
        
        if self.demension.getChecked() != _('All'):
            injection = []
            string = 'MARGIN = %s' % unicode(int(self.indexSpinBox.value()))
            injection.append(string)
            
            if self.functions.currentSelection()[0].split('\n--')[0] == 'custom':
                try:
                    self.R('tempFun<-function(data){%s}' % self.customFunctionText.toPlainText(), wantType = redR.NOCONVERSION)
                    string = 'FUN=tempFun'
                    injection.append(string)
                except: return
            else:
                string = 'FUN='+unicode(self.functionText.toPlainText())
                injection.append(string)
            
            injection.extend(params)
            
            inj = ','.join(injection)
            
            # try:
            self.R(self.Rvariables['apply']+'<- as.data.frame(apply(X='+unicode(self.data)+','+inj+'))', wantType = 'NoConversion')
        else:
            self.R('%s<-as.data.frame(%s(%s))' % (self.Rvariables['apply'], unicode(self.functionText.toPlainText()), self.data), wantType = redR.NOCONVERSION)
            
        newData = signals.base.RDataFrame(self, data = self.Rvariables['apply'])
        self.outputTable.setTable(newData)
        self.rSend("id0", newData)
        # except: 
            # self.R('%s <- NULL'%self.Rvariables['apply'],silent=True)
            # self.outputTable.clear()
            # self.rSend("id0", None)
        

