"""
.. helpdoc::
Perform base set operations:union, intersect, difference, and equality.<br />
Each of union, intersect, setdiff and setequal will discard any duplicated values in the arguments. 
"""

"""
<widgetXML>    
    <name>Set Operations</name>
    <icon>datatable.png</icon>
    <tags> 
        <tag>Data Manipulation</tag> 
    </tags>
    <summary>Perform base set operations:union, intersect, difference, and equality</summary>
    <author>
        <authorname>Red-R Core Development Team</authorname>
        <authorcontact>www.red-r.org</authorcontact>
    </author>
</widgetXML>
"""

"""
<name>Set Operations</name>
<tags>Data Manipulation</tags>
<icon>datatable.png</icon>
"""

from OWRpy import * 
import redRGUI, signals
import redRGUI 

import redRi18n
_ = redRi18n.get_(package = 'base')
class setOperations(OWRpy): 
    globalSettingsList = ['commit']
    def __init__(self, **kwargs):
        OWRpy.__init__(self, **kwargs)
        self.setRvariableNames(["intersect"])
        self.dataA = None
        self.dataB = None
        
        """.. rrsignals::"""
        self.inputs.addInput('id0', _('Input Data A'), signals.base.RList, self.processA)
        
        """.. rrsignals::"""
        self.inputs.addInput('id1', _('Input Data B'), signals.base.RList, self.processB)

        """.. rrsignals::"""
        self.outputs.addOutput('id0', _('intersect Output'), signals.base.RVector)
        
        box = redRGUI.base.widgetBox(self.controlArea,orientation = 'vertical')
        dataSetBox = redRGUI.base.widgetBox(box,orientation = 'horizontal')
        #pickA = redRGUI.base.groupBox(dataSetBox, "Dataset A:")
        self.colA = redRGUI.base.listBox(dataSetBox, label = _('Input Data A'), callback = self.onSelect)
        
        #pickB = redRGUI.base.groupBox(dataSetBox, "Dataset B:")
        self.colB = redRGUI.base.listBox(dataSetBox, label = _('Input Data B'), callback = self.onSelect)

        self.resultInfo = redRGUI.base.textEdit(box,label=_('Results'), displayLabel=False,includeInReports=False,
        editable=False, alignment=Qt.AlignHCenter)
        self.resultInfo.setMaximumWidth(170)
        self.resultInfo.setMaximumHeight(25)
        self.resultInfo.setMinimumWidth(170)
        self.resultInfo.setMinimumHeight(25)
        #box.layout().setAlignment(self.resultInfo,Qt.AlignHCenter)
        self.resultInfo.hide()
        self.type = redRGUI.base.radioButtons(self.bottomAreaLeft,  label = _("Perform"), 
        buttons = [('intersect', _('Intersect')), ('union', _('Union')), ('setdiff', _('Set Difference')), ('setequal', _('Set Equal'))],setChecked='intersect',
        orientation='horizontal',callback=self.onTypeSelect)
        
        commitBox = redRGUI.base.widgetBox(self.bottomAreaRight,orientation = 'horizontal')
        self.bottomAreaRight.layout().setAlignment(commitBox, Qt.AlignBottom)

        self.commit = redRGUI.base.commitButton(commitBox, _("Commit"), callback = self.commitFunction, processOnChange=True, processOnInput=True)
    
    def onSelect(self):
        if self.commit.processOnChange():
            self.commitFunction()
    def onTypeSelect(self):
        self.resultInfo.setPlainText('')
        if self.type.getCheckedId() == 'setequal':
            self.resultInfo.show()
        else:
            self.resultInfo.hide()
        
        if self.commit.processOnChange():
            self.commitFunction()
            
    def processA(self, data):
        #print 'processA'
        if not data:
            self.colA.update([])
            return 
            
        self.dataA = data.getData()
        colsA = self.R('names(%s)' % self.dataA,wantType='list')
        self.colA.update(colsA)
        
        if self.commit.processOnInput():
            self.commitFunction()
    def processB(self, data):
        if not data:
            self.colB.update([])
            return 
        self.dataB = data.getData()
        colsB = self.R('names(%s)' % self.dataB,wantType='list') 

        self.colB.update(colsB)

        if self.commit.processOnInput():
            self.commitFunction()
    def commitFunction(self):
        if self.dataA and self.dataB:
            h = self.R('intersect(names(%s), names(%s))' % (self.dataA, self.dataB),wantType='list')
        else: 
            return
            
        if self.colA.selectedItems():
            nameA = self.colA.selectedIds()[0]
        else:
            nameA = None
        if self.colB.selectedItems():
            nameB = self.colB.selectedIds()[0]
        else:
            nameB = None
        
        func = self.type.getCheckedId()
            
        if nameA and nameB:
            self.R(self.Rvariables['intersect']+'<-%s(y=%s[["%s"]],x=%s[["%s"]])' 
            % (func, self.dataA,nameA,self.dataB,nameB), wantType = 'NoConversion')
        elif len(h) ==1:
            self.R(self.Rvariables['intersect']+'<-%s(y=%s[["%s"]],x=%s[["%s"]])' 
            % (func, self.dataA,h[0],self.dataB,h[0]), wantType = 'NoConversion')
        else:
            self.status.setText(_('You must select an item to compare from each list.'))
            return
            
        if self.type.getCheckedId() == 'setequal':
            eq = self.R(self.Rvariables['intersect'])
            if eq:
                self.resultInfo.setPlainText('%s is equal to %s' % (nameA, nameB))
            else:
                self.resultInfo.setPlainText('%s is not equal to %s' % (nameA, nameB))
        else:
            newData = signals.base.RVector(self, data = self.Rvariables["intersect"])
            self.rSend("id0", newData)
    
