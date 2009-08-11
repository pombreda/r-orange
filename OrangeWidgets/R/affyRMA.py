"""
<name>Normalize</name>
<description>Processes an Affybatch to an eset using RMA</description>
<icon>icons/rma.png</icons>
<priority>1010</priority>
"""

from rpy_options import set_options
set_options(RHOME='c:/progra~1/r/R-2.6.2/')
from rpy import *
from OWWidget import *
import OWGUI
r.require('affy')

class affyRMA(OWWidget):
	def __init__(self, parent=None, signalManager=None):
		OWWidget.__init__(self, parent, signalManager, "Sample Data")
		
		self.inputs = [("Affybatch Expression Matrix", orange.Variable, self.process)]
		self.outputs = [("Normalized eSet", orange.Variable)]
		
		self.data = None
		self.normmeth = 'quantiles'
		self.normoptions = ""
		self.rand = str(random.random())
		self.bgcorrect = 'FALSE'
		self.bgcorrectmeth = 'none'
		self.pmcorrect = 'pmonly'
		self.summarymeth = 'liwong'
		self.norm = ['quantiles']
		self.selectMethod = 3
		
		#the GUI
		normrad = OWGUI.widgetBox(self.controlArea, "Normalization Methods")
		selMethBox = OWGUI.radioButtonsInBox(self.controlArea, self, "selectMethod", ["RMA", "MAS5", "Custom"], box="Select attributes", callback=self.selectMethodChanged)
		
		info = OWGUI.widgetBox(self.controlArea, "Normalization Options")
		self.infoa = OWGUI.widgetLabel(info, 'No data loaded.')
		#drop list box
		
		#insert a block to check what type of object is connected.  If nothing connected set the items of the normalize methods objects to 
		self.normselector = OWGUI.comboBox(info, self, "normmeth", label="Normalization Method  ", items=self.norm, orientation=0)
		self.normselector.setEnabled(False)
		self.bgcorrectselector = OWGUI.comboBox(info, self, 'bgcorrect', label="Background Correct Methods", items=['TRUE', 'FALSE'], orientation=0)
		self.bgcorrectselector.setEnabled(False)
		self.bgcmethselector = OWGUI.comboBox(info, self, 'bgcorrectmeth', label="Background Correct Methods", items=r('bgcorrect.methods'), orientation=0)
		self.bgcmethselector.setEnabled(False)
		self.pmcorrectselector = OWGUI.comboBox(info, self, 'pmcorrect', label="Perfect Match Correct Methods", items=r('pmcorrect.methods'), orientation=0)
		self.pmcorrectselector.setEnabled(False)
		self.summethselector = OWGUI.comboBox(info, self, 'summarymeth', label="Summary Methods", items=r('express.summary.stat.methods'), orientation=0)
		self.summethselector.setEnabled(False)
		
		
		run = OWGUI.widgetBox(self.controlArea, "Run the Normalization")
		self.infob = OWGUI.widgetLabel(run, 'Procedure not run yet')
		runbutton = OWGUI.button(run, self, "Run Normalization", callback = self.normalize, width=200)
		OWGUI.button(run, self, 'test', callback = self.checkRCode, width=200)
		
	def normalize(self):
		if self.selectMethod == 1:
			self.runRMA()
		if self.selectMethod == 2:
			self.runMAS5()
		if self.selectMethod == 3:
			self.runCustom()
	
	def runRMA(self):
		r('normalized_affybatch'+self.rand+'<-rma('+self.data+')') #makes the rma normalization
		neset = {'data':['exprs(normalized_affybatch'+self.rand+')'], 'eset':['normalized_affybatch'+self.rand], 'normmethod':['rma']}
		
		self.send("Normalized eSet", neset)
	
	def runMAS5(self):
		r('normalized_affybatch'+self.rand+'<-mas5('+self.data+')') #makes the rma normalization
		neset = {'data':['exprs(normalized_affybatch'+self.rand+')'], 'eset':['normalized_affybatch'+self.rand], 'normmethod':['mas5']}
		
		self.send("Normalized eSet", neset)
	
	def checkRCode(self):
		self.infob.setText('normalized_affybatch'+self.rand+'<-expresso('+self.data+', bg.correct='+self.bgcorrect+', bgcorrect.method='+self.bgcorrectmeth+', pmcorrect.method='+self.pmcorrect+', summary.method='+self.summarymeth+')')
		
	def collectOptions(self):
		if self.normmeth == None: self.normoptions = ""
		elif self.normmeth == "":
			self.normmeth = None
			self.collectOptions()
		else:
			self.normoptions = ',method='+self.normmeth
	
	def process(self, dataset):
		if dataset['eset']:
			self.data = str(dataset['eset'][0])
			if r('length(exprs('+self.data+')[1,])') > 10:
				self.setLiWong()
			else:
				self.setRMA()
		else: return
	
	def setLiWong(self):
		self.bgcorrectselector.setCurrentIndex(self.bgcorrectselector.findText('FALSE'))
		self.bgcorrectselector.setEnabled(True)
		self.bgcorrectmeth = 'none'
		self.bgcmethselector.setCurrentIndex(self.bgcmethselector.findText('none'))
		self.bgcmethselector.setEnabled(True)
		self.pmcorrect = 'pmonly'
		self.pmcorrectselector.setCurrentIndex(self.pmcorrectselector.findText('pmonly'))
		self.pmcorrectselector.setEnabled(True)
		self.summarymeth = 'liwong'
		self.summethselector.setCurrentIndex(self.summethselector.findText('liwong'))
		self.summethselector.setEnabled(True)
		self.norm = ['quantiles']
		self.normselector.clear()
		self.normselector.addItems(r('normalize.methods('+self.data+')'))
		self.normselector.setCurrentIndex(self.normselector.findText('invariantset'))
		self.normselector.setEnabled(True)
		self.infoa.setText('Data has been connected')
		
	
	def runCustom(self):
		self.collectOptions()
		if self.data:
			r('normalized_affybatch'+self.rand+'<-expresso('+self.data+', bg.correct='+self.bgcorrect+', bgcorrect.method="'+self.bgcorrectmeth+'", pmcorrect.method="'+self.pmcorrect+'", summary.method="'+self.summarymeth+'")')
			normset = 'normalized_affybatch'+self.rand
			self.infob.setText('Normalization compleated.')
			self.send("Normalized eSet", normset)
		else: return
	
	def setRMA(self):
		self.bgcorrectselector.setEnabled(False)
		self.bgcmethselector.setEnabled(False)
		self.pmcorrectselector.setEnabled(False)
		self.summethselector.setEnabled(False)
		self.normselector.setEnabled(False)
	
	def setMAS5(self):
		self.bgcorrectselector.setEnabled(False)
		self.bgcmethselector.setEnabled(False)
		self.pmcorrectselector.setEnabled(False)
		self.summethselector.setEnabled(False)
		self.normselector.setEnabled(False)
		
	def selectMethodChanged(self):
		if self.selectMethod == 1:
			self.setRMA()
		if self.selectMethod == 2:
			self.setMAS5()
		if self.selectMethod == 3:
			self.setLiWong()
		
	