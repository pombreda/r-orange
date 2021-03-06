"""
.. helpdoc::
Combining data from different tables is often required during data mining.  The Merge Data widget combines data in a variety of ways.

Once data is connected it is loaded into the appropriate channel and the names of the columns are shown in the selection list boxes under the headings 'Select Columns to Merge From A/B'.  The name Rownames will always be displayed in these for merging on rownames.  If there are two identically named columns in your data these will be the default merge columns on widget connect.  After selecting a column name or to merge using rownames your data will be merged and three data tables will be sent.  One with the merger of all of the data through the Merge_All slot, and two others with the merger on only one of the tables (ex. All rows from table A merged with the matching columns from table B).
"""

"""
<widgetXML>    
    <name>Merge</name>
    <icon>merge2.png</icon>
    <tags> 
        <tag>Data Manipulation</tag> 
    </tags>
    <summary>Merge two datasets</summary>
    <author>
        <authorname>Red-R Core Development Team</authorname>
        <authorcontact>www.red-r.org</authorcontact>
    </author>
</widgetXML>
"""

"""
<name>Merge</name>
<tags>Data Manipulation</tags>
<icon>merge2.png</icon>
"""

from OWRpy import *
import redRGUI, signals
import redRGUI

import redRi18n
_ = redRi18n.get_(package = 'base')
class mergeR(OWRpy):
    globalSettingsList = ['commit']

    def __init__(self, **kwargs):
        OWRpy.__init__(self, **kwargs)
        
        # self.dataParentA = {}
        # self.dataParentB = {}
        self.dataA = ''
        self.dataB = ''
        
        """.. rrsignals::"""
        self.inputs.addInput('id0', _('Dataset A'), signals.base.RDataFrame, self.processA)
        
        """.. rrsignals::"""
        self.inputs.addInput('id1', _('Dataset B'), signals.base.RDataFrame, self.processB)

        """.. rrsignals::"""
        self.outputs.addOutput('id0', _('Merged'), signals.base.RDataFrame)

        #default values        
        self.colAsel = None
        self.colBsel = None
        #self.forceMergeAll = 0 #checkbox value for forcing merger on all data, default is to remove instances from the rows or cols.
        
        #set R variable names
        self.setRvariableNames(['merged'])
                
        #GUI
        box = redRGUI.base.widgetBox(self.controlArea,orientation='horizontal')
    
        self.colA = redRGUI.base.listBox(box, label=_('Columns to Merge From A'), callback = self.setcolA)
        self.colB = redRGUI.base.listBox(box, label=_('Columns to Merge From B'),  callback = self.setcolB)
        

        self.sortOption = redRGUI.base.checkBox(self.bottomAreaLeft, label=_('Sort by Selected Column'), displayLabel=False, 
        buttons = [_('Sort by Selected Column')], 
        toolTips = [_('logical. Should the results be sorted on the by columns?')])
        self.rownamesOption = redRGUI.base.checkBox(self.bottomAreaLeft, label = _('Include Row Names in Merge'), displayLabel = False, buttons = [_('Include Row in Merge')], toolTips = [_('This will include the row names in the data after merge.')], setChecked = [_('Include Row in Merge')])
        self.sortOption.layout().setAlignment(Qt.AlignLeft)
        
        self.mergeOptions = redRGUI.base.radioButtons(self.bottomAreaCenter,label=_('Type of merge'), displayLabel=False,
        buttons=['A+B','B+A','AB'],setChecked='A+B',
        orientation='horizontal')
        
        self.mergeOptions.layout().setAlignment(Qt.AlignCenter) 
        
        self.commit = redRGUI.base.commitButton(self.bottomAreaRight, _('Commit'), callback = self.run, 
        processOnChange=True,processOnInput=True)
        
    def processA(self, data):
        #print 'processA'
        if not data:
            self.colA.clear()
            return 
        self.dataA = unicode(data.getData())
        self.dataParentA = data
        colsA = self.R('colnames('+self.dataA+')') #collect the sample names to make the differential matrix
        
        if type(colsA) is str:
            colsA = [colsA]
        colsA.insert(0, 'Rownames')
        self.colA.update(colsA)

        if self.commit.processOnInput():
            self.run()
        
    def processB(self, data):
        #print 'processB'
        if not data:
            self.colB.clear()
            return 
        self.dataB = unicode(data.getData())
        self.dataParentB = data
        colsB = self.R('colnames('+self.dataB+')') #collect the sample names to make the differential matrix
        if type(colsB) is str:
            colsB = [colsB]
        colsB.insert(0, 'Rownames')
        self.colB.update(colsB)
                
        if self.commit.processOnInput():
            self.run()
    
    def run(self):
        if self.dataA == '':
            self.status.setText(_("Dataset A Does Not Exist"))
            return
        if self.dataB == '': 
            self.status.setText(_("Dataset B Does Not Exist"))
            return
        
        if len(self.colA.selectedItems()) == 0 or len(self.colB.selectedItems()) == 0:
            self.status.setText(_('Please make valid column selections'))
            return
        if self.dataA != '' and self.dataB != '':
            h = self.R('intersect(colnames('+self.dataA+'), colnames('+self.dataB+'))')
        else: h = None
        
        # make a temp variable that is the combination of the parent frame and the cm for the parent.
        if self.mergeOptions.getChecked() =='A+B':
            options = 'all.x=T'
        elif self.mergeOptions.getChecked() =='B+A':
            options = 'all.y=T'
        else:
            options = '' #'all.y=T, all.x=T'
        if _('Sort by Selected Column') in self.sortOption.getChecked():
            options += ', sort=TRUE'
            
        if self.colAsel == None and self.colBsel == None and type(h) is str: 
            self.colA.setCurrentRow( self.R('which(colnames('+self.dataA+') == "' + h + '")-1'))
            self.colB.setCurrentRow( self.R('which(colnames('+self.dataB+') == "' + h + '")-1'))
            
            self.R(self.Rvariables['merged']+'<-merge('+self.dataA+', '+self.dataB+','+options+')', wantType = 'NoConversion')
            self.sendMe()
        elif self.colAsel and self.colBsel:
            if self.colAsel == 'Rownames': cas = '0'
            else: cas = self.colAsel
            if self.colBsel == 'Rownames': cbs = '0'
            else: cbs = self.colBsel
            
            if 'Include Row in Merge' in self.rownamesOption.getChecked():
                self.R(self.Rvariables['merged']+'<-merge(as.data.frame(cbind(as.data.frame('+self.dataA+'), RownamesA = rownames(as.data.frame('+self.dataA+')))), as.data.frame(cbind(as.data.frame('+self.dataB+'), RownamesB = rownames(as.data.frame('+self.dataB+')))), by.x='+cas+', by.y='+cbs+','+options+')', wantType = 'NoConversion')
            else:
                self.R(self.Rvariables['merged']+'<-merge(as.data.frame('+self.dataA+'), as.data.frame('+self.dataB+'), by.x='+cas+', by.y='+cbs+','+options+')', wantType = 'NoConversion')
            # if self.colAsel == 'Rownames':
                # self.R('rownames('+self.Rvariables['merged']+')<-rownames('+self.dataA+')', wantType = 'NoConversion')
            self.sendMe()
        else:
            self.status.setText(_("Dataset failed to find a match!"))

    def sendMe(self,kill=False):
        """Sends the data to the canvas.  This step also forces the data to have syntactically valid names.  Failure to do so can cause problems later."""
        self.R('names(%(DATA)s)<-make.names(names(%(DATA)s), unique = TRUE)' % {'DATA':self.Rvariables['merged']}, wantType = 'NoConversion')
        newDataAll = signals.base.RDataFrame(self, data = self.Rvariables['merged'])
        newDataAll.dictAttrs = self.dataParentB.dictAttrs.copy()
        newDataAll.dictAttrs.update(self.dataParentA.dictAttrs)
        print 'Moving to send'
        self.rSend("id0", newDataAll)
    
    def setcolA(self):
        try:
            self.colAsel = '\''+unicode(self.colA.currentSelection()[0])+'\''
            if self.colAsel == '\'Rownames\'':
                self.colAsel = '0'
        except:
            self.status.setText(_("Failed to set column A"))
            return
        if self.commit.processOnChange():
            self.run()
    def setcolB(self):
        try:
            self.colBsel = '\''+unicode(self.colB.currentSelection()[0])+'\''
            if self.colBsel == '\'Rownames\'':
                self.colBsel = '0'
        except:
            self.status.setText(_("Failed to set column B"))
            return
        if self.commit.processOnChange():
            self.run()
