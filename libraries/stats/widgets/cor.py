"""Correlation/Variance widget


.. helpdoc::
Performs correlation, variance, or covariance testing on two data tables.
"""


"""<widgetXML>
    <name>
        Correlation/Variance
    </name>
    <icon>
        correlation.png
    </icon>
    <summary>
        Performs correlation, variance, or covariance testing on two data tables.
    </summary>
    <tags>
        <tag priority="1">
            Stats
        </tag>
    </tags>
    <author>
        <authorname>Red-R Core Development Team</authorname>
        <authorcontact>www.red-r.org</authorcontact>
    </author>
    </widgetXML>
"""

"""
<name>Correlation/Variance</name>
<tags>Stats</tags>
<icon>correlation.png</icon>
"""
#OWRpy is the parent of all widgets. 
#Contains all the functionality for connecting the widget to the underlying R session.
from OWRpy import *
import redRGUI, signals


# signalClasses classes contain the data that is passed between widgets. 
# In this case we are using the RDataFrame and RMatrix signals


# our first widget. Must be a child of OWRpy class
# The wiget class name must be the same as the file name

## these are the imports of the qt widgets that are Red-R compliant.  Feel free to make your own widgets and use them.  You can even use Qt widgets directly, though this is not recomended as they may not work with loading and saving.

class cor(OWRpy):
    
    # a list of all the variables that need to be saved in the widget state file.
    # these varibles values will be shared between widgets
    globalSettingsList = ['commit']

    # Python init statement is the class constructor 
    # Here you put all the code that will run as soon as the widget is put on the canvas
    def __init__(self, **kwargs):
        #Here we init the parent class of our widget OWRpy.
        OWRpy.__init__(self, **kwargs)
        
        #create a R variable cor in the R session.  These variables will be in the R session to track the ouputs of functions that run in R.
        #the cor variable will not conflict with some other widgets cor function
        self.setRvariableNames(["cor"])
        
        # declare some variables we will use later
        self.RFunctionParam_y = None
        self.RFunctionParam_x = None
        
        # Define the inputs that this widget will accept
        # When data is received the three element in the tuple which is a function will be executed
        
        """.. rrsignals::
            :description: `Input data table for comparison.`"""
        self.inputs.addInput('id0', 'x', [signals.base.RMatrix, signals.base.RDataFrame], self.processx)
        
        """.. rrsignals::
            :description: `Input data table for comparison.`"""
        self.inputs.addInput('id1', 'y', [signals.base.RMatrix, signals.base.RDataFrame], self.processy)

        # Define the outputs of this widget
        self.outputs.addOutput('id0', 'cor Output', signals.base.RMatrix)

        
        #START THE GUI LAYOUT
        area = redRGUI.base.widgetBox(self.controlArea,orientation='horizontal')       
        
        options = redRGUI.base.widgetBox(area,orientation='vertical')
        area.layout().setAlignment(options,Qt.AlignTop)
        
        """.. rrgui::
            :description: `Select the type of comparison to be made.`
        """
        # radioButtons are a type of qtWidget from the base package.  This widget will show radioButtons in a group.  Only one radio button may be selected at one time.  Buttons are declared using buttons = , the callback is the function that will be executed when the button selection changes.  setChecked sets a button to be checked by default.
        self.type = redRGUI.base.radioButtons(options,  label = "Perform", 
        buttons = ['Variance', 'Correlation', 'Covariance'],setChecked='Correlation',
        orientation='vertical',callback=self.changeType)
        
        
        """.. rrgui::
            :description: `Select statistic to ouptut.`
        """
        self.methodButtons = redRGUI.base.radioButtons(options,  label = "Method", 
        buttons = ['pearson', 'kendall', 'spearman'],setChecked='pearson',
        orientation='vertical')

        
        """.. rrgui::
            :description: `Set how missing values are to be handled.`
        """
        self.useButtons =  redRGUI.base.radioButtons(options, label='Handing Missing Values', setChecked='everything',
        buttons = ["everything","all.obs", "complete.obs", "pairwise.complete.obs"],
        orientation='vertical')
        
        
        """.. rrgui::
            :description: `Run the comparison.`
        """
        # the commit button is a special button that can be set to process on data input.  Widgets must be aware of these selections.  Clicking the commit button executes the callback which in this case executes the commitFunction.
        self.commit = redRGUI.base.commitButton(self.bottomAreaRight, "Commit", callback = self.commitFunction,
        processOnInput=True)
        
        """.. rrgui::
            :description: `Display results from the comparison in a table.`
        """
        # this is a filter table designed to hold R data.  The name is Cor/Var for the report generation but the user will not see this label because displayLabel is set to False.
        self.RoutputWindow = redRGUI.base.filterTable(area,label='Cor/Var', displayLabel=False,
        sortable=True,filterable=False)
    
    # execute this function when data in the X channel is received
    # The function will be passed the data
    def processx(self, signal):
        if signal:
            #if the signal exists get the data from it
            if isinstance(signal, signals.base.RDataFrame):
                self.RFunctionParam_x = 'data.matrix(%s)' % signal.getData()
            else:
                self.RFunctionParam_x=signal.getData()
            #self.RFunctionParam_x=signal.getData()
            # if the checkbox is checked, immediately process the data
            if self.commit.processOnInput():
                self.commitFunction()
                
    # execute this function when data in the Y channel is received
    # does the same things as processX
    def processy(self, signal):
        if signal:
            if isinstance(signal, signals.base.RDataFrame):
                self.RFunctionParam_y = 'data.matrix(%s)' % signal.getData()
            else:
                self.RFunctionParam_y=signal.getData()
            if self.commit.processOnInput():
                self.commitFunction()
            
    # this function actually does the work in R 
    # its call by clicking the Commit button
    # or when data is received, if the checkbox is checked.
    def commitFunction(self):
        # The X data is required, if not received, do nothing
        if not self.RFunctionParam_x: 
            self.status.setText('X data is missing')
            return

        
        # START COLLECTION THE R PARAMETERS THAT WILL CREATE THE R CODE TO EXECUTE
        injection = []
        
        if self.type.getChecked() == 'Correlation':
            test = 'cor'
        elif self.type.getChecked() == 'Variance':
            test = 'var'
        elif self.type.getChecked() == 'Covariance':
            test = 'cov'
            
        if self.useButtons.getChecked():
            string = 'use=\''+unicode(self.useButtons.getChecked())+'\''
            injection.append(string)
        elif self.type.getChecked() == 'Variance':
            string = 'na.rm=TRUE'
            injection.append(string)
        
        if self.methodButtons.getChecked() and test != 'var':
            string = 'method=\''+unicode(self.methodButtons.getChecked())+'\''
            injection.append(string)
            
        if self.RFunctionParam_y:
            injection.append('y=data.matrix(%s)' % unicode(self.RFunctionParam_y))

        # combine all the parameters in the a string    
        inj = ','.join(injection)
        
        # make the R call. The results will be saved in the 'cor' variable we declared earlier
        self.R('%s<-%s(x=data.matrix(%s),%s)' % (self.Rvariables['cor'], test, unicode(self.RFunctionParam_x), inj), wantType = 'NoConversion')
        
        # visualize the data in a table
        tableData = signals.base.RDataFrame(self, data = 'as.data.frame(%s)' % self.Rvariables["cor"])
        self.RoutputWindow.clear()
        
        self.RoutputWindow.setTable(tableData)
        
        # create a new signal of type RMatrix and load the results 
        newData = signals.base.RMatrix(self, data = self.Rvariables["cor"]) 
        # send the signal forward
        self.rSend("id0", newData)
  
    
    # Based on the user selections some parameters is not valid. This is all documented in the R help for cor/var/cov
    # Here we are instructing the GUI to disable those parameters that are invalid. 
    def changeType(self):
        if self.type.getChecked() =='Variance':
            self.useButtons.setDisabled(True)
            self.methodButtons.setDisabled(True)
        else:    
            self.useButtons.setEnabled(True)
            self.methodButtons.setEnabled(True)

        if self.type.getChecked() =='Covariance':
            self.useButtons.disable(['pairwise.complete.obs'])
        elif self.type.getChecked() =='Correlation':
            self.useButtons.enable(['pairwise.complete.obs'])
    
    # getReportText returns a string of text in restructuredtext format that will be used to generate the report of the data.
    # We should send back a general representation of what happened in the widget to the user.
 
        
        
        
