"""
.. helpdoc::
"""

"""
<widgetXML>    
    <name>Row or Column Binding</name>
    <icon>default.png</icon>
    <tags> 
        <tag>Prototypes</tag> 
    </tags>
    <summary>Row bind data</summary>
    <author>
        <authorname>Red-R Core Development Team</authorname>
        <authorcontact>www.red-r.org</authorcontact>
    </author>
</widgetXML>
"""

"""
<name>Row or Column Binding</name>
<tags>Prototypes</tags>
"""
from OWRpy import * 
import redRGUI, signals
import redRi18n
_ = redRi18n.get_(package = 'base')
class RedRrbind(OWRpy): 
    settingsList = []
    def __init__(self, **kwargs):
        OWRpy.__init__(self, **kwargs)
        self.setRvariableNames(["rbind"])
        self.data = {}
        self.RFunctionParam_x = ''
        
        """.. rrsignals::"""
        self.inputs.addInput("x", _("Data"), [signals.base.RDataFrame, signals.base.RDataFrame], self.processx, multiple = True)
        
        """.. rrsignals::"""
        self.outputs.addOutput("rbind Output",_("Joined Data"), signals.base.RDataFrame)
        
        self.rowcolnames = redRGUI.base.comboBox(self.controlArea, label = _('Source of Row / Column Names:'), callback = self.commitFunction)
        self.bindingMode = redRGUI.base.radioButtons(self.controlArea, label = _('Binding Mode:'), buttons = [_('Row'), _('Column')], setChecked = _('Row'))
        self.RFunctionParamdeparse_level_lineEdit = redRGUI.base.lineEdit(self.controlArea, label = _("Deparse Level:"), text = '1')
        redRGUI.base.commitButton(self.bottomAreaRight, _("Commit"), callback = self.commitFunction)
    def processx(self, data, id):
        
        if data:
            self.data[id] = data.getData()
            
            #self.data = data
            self.rowcolnames.update(self.data.keys())
            self.commitFunction()
        else:
            del self.data[id]
    def commitFunction(self):
        if len(self.data) < 2: return
        injection = []
        if unicode(self.RFunctionParamdeparse_level_lineEdit.text()) != '':
            string = 'deparse.level='+unicode(self.RFunctionParamdeparse_level_lineEdit.text())+''
            injection.append(string)
        inj = ''.join(injection)
        if unicode(self.bindingMode.getChecked()) == 'Row':
            function = 'rbind'
        else:
            function = 'cbind'
        self.R(self.Rvariables['rbind']+'<-'+function+'('+','.join([i for k, i in self.data.items()])+','+inj+')', wantType = 'NoConversion')
        newData = signals.base.RDataFrame(self, data = 'as.data.frame('+self.Rvariables["rbind"]+')') # moment of variable creation, no preexisting data set.  To pass forward the data that was received in the input uncomment the next line.
        #newData.copyAllOptinoalData(self.data)  ## note, if you plan to uncomment this please uncomment the call to set self.data in the process statemtn of the data whose attributes you plan to send forward.
        if unicode(self.bindingMode.getChecked()) == 'Column':
            self.R('rownames(%s)<-rownames(%s)' % (self.Rvariables['rbind'], self.data[unicode(self.rowcolnames.currentText())]), wantType = 'NoConversion', silent = True)
        else:
            self.R('colnames(%s)<-colnames(%s)' % (self.Rvariables['rbind'], self.data[unicode(self.rowcolnames.currentText())]), wantType = 'NoConversion', silent = True)
        self.rSend("rbind Output", newData)