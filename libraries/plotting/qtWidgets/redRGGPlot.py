## redRGUI Graphics View.  A graphics view used for graphing R graphs, this should be as general as possible with an eye to some degree of automation in assignment of items.  

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSvg import *
from redRGUI import widgetState
from libraries.base.qtWidgets.widgetBox import widgetBox
from libraries.base.qtWidgets.groupBox import groupBox
from libraries.base.qtWidgets.comboBox import comboBox
from libraries.base.qtWidgets.lineEdit import lineEdit 
from libraries.base.qtWidgets.widgetLabel import widgetLabel 
from libraries.base.qtWidgets.button import button
from libraries.base.qtWidgets.tabWidget import tabWidget
from libraries.base.qtWidgets.listBox import listBox
from libraries.base.qtWidgets.spinBox import spinBox
from libraries.base.qtWidgets.textEdit import textEdit
from libraries.base.qtWidgets.checkBox import checkBox
from libraries.base.qtWidgets.dialog import dialog
from libraries.base.qtWidgets.colorButton import colorButton
import RSession, redREnviron, datetime, os, time
    

class redRGGPlot(QGraphicsView, widgetState):
    def __init__(self, parent,label=None, displayLabel=True,includeInReports=True, name = '', data = None):
        ## want to init a graphics view with a new graphics scene, the scene will be accessable through the widget.
        widgetState.__init__(self,parent,label,includeInReports)
        
        QGraphicsView.__init__(self, self.controlArea)
        self.topArea = widgetBox(self.controlArea,
        sizePolicy = QSizePolicy(QSizePolicy.Maximum,QSizePolicy.Maximum),includeInReports=False, orientation = 'horizontal')
        self.middleArea = widgetBox(self.controlArea)
        self.bottomArea = widgetBox(self.controlArea,includeInReports=False)  #, sizePolicy = QSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        
        self.middleArea.layout().addWidget(self)  # place the widget into the parent widget
        scene = QGraphicsScene()
        self.setScene(scene)
        self.parent = parent
        self.data = data
        self.printQuery = ''
        self.widgetSelectionRect = None
        self.mainItem = None
        self.query = ''
        self.function = 'plot'
        self.layers = []
        self.image = 'plot'+unicode(time.time()) # the base file name without an extension
        self.imageFileName = ''
        self.currentScale = 1

    ################################
    ####   Themes              #####
    ################################
        
        
        self.options = {
            'device': {
                'Rcall': 'Cairo',
                'parameters': {
                    'type':{
                            'default':'svg',
                            'qtWidget': 'imageType'
                        }
                    ,'dpi':{
                            'default':'75',
                            'qtWidget': 'dpi'
                        }
                    ,'bg': {
                            'default':'#FFFFFF', 
                            'color': '#FFFFFF',
                            'qtWidget':'bgColor'
                            
                            }
                    ,'height': {
                            'default':400, 
                            'qtWidget': 'dheight'
                            }
                    ,'width': {
                            'default':400, 
                            'qtWidget': 'dwidth'
                            }
                    ,'units': {
                            'default':'px', 
                            'qtWidget': 'units'
                            }
                    }
                }
            ,'main': {
                'Rcall': 'plot',
                'parameters': {
                    'col': {
                        'default':None, 
                        'qtWidget':'colorSeries',
                        'series': '',
                        'seriesLen': 0,
                        'getFunction': self.getColorSeries,
                        'setFunction': self.setColorSeries,
                        }
                    ,'lty': {
                        'default':None, 
                        'qtWidget':'linesListBox',
                        'getFunction': self.getLineTypes,
                        'setFunction': self.setLineTypes,
                        }
                    ,'lwd': {
                        'default':None, 
                        'qtWidget':'lineWidth'
                        }
                    ,'pch': {
                        'default':None, 
                        'qtWidget':'pointListBox',
                        'getFunction': self.getLineTypes,
                        'setFunction': self.setLineTypes,
                        }
                }
            },
            'title': {
                'Rcall': 'title',
                'parameters': {
                    'main': {
                          'default':"Title", 
                          'qtWidget':'mainTitle' 
                          }
                    ,'xlab': {
                        'default':"XLab", 
                        'qtWidget':'xLab'
                        }
                    ,'ylab': {
                        'default':"YLab", 
                        'qtWidget':'yLab'
                        }   
                    ,'col.main': {
                          'default':'#000000', 
                          'qtWidget':'titleColor' 
                          }
                    ,'col.sub': {
                          'default':'#000000', 
                          'qtWidget':'subColor' 
                          }
                    ,'col.lab': {
                          'default':'#000000', 
                          'qtWidget':'labColor' 
                          }                        
                }
            },
            'par': {
                'Rcall':'par',
                'parameters': {
                    'cex.axis': {
                          'default':1, 
                          'qtWidget':'axisFont' 
                          }
                    ,'cex.lab': {
                          'default':1, 
                          'qtWidget':'labFont' 
                          }
                    ,'cex': {
                          'default':1, 
                          'qtWidget':'plotFont' 
                          }
                    ,'cex.main': {
                          'default':1, 
                          'qtWidget':'mainFont' 
                          }
                    ,'cex.sub': {
                          'default':1, 
                          'qtWidget':'subFont' 
                          }
                    ,'col.axis': {
                          'default':'#000000', 
                          'qtWidget':'axisColor' 
                          }
                    # ,'family': {
                          # 'default':'serif', 
                          # 'qtWidget':'fontCombo' 
                          # }
                }
            }
        }
        
        
        ### ggplot options
        self.optionsDialog = dialog(self.controlArea)
        self.optionsTab = tabWidget(self.optionsDialog)
        
        plotGridTab = self.optionsTab.createTabPage("Plot Grid Area", orientation = 'vertical')
        
        self.panelGridMajorTheme = comboBox(plotGridTab, label = 'Major Grid General Theme', toolTip = 'If Ignore, no options are set for this.  If not None overrides all other options set and sets the theme specified.', items = [('ignore', 'Ignore'), ('none', 'None'), ('theme_bw()', 'Black and White'), ('theme_blank()', 'Blank Theme')])
        self.panelGridMajorColour = colorButton(plotGridTab, label = "Major Grid Color")
        self.panelGridMajorSize = spinBox(plotGridTab, label = "Major Grid Size")
        self.panelGridMajorLineType = comboBox(plotGridTab, label = "Major Grid Line Type", items = [('solid', 'Solid'), ('dotted', 'Dotted'), ('dashed', 'Dashed')])
        
        self.panelGridMinorTheme = comboBox(plotGridTab, label = 'Minor Grid General Theme', toolTip = 'If Ignore, no options are set for this.  If not None overrides all other options set and sets the theme specified.', items = [('ignore', 'Ignore'), ('none', 'None'), ('theme_bw()', 'Black and White'), ('theme_blank()', 'Blank Theme')])
        self.panelGridMinorColour = colorButton(plotGridTab, label = "Minor Grid Color")
        self.panelGridMinorSize = spinBox(plotGridTab, label = "Minor Grid Size")
        self.panelGridMinorLineType = comboBox(plotGridTab, label = "Minor Grid Line Type", items = [('solid', 'Solid'), ('dotted', 'Dotted'), ('dashed', 'Dashed')])
        
        panelTab = self.optionsTab.createTabPage("panel Background Options", orientation = 'vertical')
        
        self.panelBackgroundTheme = comboBox(panelTab, label = 'panel Background Theme', toolTip = 'If Ignore, no options are set for this.  If not None overrides all other options set and sets the theme specified.', items = [('ignore', 'Ignore'), ('none', 'None'), ('theme_bw()', 'Black and White'), ('theme_blank()', 'Blank Theme')])
        
        textTab = self.optionsTab.createTabPage("Text Options", orientation = 'vertical')
        
        self.useTextOptions = comboBox(textTab, label = 'Use Text Options', items = [('ignore', 'No'), ('yes', 'Yes')])
        self.plotTitle = lineEdit(textTab, label = 'Plot Title')
        self.plotTitleSize = spinBox(textTab, label = 'Title Font Size', min = 1, value = 20)
        self.plotTitleAngle = spinBox(textTab, label = 'Title Angle', min = 0, max = 360, value = 0)
        self.plotTitleFontFace = comboBox(textTab, label = 'Font Face', items = [('none', 'None'), ('bold', 'Bold')])
        
        self.axisTitleX = lineEdit(textTab, label = 'X Axis Title')
        self.axisTitleXColor = colorButton(textTab, label = 'X Axis Color')
        self.axisTitleXSize = spinBox(textTab, label = 'X Axis Title Size', min = 1, value = 14)
        self.axisTitleXAngle = spinBox(textTab, label = 'X Axis Title Angle', min = 0, max = 360, value = 0)
        self.axisTitleXFontFace = comboBox(textTab, label = 'X Axis Title Font Face', items = [('none', 'None'), ('bold', 'Bold')])
        
        self.axisTextXSize = spinBox(textTab, label = 'X Axis Text Size', min = 1, value = 14)
        self.axisTextXColor = colorButton(textTab, label = 'X Axis Text Color')
        self.axisTextXAngle = spinBox(textTab, label = 'X Axis Text Angle', min = 0, max = 360, value = 0)
        self.axisTextXFontFace = comboBox(textTab, label = 'X Axis Text Font Face', items = [('none', 'None'), ('bold', 'Bold')])
        
        self.axisTitleY = lineEdit(textTab, label = 'Y Axis Title')
        self.axisTitleYColor = colorButton(textTab, label = 'Y Axis Color')
        self.axisTitleYSize = spinBox(textTab, label = 'Y Axis Title Size', min = 1, value = 14)
        self.axisTitleYAngle = spinBox(textTab, label = 'Y Axis Title Angle', min = 0, max = 360, value = 0)
        self.axisTitleYFontFace = comboBox(textTab, label = 'Y Axis Title Font Face', items = [('none', 'None'), ('bold', 'Bold')])
        
        self.axisTextYSize = spinBox(textTab, label = 'Y Axis Text Size', min = 1, value = 14)
        self.axisTextYColor = colorButton(textTab, label = 'Y Axis Text Color')
        self.axisTextYAngle = spinBox(textTab, label = 'Y Axis Text Angle', min = 0, max = 360, value = 0)
        self.axisTextYFontFace = comboBox(textTab, label = 'Y Axis Text Font Face', items = [('none', 'None'), ('bold', 'Bold')])
        
        self.optionsDialog.hide()
        
        self.optionWidgets = {}
        self.colorList = ['#000000', '#ff0000', '#00ff00', '#0000ff']       

        self.extraOptionsLineEdit = lineEdit(self.topArea, label = 'Extra Options', toolTip = 'These options will be appended to the plotting call, remember that these are ggplot options that will be added to the plot object')
        self.extraOptionsLineEdit.controlArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        
        self.heightSpinBox = spinBox(self.topArea, label = 'Height', min = 0, value = 7, decimals = 3)
        self.widthSpinBox = spinBox(self.topArea, label = 'Width', min = 0, value = 7, decimals = 3)
        button(self.topArea, label = 'Show Options', callback = self.optionsDialog.show)
        
    
    ################################
    ### right click menu     #######
    ################################
        self.menu = QMenu(self)
        save = self.menu.addMenu('Save As')
        save.addAction('Bitmap')
        save.addAction('PDF')
        save.addAction('Post Script')
        save.addAction('JPEG')
        save.addAction('SVG')
        self.menu.addAction('Copy')
        self.menu.addAction('Fit In Window')
        self.menu.addAction('Zoom Out')
        self.menu.addAction('Zoom In')
        self.menu.addAction('R Graphics Device')
        #self.menu.addAction('Undock')
        #self.menu.addAction('Redock')
        
        self.dialog = QDialog()
        self.dialog.setWindowTitle('Red-R Graphics View' + name)
        self.dialog.setLayout(QHBoxLayout())
        
        self.standardImageType = 'svg'
        self.imageType = 'svg'
        QObject.connect(self.dialog, SIGNAL('finished(int)'), self.dialogClosed)




    ################################
    #### Plot Option Widgets   #####
    ################################
    
    def displayGraphicOptions(self):
        if self.graphicOptionsButton.isChecked():
            self.graphicOptionsWidget.show()
        else:
            self.graphicOptionsWidget.hide()
    
    def setTheme(self,options):
        for Rcall,parameters in self.options.items():
            for k,v in parameters['parameters'].items():
                #call function to collect data  
                if 'setFunction' in v.keys():
                    v['setFunction'](self.options[Rcall]['parameters'][k])
                else:
                    self.setOptions(self.options[Rcall]['parameters'][k])
        
        
    ################################
    ####  Tab Actions         #####
    ################################
    
    def setPlotColors(self):
        colorDialog = colorListDialog(data = self.data)
        colorDialog.setColors(self.colorList)
        colorDialog.exec_()
        self.options['col']['value'] = 'c('+','.join([unicode(a) for a in colorDialog.listOfColors])+')'
        self.colorList = colorDialog.listOfColors
        if self.options['col']['value'] == 'c()':
           self.options['col']['value'] = 'c("#FFFFFF")'
        colorDialog.hide()

    def setColorSeries(self,options):
        self.optionWidgets['colorSeries'].setCurrentId(options['series'])
        self.optionWidgets['colorSeriesLen'].setValue(options['seriesLen'])
        
    def getColorSeries(self,options):
        #print options
        if self.optionWidgets['colorSeries'].currentId() == 'select':
            options['value'] = None
        else:
            series = self.optionWidgets['colorSeries'].currentId()
            options['value'] = '%s(%d)' % (series,self.optionWidgets['colorSeriesLen'].value())
    
    def setOptions(self,options):
        if 'default' not in options.keys() or options['default'] == None: return
        
        qtWidget = self.optionWidgets[options['qtWidget']]
        if isinstance(qtWidget,ColorIcon):
            qtWidget.color = options['default']
            qtWidget.updateColor()
        elif isinstance(qtWidget,lineEdit):
            qtWidget.setText(options['default'])
        elif isinstance(qtWidget,comboBox):
            qtWidget.setCurrentId(options['default'])
        elif isinstance(qtWidget,spinBox):
            qtWidget.setValue(options['default'])
            
    def updateOptions(self,options):
        return
        qtWidget = self.optionWidgets[options['qtWidget']]
        
        if isinstance(qtWidget,ColorIcon):
            options['value'] = "'%s'" % self.optionWidgets[options['qtWidget']].color
        if isinstance(qtWidget,lineEdit):
            #if qtWidget.text() =='': return
            try:
                options['value'] = "%f" % float(qtWidget.text())
            except:
                options['value'] = "'%s'" % qtWidget.text()
        elif isinstance(qtWidget,comboBox):
            if qtWidget.currentId() =='': 
                options['value'] = None
                return 
            try:
                options['value'] = "%f" % float(qtWidget.currentId())
            except:
                options['value'] = "'%s'" % qtWidget.currentId()
                
        elif isinstance(qtWidget,spinBox):
            if qtWidget.value() =='':
                options['value'] = None
                return 

            options['value'] = qtWidget.value()
    
    def getLineTypes(self,options):
        qtWidget = self.optionWidgets[options['qtWidget']]
        print qtWidget.selectedIds()
        options['value'] = 'c('+','.join([unicode(x) for x in qtWidget.selectedIds()])+')'
        
    def setLineTypes(self,options):
        if 'default' not in options.keys() or options['default'] == None: return
        qtWidget = self.optionWidgets[options['qtWidget']]
        qtWidget.setSelectedIds(options['default'])
        
    ##############################
    ### Plotting #################\
    ##############################
    def _setLegend(self):
        ## we want to make a legend that will appear on the plot.  legend(x, y = NULL, legend, fill = NULL, col = par("col"),
                   # border="black", lty, lwd, pch,
                   # angle = 45, density = NULL, bty = "o", bg = par("bg"),
                   # box.lwd = par("lwd"), box.lty = par("lty"), box.col = par("fg"),
                   # pt.bg = NA, cex = 1, pt.cex = cex, pt.lwd = lwd,
                   # xjust = 0, yjust = 1, x.intersp = 1, y.intersp = 1,
                   # adj = c(0, 0.5), text.width = NULL, text.col = par("col"),
                   # merge = do.lines && has.pch, trace = FALSE,
                   # plot = TRUE, ncol = 1, horiz = FALSE, title = NULL,
                   # inset = 0, xpd, title.col = text.col)
        if not self._legendNames:
            self.parent.status.setText('No legend names specified. Can\'t make the legend')
        function = 'legend(x=\''+self._legendLocation+'\', legend = '+self._legendNames
        if self._col:
            function += ', col = '+self._col
        if self._lty:
            function += ', lty = '+self._lty
        if self._lwd:
            function += ', lwd = '+self._lwd
        if self._pch:
            function += ', pch = '+self._pch
        function += ')'
        self.R(function)
    def setLegendNames(self, parameter):
        ## sets the legend to plot the names as the set parameter.  This can come from either a call to the widget through it's own interface or through the widget.
        self._legendNames = parameter
    def _setLegendLocation(self, location):
        self._legendLocation = location
    def _getParameters(self):
        # import pprint
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(self.options)

        injection = {}
        for Rcall,parameters in self.options.items():
            injection[Rcall] = []
            for k,v in parameters['parameters'].items():
                #call function to collect data  
                if 'getFunction' in v.keys():
                    v['getFunction'](self.options[Rcall]['parameters'][k])
                else:
                    self.updateOptions(self.options[Rcall]['parameters'][k])
                print Rcall,k
                if v['value']:
                    injection[Rcall].append('%s = %s' % (k,v['value']))
            
        # pp.pprint(self.options)            
        return injection            
        
    def _startRDevice(self, imageType):
        if imageType not in ['svg', 'png', 'jpeg']:
            imageType = 'png'
        
        # fileName = redREnviron.directoryNames['tempDir']+'/plot'+unicode(self.widgetID).replace('.', '_')+'.'+imageType
        # fileName = fileName.replace('\\', '/')
        self.imageFileName = unicode(self.image).replace('\\', '/')+'.'+unicode(imageType)
        file = unicode(os.path.join(redREnviron.directoryNames['tempDir'], self.imageFileName).replace('\\', '/'))
        # print '###################### filename' , self.imageFileName
        if imageType == 'svg':
            self.require_librarys(['RSvgDevice'])
            self.R('devSVG(file="%s")' % ( file,))
            
        if imageType == 'png':
            self.R('png(file="%s")' % ( file,))

        elif imageType == 'jpeg':
            self.R('jpeg(file="%s")' % (file,))
        return file
    def plot(self, query, function = 'print', parameters=None,data=None):
        ## performs a quick plot given a query and an imageType
        self.data = data
        self.function = function
        self.query = query
        self.layers = []
           
        self.plotMultiple()
        
    def plotMultiple(self):
        
        self.require_librarys(['RSvgDevice'])
        self.imageFileName = unicode(self.image)+'.svg'
        
        file = self._startRDevice(self.imageType)
        
        fullquery = self.query
        try:
            options = []
            ## build the options from what we have set in the gui.
            if self.panelBackgroundTheme.currentId() != 'ignore':
                if self.panelBackgroundTheme.currentId() == 'none':
                    pass
                else:
                    options.append('opts(panel.background = %s)' % self.panelBackgroundTheme.currentId())
            if self.panelGridMajorTheme.currentId() != 'ignore':
                if self.panelGridMajorTheme.currentId() == 'none':
                    options.append('opts(panel.grid.major = theme_line(colour = "%(COLOUR)s", size = %(SIZE)s, linetype = "%(LINE)s))' % {'COLOUR':self.panelGridMajorColour.color, 'SIZE':str(self.panelGridMajorSize.value()), 'LINE':self.panelGridMajorLineType.currentId()})
                else:
                    options.append('opts(panel.grid.major = %s)' % self.panelGridMajorTheme.currentId())
            if self.panelGridMinorTheme.currentId() != 'ignore':
                if self.panelGridMinorTheme.currentId() == 'none':
                    options.append('opts(panel.grid.minor = theme_line(colour = "%(COLOUR)s", size = %(SIZE)s, linetype = "%(LINE)s))' % {'COLOUR':self.panelGridMinorColour.color, 'SIZE':str(self.panelGridMinorSize.value()), 'LINE':self.panelGridMinorLineType.currentId()})
                else:
                    options.append('opts(panel.grid.major = %s)' % self.panelGridMinorTheme.currentId())
            if self.useTextOptions.currentId() != 'ignore':
                options.append('opts(axis.title.x = theme_text(label = %(XLAB)s, colour = "%(XCOL)s, size = %(XSIZE)s, face = "%(XFACE)s", angle = %(XANGLE)s), axis.title.y = theme_text(label = %(YLAB)s, colour = "%(YCOL)s, size = %(YSIZE)s, face = "%(YFACE)s", angle = %(YANGLE)s), axis.text.x = theme_text(colour = "%(XTCOL)s, size = %(XTSIZE)s, face = "%(XTFACE)s", angle = %(XTANGLE)s), axis.text.y = theme_text(colour = "%(YTCOL)s, size = %(YTSIZE)s, face = "%(YTFACE)s", angle = %(YTANGLE)s))' % {'XLAB':self.axisTitleX.text(), 'XCOL':self.axisTitleXColor.color, 'XSIZE':str(self.axisTitleXSize.value()), 'XFACE':self.axisTitleXFontFace.currentId(), 'XANGLE':str(self.axisTitleXAngle.value()), 'YLAB':self.axisTitleY.text(), 'YCOL':self.axisTitleYColor.color, 'YSIZE':str(self.axisTitleYSize.value()), 'YFACE':self.axisTitleYFontFace.currentId(), 'YANGLE':str(self.axisTitleYAngle.value()), 'XTCOL':self.axisTextXColor.color, 'XTSIZE':str(self.axisTextXSize.value()), 'XTFACE':self.axisTextXFontFace.currentId(), 'XTANGLE':str(self.axisTextXAngle.value()), 'YTCOL':self.axisTextYColor.color, 'YTSIZE':str(self.axisTextYSize.value()), 'YTFACE':self.axisTextYFontFace.currentId(), 'YTANGLE':str(self.axisTextYAngle.value())})
            #self.R('print(%s + xlab("%s") + ylab("%s"))' % (fullquery, self.)  opts(grid.fill = 'white') + scale_x_discrete(limits = c('V', 'M2', 'M3'))
            if self.extraOptionsLineEdit.text() != '' and len(options) != 0:
                self.printQuery = 'print(%s + %s + %s)' % (fullquery, self.extraOptionsLineEdit.text(), ' + '.join(options))
                self.R(self.printQuery)
            elif self.extraOptionsLineEdit.text() != '':
                self.printQuery = 'print(%s + %s)' % (fullquery, self.extraOptionsLineEdit.text())
                self.R(self.printQuery)
            elif len(options) != 0:
                self.printQuery = 'print(%s + %s)' % (fullquery, ' + '.join(options))
                self.R(self.printQuery)
            else:
                self.printQuery = 'print(%s)' % fullquery
                self.R(self.printQuery)
        except Exception as inst:
            self.R('dev.off()') ## we still need to turn off the graphics device
            print 'Plotting exception occured'
            raise Exception(unicode(inst))
            
        self.R('dev.off()')
        self.clear()
        self.addImage(file)
        self.fitInView(self.mainItem.boundingRect(), Qt.KeepAspectRatio)
    def setExtrasLineEditEnabled(self, enabled = True):
        
        self.extrasLineEdit.enabled(enabled)
        if enabled:
            self.extrasLineEdit.show()
        else:
            self.extrasLineEdit.hide()
    def printMe(self):
        printer = QPrinter()
        printDialog = QPrintDialog(printer)
        if printDialog.exec_() == QDialog.Rejected: 
            print 'Printing Rejected'
            return
        painter = QPainter(printer)
        self.scene().render(painter)
        painter.end()    
    

    #########################
    ## R session functions ##
    #########################
    def R(self, query):
        return RSession.Rcommand(query = query)
    def require_librarys(self, libraries):
        return RSession.require_librarys(libraries)
        
    ##########################
    ## Interaction Functions #
    ##########################
    def clear(self):
        if self.scene():
            self.scene().clear()
        else:
            print 'loading scene'
            scene = QGraphicsScene()
            self.setScene(scene)
    def dialogClosed(self, int):
        self.backToParent()

    def toClipboard(self):
        QApplication.clipboard().setImage(self.returnImage())
    def saveAsSVG(self):
        print 'save as svg'
        qname = QFileDialog.getSaveFileName(self, "Save Image", redREnviron.directoryNames['documentsDir'] + "/Image-"+unicode(datetime.date.today())+".svg", "Vector Graphics (.svg)")
        if qname.isEmpty(): return
        qname = unicode(qname)
        self.saveAs(unicode(qname), 'svg')
    def saveAsPDF(self):
        print 'save as pdf'
        qname = QFileDialog.getSaveFileName(self, "Save Image", redREnviron.directoryNames['documentsDir'] + "/Image-"+unicode(datetime.date.today())+".pdf", "PDF Document (.pdf)")
        if qname.isEmpty(): return
        qname = unicode(qname)
        self.saveAs(unicode(qname), 'pdf')
    def saveAsPostScript(self):
        print 'save as post script'
        qname = QFileDialog.getSaveFileName(self, "Save Image", redREnviron.directoryNames['documentsDir'] + "/Image-"+unicode(datetime.date.today())+".eps", "Post Script (.eps)")
        if qname.isEmpty(): return
        qname = unicode(qname)
        self.saveAs(unicode(qname), 'ps')
    def saveAsBitmap(self):
        print 'save as bitmap'
        qname = QFileDialog.getSaveFileName(self, "Save Image", redREnviron.directoryNames['documentsDir'] + "/Image-"+unicode(datetime.date.today())+".bmp", "Bitmap (.bmp)")
        if qname.isEmpty(): return
        qname = unicode(qname)
        self.saveAs(unicode(qname), 'bmp')
    def saveAsJPEG(self):
        print 'save as jpeg'
        qname = QFileDialog.getSaveFileName(self, "Save Image", redREnviron.directoryNames['documentsDir'] + "/Image-"+unicode(datetime.date.today())+".jpg", "JPEG Image (.jpg)")
        if qname.isEmpty(): return
        qname = unicode(qname)
        self.saveAs(unicode(qname), 'jpeg')
    def backToParent(self):
        self.parent.layout().addWidget(self.controlArea)
        self.dialog.hide()
    def mousePressEvent(self, mouseEvent):
        
        if mouseEvent.button() == Qt.RightButton:
            # remove the selection rect
            if self.widgetSelectionRect:
                self.widgetSelectionRect.hide()
                self.widgetSelectionRect = None
            
            # show the action menu
            newCoords = QPoint(mouseEvent.globalPos())
            action = self.menu.exec_(newCoords)
            if action:
                if unicode(action.text()) == 'Copy':
                    self.toClipboard()
                elif unicode(action.text()) == 'Zoom Out':
                    self.scale(0.80, 0.80)
                elif unicode(action.text()) == 'Zoom In':
                    self.scale(1.50, 1.50)
                elif unicode(action.text()) == 'Undock':
                    ## want to undock from the widget and make an independent viewing dialog.
                    self.dialog.layout().addWidget(self.controlArea)
                    self.dialog.show()
                elif unicode(action.text()) == 'Redock':
                    self.parent.layout().addWidget(self.controlArea)
                    self.dialog.hide()
                elif unicode(action.text()) == 'Fit In Window':
                    print self.mainItem.boundingRect()
                    self.fitInView(self.mainItem.boundingRect(), Qt.KeepAspectRatio)
                elif unicode(action.text()) == 'Bitmap':
                    self.saveAsBitmap()
                elif unicode(action.text()) == 'PDF':
                    self.saveAsPDF()
                elif unicode(action.text()) == 'Post Script':
                    self.saveAsPostScript()
                elif unicode(action.text()) == 'JPEG':
                    self.saveAsJPEG()
                elif unicode(action.text()) == 'SVG':
                    self.saveAsSVG()
                elif unicode(action.text()) == 'R Graphics Device':
                    self.rGraphicsDevice()
        else:
            self.mouseDownPosition = self.mapToScene(mouseEvent.pos())
            self.widgetSelectionRect = QGraphicsRectItem(QRectF(self.mouseDownPosition, self.mouseDownPosition), None, self.scene())
            self.widgetSelectionRect.setZValue(-100)
            self.widgetSelectionRect.show()
    def mouseMoveEvent(self, ev):
        point = self.mapToScene(ev.pos())

        if self.widgetSelectionRect:
            self.widgetSelectionRect.setRect(QRectF(self.mouseDownPosition, point))            

        self.scene().update()
    def mouseReleaseEvent(self, ev):
        point = self.mapToScene(ev.pos())
        if self.widgetSelectionRect:
            self.fitInView(self.widgetSelectionRect.rect(), Qt.KeepAspectRatio)
            self.widgetSelectionRect.hide()
            self.widgetSelectionRect = None
            
        self.scene().update()

    def returnImage(self):
        ## generate a rendering of the graphicsView and return the image
        
        size = self.scene().sceneRect().size()
        image = QImage(int(self.scene().width()), int(self.scene().height()), QImage.Format_ARGB32_Premultiplied)
        painter = QPainter(image)
        self.scene().render(painter)
        painter.end()
        return image
        
    def addImage(self, image, imageType = None):
        ## add an image to the view
        #self.image = os.path.abspath(image)
        #print self.image
        # print 'Addign Image'
        if image == '': return
        if not self.scene():
            # print 'loading scene'
            scene = QGraphicsScene()
            self.setScene(scene)
        if imageType == None:
            imageType = self.imageType
        if imageType not in ['svg', 'png', 'jpeg']:
            self.clear()
            print imageType, 'Error occured'
            raise Exception, 'Image type specified is not a valid type for this widget.'
        if imageType == 'svg':
            #self.convertSVG(unicode(os.path.join(redREnviron.directoryNames['tempDir'], image)).replace('\\', '/')) ## handle the conversion to glyph free svg
            mainItem = QGraphicsSvgItem(unicode(os.path.join(redREnviron.directoryNames['tempDir'], image)).replace('\\', '/'))
        elif imageType in ['png', 'jpeg']:
            mainItem = QGraphicsPixmapItem(QPixmap(os.path.join(redREnviron.directoryNames['tempDir'], image.replace('\\', '/'))))
        else:
            raise Exception, 'Image type %s not specified in a plotting method' % imageType
            #mainItem = QGraphicsPixmapItem(QPixmap(image))
        self.scene().addItem(mainItem)
        self.mainItem = mainItem
        
    def getSettings(self):
        #print '#################in getSettings'
        r = {'image':self.imageFileName, 'query':self.printQuery, 'function':self.function}
        
        #print r
        return r
    def loadSettings(self,data):
        self.printQuery = data['query']
        self.function = data['function']
        self.addImage(data['image'])
    def getReportText(self, fileDir):
        
        image = self.returnImage()
        image = image.scaled(1000,1000, Qt.KeepAspectRatio)
        imageFile = os.path.join(fileDir, self.image + '.png').replace('\\', '/')
        if not image.save(imageFile):
            print 'Error in saving image in graphicsView'
            return ''
        
        text = '.. image:: %s\n    :scale: 50%%\n\n' % imageFile
        
        return {self.widgetName:{'includeInReports':self.includeInReports,'text':text}}  
        
    def saveAs(self, fileName, imageType):
        if self.printQuery == '': return
        opts = {'FILE':fileName.replace('\\', '/'), 'WIDTH':self.widthSpinBox.value() , 'HEIGHT':self.heightSpinBox.value()}
        if imageType == 'pdf':
            self.R('pdf(file = \'%(FILE)s\', width = %(WIDTH)s, height = %(HEIGHT)s)' % opts)
        elif imageType == 'ps':
            self.R('postscript(file = \'%(FILE)s\', width = %(WIDTH)s, height = %(HEIGHT)s)' % opts)
        elif imageType == 'bmp':
            self.R('bmp(file = \'%(FILE)s\', width = %(WIDTH)s, height = %(HEIGHT)s, units = "in")' % opts)
        elif imageType == 'jpeg':
            self.R('jpeg(file = \'%(FILE)s\', width = %(WIDTH)s, height = %(HEIGHT)s, units = "in")' % opts)
        elif imageType == 'svg':
            self.R('devSVG(file = \'%(FILE)s\', width = %(WIDTH)s, height = %(HEIGHT)s)' % opts)
            
        self.R(self.printQuery)
        
        self.R('dev.off()')
    def rGraphicsDevice(self):
        self.R(self.printQuery)
    ###########
    ## Convert an SVG for pyqt
    ###########
    def convertSVG(self, file):
        print file
        dom = self._getsvgdom(file)
        #print dom
        self._switchGlyphsForPaths(dom)
        self._commitSVG(file, dom)
    def _commitSVG(self, file, dom):
        f = open(file, 'w')
        dom.writexml(f)
        f.close()
    def _getsvgdom(self, file):
        print 'getting DOM model'
        import xml.dom
        import xml.dom.minidom as mini
        f = open(file, 'r')
        svg = f.read()
        f.close()
        dom = mini.parseString(svg)
        return dom
    def _getGlyphPaths(self, dom):
        symbols = dom.getElementsByTagName('symbol')
        glyphPaths = {}
        for s in symbols:
            pathNode = [p for p in s.childNodes if 'tagName' in dir(p) and p.tagName == 'path']
            glyphPaths[s.getAttribute('id')] = pathNode[0].getAttribute('d')
        return glyphPaths
    def _switchGlyphsForPaths(self, dom):
        glyphs = self._getGlyphPaths(dom)
        use = self._getUseTags(dom)
        for glyph in glyphs.keys():
            #print glyph
            nl = self.makeNewList(glyphs[glyph].split(' '))
            u = self._matchUseGlyphs(use, glyph)
            for u2 in u:
                #print u2, 'brefore'
                self._convertUseToPath(u2, nl)
                #print u2, 'after'
            
    def _getUseTags(self, dom):
        return dom.getElementsByTagName('use')
    def _matchUseGlyphs(self, use, glyph):
        matches = []
        for i in use:
            #print i.getAttribute('xlink:href')
            if i.getAttribute('xlink:href') == '#'+glyph:
                matches.append(i)
        #print matches
        return matches
    def _convertUseToPath(self, use, strokeD):
        ## strokeD is a list of lists of strokes to make the glyph
        newD = self.nltostring(self.resetStrokeD(strokeD, use.getAttribute('x'), use.getAttribute('y')))
        use.tagName = 'path'
        use.removeAttribute('xlink:href')
        use.removeAttribute('x')
        use.removeAttribute('y')
        use.setAttribute('style', 'fill: rgb(0%,0%,0%); stroke-width: 0.5; stroke-linecap: round; stroke-linejoin: round; stroke: rgb(0%,0%,0%); stroke-opacity: 1;stroke-miterlimit: 10; ')
        use.setAttribute('d', newD)
    def makeNewList(self, inList):
        i = 0
        nt = []
        while i < len(inList):
            start = i + self.listFind(inList[i:], ['M', 'L', 'C', 'Z'])
            end = start + self.listFind(inList[start+1:], ['M', 'L', 'C', 'Z', '', ' '])
            nt.append(inList[start:end+1])
            i = end + 1
        return nt
    def listFind(self, x, query):
        for i in range(len(x)):
            if x[i] in query:
                return i
        return len(x)
    def resetStrokeD(self, strokeD, x, y):
        nsd = []
        for i in strokeD:
            nsd.append(self.resetXY(i, x, y))
        return nsd
    def resetXY(self, nl, x, y): # convert a list of strokes to xy coords
        nl2 = []
        for i in range(len(nl)):
            if i == 0:
                nl2.append(nl[i])
            elif i%2: # it's odd
                nl2.append(float(nl[i]) + float(x))
            elif not i%2: # it's even
                nl2.append(float(nl[i]) + float(y))
            else:
                print i, nl[i], 'error'
        return nl2
    def nltostring(self, nl): # convert a colection of nl's to a string
        col = []
        for l in nl:
            templ = []
            for c in l:
                templ.append(unicode(c))
            templ = ' '.join(templ)
            col.append(templ)
        return ' '.join(col)
        
    
class colorListDialog(QDialog):
    def __init__(self, parent = None, layout = 'vertical', title = 'Color List Dialog', data = ''):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        if layout == 'horizontal':
            self.setLayout(QHBoxLayout())
        else:
            self.setLayout(QVBoxLayout())
        
        self.listOfColors = []
        self.controlArea = widgetBox(self)
        mainArea = widgetBox(self.controlArea, 'horizontal')
        leftBox = widgetBox(mainArea)
        rightBox = widgetBox(mainArea)
        ## GUI
        
        # color list
        self.colorList = listBox(leftBox, label = 'Color List')
        button(leftBox, label = 'Add Color', callback = self.addColor)
        button(leftBox, label = 'Remove Color', callback = self.removeColor)
        button(leftBox, label = 'Clear Colors', callback = self.colorList.clear)
        button(mainArea, label = 'Finished', callback = self.accept)
        # attribute list
        self.attsList = listBox(rightBox, label = 'Data Parameters', callback = self.attsListSelected)
        if data:
            names = self.R('names('+data+')')
            print names
            self.attsList.update(names)
        self.data = data
    def attsListSelected(self):
        ## return a list of numbers coresponding to the levels of the data selected.
        self.listOfColors = self.R('as.numeric(as.factor('+self.data+'$'+unicode(self.attsList.selectedItems()[0])+'))')
        
    def addColor(self):
        colorDialog = QColorDialog(self)
        color = colorDialog.getColor()
        colorDialog.hide()
        newItem = QListWidgetItem()
        newItem.setBackgroundColor(color)
        self.colorList.addItem(newItem)
        
        self.processColors()
    def removeColor(self):
        for item in self.colorList.selectedItems():
            self.colorList.removeItemWidget(item)
            
        self.processColors()
    def setColors(self, colorList):
        self.colorList.clear()
        try:
            for c in colorList:
                col = QColor()
                col.setNamedColor(unicode(c))
                newItem = QListWidgetItem()
                newItem.setBackgroundColor(col)
                self.colorList.addItem(newItem)
        except:
            pass # it might happen that we can't show the colors that's not good but also not disasterous either.
    def processColors(self):
        self.listOfColors = []
        for item in self.colorList.items():
            self.listOfColors.append('"'+unicode(item.backgroundColor().name())+'"')
    def R(self, query):
        return RSession.Rcommand(query = query)

class dialog(QDialog):
    def __init__(self, parent, layout = 'vertical',title=None):
        QDialog.__init__(self,parent)
        self.ltys = []
        self.parent = parent
        if title:
            self.setWindowTitle(title)
        if layout == 'horizontal':
            self.setLayout(QHBoxLayout())
        else:
            self.setLayout(QVBoxLayout())


class ColorIcon(QToolButton):
    def __init__(self, parent, label):
        box = widgetBox(parent,orientation='horizontal')       
        a = widgetLabel(box,label=label)
        QToolButton.__init__(self, box)
        box.layout().addWidget(self)
        # if not color:
        self.color = '#000000'
        # else:
            # self.color = color
            
        self.setMaximumSize(20,20)
        self.connect(self, SIGNAL("clicked()"), self.showColorDialog)
        # self.updateColor()

    def updateColor(self):
        pixmap = QPixmap(16,16)
        painter = QPainter()
        painter.begin(pixmap)
        painter.setPen(QPen(QColor(self.color)))
        painter.setBrush(QBrush(QColor(self.color)))
        painter.drawRect(0, 0, 16, 16);
        painter.end()
        self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(16,16))


    def drawButtonLabel(self, painter):
        painter.setBrush(QBrush(QColor(self.color)))
        painter.setPen(QPen(QColor(self.color)))
        painter.drawRect(3, 3, self.width()-6, self.height()-6)

    def showColorDialog(self):
        color = QColorDialog.getColor(QColor(self.color), self)
        if color.isValid():
            self.color = color.name()
            self.updateColor()
            self.repaint()
