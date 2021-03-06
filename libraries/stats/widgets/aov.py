"""AOV


.. helpdoc::
Performed ANOVA on any model or data received.  This can result in errors if inappropriate models are supplied.
"""


"""<widgetXML>
    <name>
        ANOVA
    </name>
    <icon>
        default.png
    </icon>
    <summary>
        Performed ANOVA on any model or data received.  This can result in errors if inappropriate models are supplied.
    </summary>
    <tags>
        <tag priority="10">
            Advanced Stats
        </tag>
    </tags>
    <author>
        <authorname>Red-R Core Development Team</authorname>
        <authorcontact>www.red-r.org</authorcontact>
    </author>
    </widgetXML>
"""
"""
<name>ANOVA</name>
<author>Generated using Widget Maker written by Kyle R. Covington</author>
<RFunctions>stats:aov</RFunctions>
<tags>Parametric</tags>
<icon>stats.png</icon>
"""
from OWRpy import * 
import redRGUI, signals
import redRGUI 
class aov(OWRpy): 
    def __init__(self, **kwargs):
        OWRpy.__init__(self, **kwargs)
        self.setRvariableNames(["aov"])
        self.data = {}
        self.RFunctionParam_data = ''
        
        """.. rrsignals::
            :description: `A data table to perform the modeling on.`"""
        self.inputs.addInput('id0', 'data', signals.base.RDataFrame, self.processdata)
        
        """.. rrsignals::
            :description: `Output of the ANVOA model..`"""
        self.outputs.addOutput('id0', 'aov Output', signals.base.RModelFit)

        
        box = redRGUI.base.tabWidget(self.controlArea)
        self.standardTab = box.createTabPage(name = "Standard")
        self.advancedTab = box.createTabPage(name = "Advanced")
        
        """.. rrgui::
            :description: `Set the contrasts of the model (Advanced).`
        """
        self.RFunctionParamcontrasts_lineEdit =  redRGUI.base.lineEdit(self.advancedTab,  label = "contrasts:", text = 'NULL')
        
        """.. rrgui::
            :description: `Enter the model formula.`
        """
        self.RFunctionParamformula_formulaEntry =  redRGUI.base.RFormulaEntry(self.standardTab)
        
        """.. rrgui::
            :description: `Set the qr of the model (Advanced).`
        """
        self.RFunctionParamqr_lineEdit =  redRGUI.base.lineEdit(self.advancedTab,  label = "qr:", text = 'TRUE')
        
        """.. rrgui::
            :description: `Set the projections for the model (Advanced).`
        """
        self.RFunctionParamprojections_lineEdit =  redRGUI.base.lineEdit(self.advancedTab,  label = "projections:", text = 'FALSE')
        
        """.. rrgui::
            :description: `Run the model.`
        """
        redRGUI.base.commitButton(self.bottomAreaRight, "Commit", callback = self.commitFunction)
        
        """.. rrgui::
            :description: `Display results from the model.`
        """
        self.RoutputWindow = redRGUI.base.textEdit(self.controlArea, label = "R Output Window")
    def processdata(self, data):
        
        if data:
            self.removeWarning()
            self.RFunctionParam_data=data.getData()
            #self.data = data.copy()
            self.RFunctionParamformula_formulaEntry.update(self.R('names('+self.RFunctionParam_data+')'))
            self.commitFunction()
        else:
            self.RFunctionParam_data=''
            self.RFunctionParamformula_formulaEntry.clear()
    def commitFunction(self):
        if unicode(self.RFunctionParam_data) == '': 
            self.setWarning(id = 'NoData', text = 'No Data connected or data is blank')
            return
        formula = self.RFunctionParamformula_formulaEntry.Formula()
        if formula[0] == '' or formula[1] == '': 
            self.status.setText('Formula Not Entered Correctly')
            return
        injection = []
        string = 'formula='+formula[0]+ ' ~ '+formula[1]
        injection.append(string)
        if unicode(self.RFunctionParamcontrasts_lineEdit.text()) != '':
            string = 'contrasts='+unicode(self.RFunctionParamcontrasts_lineEdit.text())+''
            injection.append(string)
        if unicode(self.RFunctionParamqr_lineEdit.text()) != '':
            string = 'qr='+unicode(self.RFunctionParamqr_lineEdit.text())+''
            injection.append(string)
        if unicode(self.RFunctionParamprojections_lineEdit.text()) != '':
            string = 'projections='+unicode(self.RFunctionParamprojections_lineEdit.text())+''
            injection.append(string)
        inj = ','.join(injection)
        self.R(self.Rvariables['aov']+'<-aov(data='+unicode(self.RFunctionParam_data)+','+inj+')')
        self.R('txt<-capture.output(summary('+self.Rvariables['aov']+'))')
        self.RoutputWindow.clear()
        tmp = self.R('paste(txt, collapse ="\n")')
        self.RoutputWindow.insertPlainText(tmp)
        newData = signals.base.RModelFit(self, data = self.Rvariables["aov"]) # moment of variable creation, no preexisting data set.  To pass forward the data that was received in the input uncomment the next line.
        #newData.copyAllOptinoalData(self.data)  ## note, if you plan to uncomment this please uncomment the call to set self.data in the process statemtn of the data whose attributes you plan to send forward.
        self.rSend("id0", newData)
