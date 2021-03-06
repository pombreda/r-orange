"""Read File widget


.. helpdoc::
Calculates principal components for a numeric matrix.
"""


"""<widgetXML>
    <name>Principal Component</name>
    <icon>stats.png</icon>
    <summary>Calculates principal components for a numeric matrix.</summary>
    <tags>
        <tag priority="10">
            Parametric
        </tag>
    </tags>
    <author>
        <authorname>Red-R Core Development Team</authorname>
        <authorcontact>www.red-r.org</authorcontact>
    </author>
    </widgetXML>
"""

"""
<name>Principal Component</name>
<icon>stats.png</icon>
<tags>Parametric</tags>
"""
from OWRpy import * 
import redRGUI, signals
import OWGUI 
import redRGUI 

class prcomp(OWRpy): 
    globalSettingsList = ['commit']
    def __init__(self, **kwargs):
        OWRpy.__init__(self, **kwargs)
        self.setRvariableNames(["prcomp"])
         
        self.RFunctionParam_x = ''
        self.inputs.addInput('id0', 'x', signals.base.RDataFrame, self.processx)

        self.outputs.addOutput('id0', 'prcomp Output', signals.base.RModelFit)
        self.outputs.addOutput('id1', 'Scaled Data', signals.base.RMatrix)
        self.options = redRGUI.base.checkBox(self.controlArea, label = 'Options:', buttons = ['Center', 'Scale'])
        self.options.setChecked(['Center', 'Scale'])

        self.commit = redRGUI.base.commitButton(self.bottomAreaRight, "Commit", callback = self.commitFunction,
        processOnInput=True)
    def processx(self, data):
        if data:
            self.RFunctionParam_x=data.getData()
            if self.commit.processOnInput():
                self.commitFunction()
        else:
            self.RFunctionParam_x = ''
    def commitFunction(self):
        if unicode(self.RFunctionParam_x) == '': return
        injection = []
        if 'Center' in self.options.getChecked():
            injection.append('center = TRUE')
        else:
            injection.append('center = FALSE')
        if 'Scale' in self.options.getChecked():
            injection.append('scale = TRUE')
        else:
            injection.append('scale = FALSE')
        inj = ','.join(injection)
        self.R(self.Rvariables['prcomp']+'<-prcomp(x=data.matrix('+unicode(self.RFunctionParam_x)+'), '+inj+')')
        
        newPRComp = signals.base.RModelFit(self, data = self.Rvariables['prcomp'])
        self.rSend("id0", newPRComp)
        newPRCompMatrix = signals.base.RMatrix(self, data = self.Rvariables['prcomp']+'$x')
        self.rSend("id1", newPRCompMatrix)
