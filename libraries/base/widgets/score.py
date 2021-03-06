"""
.. helpdoc::
Scores samples based on a scoring matrix.  First merges the data by the row names and extracts only those row names that are in the scoring matrix.  Also any NA values are removed prior to scoring.  Several scoring options are available and include; multiplication (values are multiplied and summed to generate a score for every sample for every level of the scoring matrix), correlation (identical to correlation / variance widget).
"""

"""
<widgetXML>    
    <name>Score</name>
    <icon>default.png</icon>
    <tags> 
        <tag>Data Classification</tag> 
    </tags>
    <summary>Scores samples based on a scoring matrix.  First merges the data by the row names and extracts only those row names that are in the scoring matrix.  Also any NA values are removed prior to scoring.  Several scoring options are available and include; multiplication (values are multiplied and summed to generate a score for every sample for every level of the scoring matrix), correlation (identical to correlation / variance widget).</summary>
    <author>
        <authorname>Red-R Core Development Team</authorname>
        <authorcontact>www.red-r.org</authorcontact>
    </author>
</widgetXML>
"""

"""
<name>Score</name>
<author>Generated using Widget Maker written by Kyle R. Covington, other improvements by Kyle R Covington</author>
<description>Scores samples based on a scoring matrix.  First merges the data by the row names and extracts only those row names that are in the scoring matrix.  Also any NA values are removed prior to scoring.  Several scoring options are available and include; multiplication (values are multiplied and summed to generate a score for every sample for every level of the scoring matrix), correlation (identical to correlation / variance widget).</description>
<RFunctions></RFunctions>
<tags>Data Classification</tags>
<icon>default.png</icon>
"""
from OWRpy import * 
import redRGUI, signals
import redRi18n
_ = redRi18n.get_(package = 'base')
class score(OWRpy): 
    settingsList = []
    def __init__(self, **kwargs):
        OWRpy.__init__(self, **kwargs)
        
        
        self.setRvariableNames(['score', 'mergedmatrix', 'mergedvals', 'tempmerge'])
        self.data = {}
        self.RFunctionParam_data = ''
        self.RFunctionParam_score = ''
        
        """.. rrsignals::"""
        self.inputs.addInput("data", _("Sample Data"), signals.base.RDataFrame, self.processdata)
        
        """.. rrsignals::"""
        self.inputs.addInput("scoremat", _("Scoring Matrix"), signals.base.RDataFrame, self.processscores)
        
        """.. rrsignals::"""
        self.outputs.addOutput("fscoremat",_("Sored Samples"), signals.base.RDataFrame)
        
        """.. rrsignals::"""
        self.outputs.addOutput("maxScore", _("Max Scored Class"), signals.base.RVector)

        wb = redRGUI.base.widgetBox(self.controlArea, orientation = 'vertical')
        self.scoremethod = redRGUI.base.comboBox(wb, label = _('Scoring Method'), items = [_('Multiplication'), _('Correlation')], callback = self.commitFunction)
        redRGUI.base.commitButton(self.bottomAreaRight, _("Commit"), callback = self.commitFunction)
        self.RoutputWindow = redRGUI.base.filterTable(wb,label=_('Scores'), displayLabel=False,
            sortable=True,filterable=False)
            
    def processdata(self, data):
        if data:
            self.RFunctionParam_data=data.getData()
            self.commitFunction()
        else:
            self.RFunctionParam_data=''
            
    def processscores(self, data):
        if data:
            self.RFunctionParam_score = data.getData()
            self.commitFunction()
        else:
            self.RFunctionParam_score = ''
    def commitFunction(self):
        if unicode(self.RFunctionParam_data) == '': return
        if unicode(self.RFunctionParam_score) == '': return
        self.RoutputWindow.clear()
        
        ## first merge the data so that the scores and the data are in the same register, this will usually happen on naturally but we can't be sure of that.
        
        self.R('%s<-merge(%s, %s, by.x=0, by.y=0)' % (self.Rvariables['tempmerge'], self.RFunctionParam_score, self.RFunctionParam_data), wantType = 'NoConversion')
        self.R('%s<-%s[,c(\"%s\")]' % (self.Rvariables['mergedvals'], self.Rvariables['tempmerge'], '\",\"'.join(self.R('colnames(%s)' % self.RFunctionParam_data, wantType = 'NoConversion'))), wantType = 'NoConversion')
        self.R('%s<-%s[,c(\"%s\")]' % (self.Rvariables['mergedmatrix'], self.Rvariables['tempmerge'], '\",\"'.join(self.R('colnames(%s)' % self.RFunctionParam_score, wantType = 'NoConversion'))), wantType = 'NoConversion')
        
        ## now make the matrixes
        if unicode(self.scoremethod.currentText()) == _('Multiplication'):
            ## for each col in the samples we need to multiply the cols in the score matrix and save the result.
            self.R('%s<-as.data.frame(t(data.matrix(%s)) %%*%% data.matrix(%s))' % (self.Rvariables['score'], self.Rvariables['mergedmatrix'], self.Rvariables['mergedvals']), wantType = 'NoConversion')
            
        elif unicode(self.scoremethod.currentText()) == _('Correlation'):
            # perform cor and show the results
            self.R('%s<-as.data.frame(cor(data.matrix(%s), data.matrix(%s)))' % (self.Rvariables['score'], self.Rvariables['mergedmatrix'], self.Rvariables['mergedvals']), wantType = 'NoConversion')
        
        newScores = signals.base.RDataFrame(self, data = self.Rvariables['score'])
        self.RoutputWindow.setTable(newScores)
        self.rSend('fscoremat', newScores)
        