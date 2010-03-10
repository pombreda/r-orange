"""
<name>Limma Decide</name>
<description>Calculates differential expression of genes from an eSet object</description>
<tags>Microarray</tags>
<RFunctions>limma:decideTests</RFunctions>
<icon>icons/readcel.png</icon>
<priority>2030</priority>
"""

import redRGUI
from OWRpy import *


class limmaDecide(OWRpy):
    settingsList = ['modelProcessed', 'olddata', 'newdata', 'dmethod', 'adjmethods', 'foldchange', 'pval', 'data', 'sending', 'ebdata', 'eset']
    def __init__(self, parent=None, signalManager=None):
        OWRpy.__init__(self, parent, signalManager, "File", wantMainArea = 0, resizingEnabled = 1)

        self.data = ''
        self.ebdata = ''
        self.olddata = None
        self.newdata = None
        
        self.eset = None
        self.sending = None
        self.modelProcessed = 0
        self.loadSettings()
        
        self.setRvariableNames(['gcm', 'eset_sub', 'geneissig', 'dfsg'])
        
        #self.sendMe()
        
        self.inputs = [("eBayes fit", RvarClasses.RVariable, self.process), ('NormalizedAffybatch', RvarClasses.RDataFrame, self.processeset)]
        self.outputs = [("Gene Change Table", RvarClasses.RDataFrame), ("Expression Subset", RvarClasses.RDataFrame)]
        
        #GUI
        #want to have an options part, a data viewing part and a run part
        
        layk = QWidget(self)
        self.controlArea.layout().addWidget(layk)
        grid = QGridLayout()
        grid.setMargin(0)
        layk.setLayout(grid)
        
        optionsbox = redRGUI.widgetBox(self.controlArea, "Options")
        grid.addWidget(optionsbox, 0,0)
        self.dmethod = redRGUI.comboBox(optionsbox, label = "Combine Method"+"  ", items = ["separate", "global", "hierarchical", "nestedF"], orientation=0)
        self.adjmethods = redRGUI.comboBox(optionsbox, label = "P-value Adjust Methods", items = ["BH", "none", "fdr", "BY", "holm"], orientation=0)
        self.pval = redRGUI.lineEdit(optionsbox, label = "Minimum p-value change:", orientation = 0)
        self.foldchange = redRGUI.lineEdit(optionsbox, label = "Minimum fold change:", orientation = 0)
        
        computebox = redRGUI.widgetBox(self.controlArea, "Compute")
        grid.addWidget(computebox, 1,0)
        self.infoa = redRGUI.widgetLabel(computebox, "Data not yet connected")
        runbutton = redRGUI.button(computebox, "Run Analysis", callback = self.runAnalysis, width=200)
        


    def process(self, dataset):
        self.require_librarys(['affy', 'limma'])
        self.data = '' # protect from using obsolete data
        
        for output in self.outputs:
            self.rSend(output[0], None, 0) #start the killing cascade for all outputs
        if dataset == None:
            self.infoa.setText("Blank data recieved")
            return
        if 'data' in dataset:
            self.data = dataset['data']
            self.ebdata = dataset
            self.infoa.setText("Data connected")
        else:   
            self.infoa.setText("No data element in recieved data")
        
    def runAnalysis(self):
        #self.Rvariables['gcm'] = 'gcm'+self.variable_suffix

        #run the analysis using the parameters selected or input
        self.R(self.Rvariables['gcm']+'<-decideTests('+self.data+', method="'+str(self.dmethod.text())+'", adjust.method="'+str(self.adjmethods.text())+'", p.value='+str(self.pval.text())+', lfc='+str(self.foldchange.text())+')')
        self.infoa.setText("Gene Matrix Processed and sent!")
        self.sending = {'data':self.Rvariables['gcm']}
        self.rSend("Gene Change Matrix", self.sending)
        
        self.R(self.Rvariables['gcm']+'[,2]!=0 ->'+self.Rvariables['geneissig'])
        self.R(self.Rvariables['gcm']+'['+self.Rvariables['geneissig']+',] ->'+self.Rvariables['dfsg'])
        self.modelProcessed = 1
        
        self.sendesetsubset()
        
    def onLoadSavedSession(self):
        if self.R('exists("'+self.Rvariables['gcm']+'")'):
            self.infoa.setText("Gene Matrix Processed and sent!")
            self.sending = {'data':self.Rvariables['gcm']}
            self.modelProcessed = 1
            self.sendesetsubset()
        else:
            self.send("Gene Change Matrix",None)
        if self.R('exists("'+self.Rvariables['eset_sub']+'")'):
            self.rSend("Expression Subset", self.newdata)
        else:
            self.rSend("Expression Subset", None)

            
            
    def processeset(self, data):
        self.eset = None
        if data == None:
            self.rSend("Expression Subset", None, 0)
        if data:
            self.eset = data['data'] #this is data from an expression matrix or data.frame
            self.olddata = data.copy()
            if self.sending != None and self.ebdata != '':
                self.sendesetsubset()
        else: return

    def sendesetsubset(self):
        if self.eset != None and self.modelProcessed == 1:
            self.rsession(self.Rvariables['eset_sub']+'<-'+self.eset+'[rownames('+self.Rvariables['dfsg']+'),]')
            self.newdata = self.olddata.copy()
            self.newdata['data']=self.Rvariables['eset_sub']
            if 'classes' in self.ebdata:
                self.newdata['classes'] = self.ebdata['classes']
            self.rSend("Expression Subset", self.newdata)
        else:
            return 