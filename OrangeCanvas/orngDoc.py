# Author: Gregor Leban (gregor.leban@fri.uni-lj.si) modified by Kyle R Covington and Anup Parikh
# Description:
#    document class - main operations (save, load, ...)
#
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys, os, os.path, traceback
from xml.dom.minidom import Document, parse
import orngView, orngCanvasItems, orngTabs
from orngDlgs import *
from orngSignalManager import SignalManager
import cPickle, math, orngHistory, zipfile

class SchemaDoc(QWidget):
    def __init__(self, canvasDlg, *args):
        QWidget.__init__(self, *args)
        self.canvasDlg = canvasDlg
        self.ctrlPressed = 0

        self.lines = []                         # list of orngCanvasItems.CanvasLine items
        self.widgets = []                       # list of orngCanvasItems.CanvasWidget items
        self.signalManager = SignalManager()    # signal manager to correctly process signals

        self.schemaPath = self.canvasDlg.settings["saveSchemaDir"]
        self.schemaName = ""
        self.loadedSettingsDict = {}
        self.setLayout(QVBoxLayout())
        #self.canvas = QGraphicsScene(0,0,2000,2000)
        self.canvas = QGraphicsScene()
        self.canvasView = orngView.SchemaView(self, self.canvas, self)
        self.layout().addWidget(self.canvasView)
        self.layout().setMargin(0)
        self.schemaID = orngHistory.logNewSchema()
        self.RVariableRemoveSupress = 0


    # we are about to close document
    # ask the user if he is sure
    def closeEvent(self,ce):
        res = QMessageBox.question(self, 'Red-R Canvas','Do you wish to save the schema?', QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel)
        
        if res == QMessageBox.Yes:
            newSettings = self.loadedSettingsDict and self.loadedSettingsDict != dict([(widget.caption, widget.instance.saveSettingsStr()) for widget in self.widgets])
            self.RVariableRemoveSupress = 1
            self.synchronizeContexts()
            #if self.canvasDlg.settings["autoSaveSchemasOnClose"] and self.widgets != []:
            # if self.widgets != []:
                # self.save(os.path.join(self.canvasDlg.canvasSettingsDir, "lastSchema.tmp"))

            saveComplete = self.saveDocument()
            
            if not saveComplete: 
                QMessageBox.information(self, 'Red-R Canvas','Save interupted because no file name specified.\nData not saved.',  QMessageBox.Ok + QMessageBox.Default)
                print 'Saving interupted'
                ce.ignore()
                return
            ce.accept()
            self.clear(close = True)
        # if self.canvasDlg.settings["dontAskBeforeClose"]:
            # if newSettings and self.schemaName != "":
                # pass
                ##self.save(True)
            # self.clear(close = True)  
            # self.removeTempDoc()
            # ce.accept()
        elif res == QMessageBox.No:
            self.RVariableRemoveSupress = 1
            self.clear(close = True)
            ce.accept()
        else:
            ce.ignore()
            return
            
            # res = QMessageBox.question(self, 'Orange Canvas','Do you wish to save the schema?', QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel)
            # if res == QMessageBox.Yes:
                # self.saveDocument()
                # ce.accept()
                # self.clear(close = True)
            # elif res == QMessageBox.No:
                # self.clear(close = True)
                # self.removeTempDoc()
                # ce.accept()
            # else:
                # ce.ignore()     # we pressed cancel - we don't want to close the document
                # return
        QWidget.closeEvent(self, ce)
        orngHistory.logCloseSchema(self.schemaID)
        
    # save a temp document whenever anything changes. this doc is deleted on closeEvent
    # in case that Orange crashes, Canvas on the next start offers an option to reload the crashed schema with links frozen
    def saveTempDoc(self):
        return
        if self.widgets != []:
            tempName = os.path.join(self.canvasDlg.canvasSettingsDir, "tempSchema.tmp")
            self.save(tempName,True)
        
    def removeTempDoc(self):
        tempName = os.path.join(self.canvasDlg.canvasSettingsDir, "tempSchema.tmp")
        if os.path.exists(tempName):
            os.remove(tempName)

    # called to properly close all widget contexts
    def synchronizeContexts(self):
        for widget in self.widgets[::-1]:
            widget.instance.synchronizeContexts()

    # add line connecting widgets outWidget and inWidget
    # if necessary ask which signals to connect
    def addLine(self, outWidget, inWidget, enabled = True):
        if outWidget == inWidget: 
            return None
        # check if line already exists
        line = self.getLine(outWidget, inWidget)
        if line:
            self.resetActiveSignals(outWidget, inWidget, None, enabled)
            return None

        if self.signalManager.existsPath(inWidget.instance, outWidget.instance):
            QMessageBox.critical( self, "Failed to Connect", "Circular connections are not allowed in Orange Canvas.", QMessageBox.Ok)
            return None

        dialog = SignalDialog(self.canvasDlg, None)
        dialog.setOutInWidgets(outWidget, inWidget)
        connectStatus = dialog.addDefaultLinks()
        if connectStatus == 0:
            QMessageBox.information( self, "Failed to Connect", "Selected widgets don't share a common signal type.", QMessageBox.Ok)
            return

        # if there are multiple choices, how to connect this two widget, then show the dialog
        if len(dialog.getLinks()) > 1 or dialog.multiplePossibleConnections or dialog.getLinks() == []:
            if dialog.exec_() == QDialog.Rejected:
                return None

        self.signalManager.setFreeze(1)
        linkCount = 0
        for (outName, inName) in dialog.getLinks():
            linkCount += self.addLink(outWidget, inWidget, outName, inName, enabled)

        self.signalManager.setFreeze(0, outWidget.instance)

        # if signals were set correctly create the line, update widget tooltips and show the line
        line = self.getLine(outWidget, inWidget)
        if line:
            outWidget.updateTooltip()
            inWidget.updateTooltip()
            
        self.saveTempDoc()
        return line


    # reset signals of an already created line
    def resetActiveSignals(self, outWidget, inWidget, newSignals = None, enabled = 1):
        #print "<extra>orngDoc.py - resetActiveSignals() - ", outWidget, inWidget, newSignals
        signals = []
        for line in self.lines:
            if line.outWidget == outWidget and line.inWidget == inWidget:
                signals = line.getSignals()

        if newSignals == None:
            dialog = SignalDialog(self.canvasDlg, None)
            dialog.setOutInWidgets(outWidget, inWidget)
            for (outName, inName) in signals:
                #print "<extra>orngDoc.py - SignalDialog.addLink() - adding signal to dialog: ", outName, inName
                dialog.addLink(outName, inName)

            # if there are multiple choices, how to connect this two widget, then show the dialog
            if dialog.exec_() == QDialog.Rejected:
                return

            newSignals = dialog.getLinks()

        for (outName, inName) in signals:
            if (outName, inName) not in newSignals:
                self.removeLink(outWidget, inWidget, outName, inName)
                signals.remove((outName, inName))

        self.signalManager.setFreeze(1)
        for (outName, inName) in newSignals:
            if (outName, inName) not in signals:
                self.addLink(outWidget, inWidget, outName, inName, enabled)
        self.signalManager.setFreeze(0, outWidget.instance)

        outWidget.updateTooltip()
        inWidget.updateTooltip()



    # add one link (signal) from outWidget to inWidget. if line doesn't exist yet, we create it
    def addLink(self, outWidget, inWidget, outSignalName, inSignalName, enabled = 1, fireSignal = 1):
        #print "<extra>orngDoc - addLink() - ", outWidget, inWidget, outSignalName, inSignalName
        # in case there already exists link to inSignalName in inWidget that is single, we first delete it
        widgetInstance = inWidget.instance.removeExistingSingleLink(inSignalName)
        if widgetInstance:
            widget = self.findWidgetFromInstance(widgetInstance)
            existingSignals = self.signalManager.findSignals(widgetInstance, inWidget.instance)
            for (outN, inN) in existingSignals:
                if inN == inSignalName:
                    self.removeLink(widget, inWidget, outN, inN)
                    line = self.getLine(widget, inWidget)
                    if line:
                        line.updateTooltip()

        # if line does not exist yet, we must create it
        existingSignals = self.signalManager.findSignals(outWidget.instance, inWidget.instance)
        if not existingSignals:
            line = orngCanvasItems.CanvasLine(self.signalManager, self.canvasDlg, self.canvasView, outWidget, inWidget, self.canvas)
            self.lines.append(line)
            line.setEnabled(enabled)
            line.show()
            outWidget.addOutLine(line)
            outWidget.updateTooltip()
            inWidget.addInLine(line)
            inWidget.updateTooltip()
        else:
            line = self.getLine(outWidget, inWidget)

        ok = self.signalManager.addLink(outWidget.instance, inWidget.instance, outSignalName, inSignalName, enabled)
        if not ok:
            self.removeLink(outWidget, inWidget, outSignalName, inSignalName)
            QMessageBox.warning( None, "Orange Canvas", "Unable to add link. Something is really wrong; try restarting Orange Canvas.", QMessageBox.Ok + QMessageBox.Default )
            return 0
        else:
            orngHistory.logAddLink(self.schemaID, outWidget, inWidget, outSignalName)

        line.updateTooltip()
        return 1


    # remove only one signal from connected two widgets. If no signals are left, delete the line
    def removeLink(self, outWidget, inWidget, outSignalName, inSignalName):
        #print "<extra> orngDoc.py - removeLink() - ", outWidget, inWidget, outSignalName, inSignalName
        self.signalManager.removeLink(outWidget.instance, inWidget.instance, outSignalName, inSignalName)

        otherSignals = 0
        if self.signalManager.links.has_key(outWidget.instance):
            for (widget, signalFrom, signalTo, enabled) in self.signalManager.links[outWidget.instance]:
                    if widget == inWidget.instance:
                        otherSignals = 1
        if not otherSignals:
            self.removeLine(outWidget, inWidget)

        self.saveTempDoc()


    # remove line line
    def removeLine1(self, line, close = False):
        #print 'removing a line from' + str(outName) +'to' +str(inName)
        for (outName, inName) in line.getSignals():
            self.signalManager.removeLink(line.outWidget.instance, line.inWidget.instance, outName, inName, close = close)   # update SignalManager

        self.lines.remove(line)
        line.inWidget.removeLine(line)
        line.outWidget.removeLine(line)
        line.inWidget.updateTooltip()
        line.outWidget.updateTooltip()
        line.remove()
        self.saveTempDoc()

    # remove line, connecting two widgets
    def removeLine(self, outWidget, inWidget):
        #print "<extra> orngDoc.py - removeLine() - ", outWidget, inWidget
        line = self.getLine(outWidget, inWidget)
        if line:
            self.removeLine1(line)

    # add new widget
    def addWidget(self, widgetInfo, x= -1, y=-1, caption = "", widgetSettings = {}, saveTempDoc = True, forceInSignals = None, forceOutSignals = None):
        qApp.setOverrideCursor(Qt.WaitCursor)
        try:
            #print str(forceInSignals) 
            #print str(forceOutSignals)
            #print 'adding widget '+caption
            newwidget = orngCanvasItems.CanvasWidget(self.signalManager, self.canvas, self.canvasView, widgetInfo, self.canvasDlg.defaultPic, self.canvasDlg, widgetSettings, forceInSignals = forceInSignals, forceOutSignals = forceOutSignals)
            #if widgetInfo.name == 'dummy' and (forceInSignals or forceOutSignals):
        except:
            type, val, traceback = sys.exc_info()
            sys.excepthook(type, val, traceback)  # we pretend that we handled the exception, so that it doesn't crash canvas
            qApp.restoreOverrideCursor()
            return None

        if x==-1 or y==-1:
            if self.widgets != []:
                x = self.widgets[-1].x() + 110
                y = self.widgets[-1].y()
            else:
                x = 30
                y = 150
        newwidget.setCoords(x, y)
        # move the widget to a valid position if necessary
        invalidPosition = (self.canvasView.findItemTypeCount(self.canvas.collidingItems(newwidget), orngCanvasItems.CanvasWidget) > 0)
        if invalidPosition:
            for r in range(20, 200, 20):
                for fi in [90, -90, 180, 0, 45, -45, 135, -135]:
                    xOff = r * math.cos(math.radians(fi))
                    yOff = r * math.sin(math.radians(fi))
                    rect = QRectF(x+xOff, y+yOff, 48, 48)
                    invalidPosition = self.canvasView.findItemTypeCount(self.canvas.items(rect), orngCanvasItems.CanvasWidget) > 0
                    if not invalidPosition:
                        newwidget.setCoords(x+xOff, y+yOff)
                        break
                if not invalidPosition:
                    break
            
        #self.canvasView.ensureVisible(newwidget)

        if caption == "": caption = newwidget.caption

        if self.getWidgetByCaption(caption):
            i = 2
            while self.getWidgetByCaption(caption + " (" + str(i) + ")"): i+=1
            caption = caption + " (" + str(i) + ")"
        newwidget.updateText(caption)
        newwidget.instance.setWindowTitle(caption)

        self.widgets.append(newwidget)
        if saveTempDoc:
            self.saveTempDoc()
        self.canvas.update()

        # show the widget and activate the settings
        try:
            self.signalManager.addWidget(newwidget.instance)
            newwidget.show()
            newwidget.updateTooltip()
            newwidget.setProcessing(1)
            if self.canvasDlg.settings["saveWidgetsPosition"]:
                newwidget.instance.restoreWidgetPosition()
            newwidget.setProcessing(0)
            orngHistory.logAddWidget(self.schemaID, id(newwidget), (newwidget.widgetInfo.category, newwidget.widgetInfo.name), newwidget.x(), newwidget.y())
        except:
            type, val, traceback = sys.exc_info()
            sys.excepthook(type, val, traceback)  # we pretend that we handled the exception, so that it doesn't crash canvas

        qApp.restoreOverrideCursor()
        return newwidget

    # remove widget
    def removeWidget(self, widget, saveTempDoc = True, close = False):
        if not widget:
            return
        widget.closing = close
        while widget.inLines != []: self.removeLine1(widget.inLines[0], close = True)
        while widget.outLines != []:  self.removeLine1(widget.outLines[0], close = True)

        self.signalManager.removeWidget(widget.instance) # sending occurs before this point
        self.widgets.remove(widget)
        if self.RVariableRemoveSupress == 1: #send occurs before this point
            widget.remove(suppress = 1)
        else:
            widget.remove()
        if self.RVariableRemoveSupress == 1:
            return
        if saveTempDoc:
            self.saveTempDoc()
        
        orngHistory.logRemoveWidget(self.schemaID, id(widget), (widget.widgetInfo.category, widget.widgetInfo.name))

    def clear(self, close = False):
        print 'clear called'
        self.canvasDlg.setCaption()
        for widget in self.widgets[::-1]:   
            self.removeWidget(widget, saveTempDoc = False, close = close)   # remove widgets from last to first
        self.canvas.update()
        self.saveTempDoc()

    def enableAllLines(self):
        for line in self.lines:
            self.signalManager.setLinkEnabled(line.outWidget.instance, line.inWidget.instance, 1)
            line.setEnabled(1)
            #line.repaintLine(self.canvasView)
        self.canvas.update()

    def disableAllLines(self):
        for line in self.lines:
            self.signalManager.setLinkEnabled(line.outWidget.instance, line.inWidget.instance, 0)
            line.setEnabled(0)
            #line.repaintLine(self.canvasView)
        self.canvas.update()

    # return a new widget instance of a widget with filename "widgetName"
    def addWidgetByFileName(self, widgetFileName, x, y, caption, widgetSettings = {}, saveTempDoc = True, forceInSignals = None, forceOutSignals = None):
        for category in self.canvasDlg.widgetRegistry.keys():
            for name, widget in self.canvasDlg.widgetRegistry[category].items():
                if widget.fileName == widgetFileName:  
                    #print str(forceInSignals) + 'force in signals'
                    #print str(forceOutSignals) + 'force out signals'
                    return self.addWidget(widget, x, y, caption, widgetSettings, saveTempDoc, forceInSignals, forceOutSignals)
        return None

    # return the widget instance that has caption "widgetName"
    def getWidgetByCaption(self, widgetName):
        for widget in self.widgets:
            if (widget.caption == widgetName):
                return widget
        return None

    def getWidgetCaption(self, widgetInstance):
        for widget in self.widgets:
            if widget.instance == widgetInstance:
                return widget.caption
        print "Error. Invalid widget instance : ", widgetInstance
        return ""


    # get line from outWidget to inWidget
    def getLine(self, outWidget, inWidget):
        for line in self.lines:
            if line.outWidget == outWidget and line.inWidget == inWidget:
                return line
        return None


    # find orngCanvasItems.CanvasWidget from widget instance
    def findWidgetFromInstance(self, widgetInstance):
        for widget in self.widgets:
            if widget.instance == widgetInstance:
                return widget
        return None

    # ###########################################
    # SAVING, LOADING, ....
    # ###########################################
    def saveDocument(self):
        if self.schemaName == "":
            return self.saveDocumentAs()
        else:
            return self.save(None,False)

    def saveDocumentAs(self):
        name = QFileDialog.getSaveFileName(self, "Save File", os.path.join(self.schemaPath, self.schemaName), "Orange Widget Schema (*.ows)")
        
        if not name or name == None: return False
        if str(name) == '': return False
        if os.path.splitext(str(name))[0] == "": return False
        if os.path.splitext(str(name))[1].lower() != ".ows": name = os.path.splitext(str(name))[0] + ".ows"
        return self.save(str(name),False)
        

    # save the file
    def save(self, filename = None,tmp = True):
        if filename == None:
            filename = os.path.join(self.schemaPath, self.schemaName)
        
        # create xml document
        doc = Document()
        schema = doc.createElement("schema")
        widgets = doc.createElement("widgets")
        lines = doc.createElement("channels")
        settings = doc.createElement("settings")
        doc.appendChild(schema)
        schema.appendChild(widgets)
        schema.appendChild(lines)
        schema.appendChild(settings)
        settingsDict = {}

        
        #save widgets
        for widget in self.widgets:
            temp = doc.createElement("widget")
            temp.setAttribute("xPos", str(int(widget.x())) )
            temp.setAttribute("yPos", str(int(widget.y())) )
            temp.setAttribute("caption", widget.caption)
            temp.setAttribute("widgetName", widget.widgetInfo.fileName)
            #temp.setAttribute("InSignals", widget.instance.inputs) # saves the inputs and outputs in case of failure to find the parent widget.  In this case a dummy is put in it's place and the loading can continue
            #temp.setAttribute("OutSignals", widget.instance.outputs)
            # if not tmp:
                # widget.instance.onSaveSession()
            #print 'looking for settingsstr'
            #try:
            settingsDict[widget.caption] = widget.instance.saveSettingsStr()
            #print str(settingsDict[widget.caption]) + '\n\n settings Dict (orngDoc)'
            # except:
                # settingsDict[widget.caption] = None
                #sprint str(widget.caption) + 'failed to save some settings'
            widgets.appendChild(temp)

        #save connections
        for line in self.lines:
            temp = doc.createElement("channel")
            temp.setAttribute("outWidgetCaption", line.outWidget.caption)
            temp.setAttribute("inWidgetCaption", line.inWidget.caption)
            temp.setAttribute("enabled", str(line.getEnabled()))
            temp.setAttribute("signals", str(line.getSignals()))
            lines.appendChild(temp)

        settings.setAttribute("settingsDictionary", str(settingsDict))      
        
        xmlText = doc.toprettyxml()

        if not tmp:
            tempschema = os.path.join(self.canvasDlg.canvasSettingsDir, "tempSchema.tmp")
            tempR = os.path.join(self.canvasDlg.canvasSettingsDir, "tmp.RData").replace('\\','/')
            file = open(tempschema, "wt")
            file.write(xmlText)
            file.close()
            doc.unlink()
            print 'saving image...'
            import rpy
            rpy.r('save.image("' + tempR + '")')
            zout = zipfile.ZipFile(filename, "w")
            for fname in [tempschema,tempR]:
                zout.write(fname)
            zout.close()
            os.remove(tempR)
            os.remove(tempschema)
            print 'image saved'
        else :
            file = open(filename, "wt")
            file.write(xmlText)
            file.close()
            doc.unlink()
            
        
        if os.path.splitext(filename)[1].lower() == ".ows":
            (self.schemaPath, self.schemaName) = os.path.split(filename)
            self.canvasDlg.settings["saveSchemaDir"] = self.schemaPath
            self.canvasDlg.addToRecentMenu(filename)
            self.canvasDlg.setCaption(self.schemaName)
        
        return True
    # load a scheme with name "filename"
    def loadDocument(self, filename, caption = None, freeze = 0, importBlank = 0):
        print 'document load called'
        #self.clear()
        
        if not os.path.exists(filename):
            if os.path.splitext(filename)[1].lower() != ".tmp":
                QMessageBox.critical(self, 'Orange Canvas', 'Unable to locate file "'+ filename + '"',  QMessageBox.Ok)
            return

        # set cursor
        qApp.setOverrideCursor(Qt.WaitCursor)
        failureText = ""
        
        if os.path.splitext(filename)[1].lower() == ".ows":
            self.schemaPath, self.schemaName = os.path.split(filename)
            self.canvasDlg.setCaption(caption or self.schemaName)
        if not importBlank:
            try:
                #load the data ...
                try:
                    from rpy_options import set_options
                    set_options(RHOME=os.environ['RPATH'])
                except: pass
                import rpy
                import re

                zfile = zipfile.ZipFile( str(filename), "r" )
                for name in zfile.namelist():
                    file(os.path.join(self.canvasDlg.canvasSettingsDir,os.path.basename(name)), 'wb').write(zfile.read(name))
                    if re.search('tempSchema.tmp',os.path.basename(name)):
                        doc = parse(os.path.join(self.canvasDlg.canvasSettingsDir,os.path.basename(name)))
                    else:
                        #print 'loading R session ...'
                        # insert function to load all R packages that were loaded in the previous session
                        #self.settings
                        rpy.r('load("' + os.path.join(self.canvasDlg.canvasSettingsDir,os.path.basename(name)).replace('\\','/') +'")')
                #print "Loading widgets "+str(self.widgets) + "(orngDoc.py)"
                for widget in self.widgets:
                    widget.caption += 'A'
                
                
                schema = doc.firstChild
                widgets = schema.getElementsByTagName("widgets")[0]
                lines = schema.getElementsByTagName("channels")[0]
                settings = schema.getElementsByTagName("settings")
                settingsDict = eval(str(settings[0].getAttribute("settingsDictionary")))
                self.loadedSettingsDict = settingsDict
                  
                # read widgets
                loadedOk = 1
                for widget in widgets.getElementsByTagName("widget"):
                    try:
                        name = widget.getAttribute("widgetName")
                        #print 'Name: '+str(name)+' (orngDoc.py)'
                        #print str(widget.getAttribute("caption"))
                        #print str(settingsDict)
                        settings = cPickle.loads(settingsDict[widget.getAttribute("caption")])
                        #print str(settings) + ' (orngDoc.py)'
                        #print 'widget settings are' + str(settings)
                        try:
                            for library in settings['RPackages']:
                                rpy.r('require('+library+')')
                        except: pass #there must not be a setting like that one in the dict, must be an orange widget.
                        tempWidget = self.addWidgetByFileName(name, int(widget.getAttribute("xPos")), int(widget.getAttribute("yPos")), widget.getAttribute("caption"), settings, saveTempDoc = False)
                        if not tempWidget:
                            print 'Widget loading disrupted.  Loading dummy widget with ' + str(settings['inputs']) + ' and ' + str(settings['outputs']) + ' into the schema'
                            tempWidget = self.addWidgetByFileName('dummy' , int(widget.getAttribute("xPos")), int(widget.getAttribute("yPos")), widget.getAttribute("caption"), settings, saveTempDoc = False, forceInSignals = settings['inputs'], forceOutSignals = settings['outputs']) # we must build a fake widget this will involve getting the inputs and outputs and joining them at the widget creation step.
                            if not tempWidget:
                                #QMessageBox.information(self, 'Orange Canvas','Unable to create instance of widget \"'+ name + '\"',  QMessageBox.Ok + QMessageBox.Default)
                                failureText += '<nobr>Unable to create instance of a widget <b>%s</b></nobr><br>' %(name)
                                loadedOk = 0
                                print widget.getAttribute("caption") + ' settings did not exist, this widget does not conform to current loading criteria.  This should be changed in the widget as soon as possible.  Please report this to the widget creator.'

                        qApp.processEvents()
                    except:
                        print 'Error occured during widget loading'
                
                #read lines
                lineList = lines.getElementsByTagName("channel")
                for line in lineList:
                    inCaption = line.getAttribute("inWidgetCaption")
                    outCaption = line.getAttribute("outWidgetCaption")
                    if freeze: enabled = 0
                    else:      enabled = int(line.getAttribute("enabled"))
                    signals = line.getAttribute("signals")
                    inWidget = self.getWidgetByCaption(inCaption)
                    outWidget = self.getWidgetByCaption(outCaption)
                    if inWidget == None or outWidget == None:
                        failureText += "<nobr>Failed to create a signal line between widgets <b>%s</b> and <b>%s</b></nobr><br>" % (outCaption, inCaption)
                        loadedOk = 0
                        continue

                    signalList = eval(signals)
                    for (outName, inName) in signalList:
                        self.addLink(outWidget, inWidget, outName, inName, enabled) # outName must be synthetic with dummy
                    #qApp.processEvents()
            finally:
                qApp.restoreOverrideCursor()
        else:
            self.schemaName = ""
            try:
                # removed the section for loading the RData, this should be a blank schema
                import re
                try:
                    from rpy_options import set_options
                    set_options(RHOME=os.environ['RPATH'])
                except: pass
                import rpy
                
                for widget in self.widgets:
                    widget.caption += 'A'
                
                zfile = zipfile.ZipFile( str(filename), "r" )
                for name in zfile.namelist():
                    file(os.path.join(self.canvasDlg.canvasSettingsDir,os.path.basename(name)), 'wb').write(zfile.read(name))
                    if re.search('tempSchema.tmp',os.path.basename(name)):
                        doc = parse(os.path.join(self.canvasDlg.canvasSettingsDir,os.path.basename(name)))
                    else:
                        pass
                        #print 'loading R session ...'
                        # insert function to load all R packages that were loaded in the previous session
                        #self.settings
                        #rpy.r('load("' + os.path.join(self.canvasDlg.canvasSettingsDir,os.path.basename(name)).replace('\\','/') +'")')
                
                schema = doc.firstChild
                widgets = schema.getElementsByTagName("widgets")[0]
                lines = schema.getElementsByTagName("channels")[0]
                settings = schema.getElementsByTagName("settings")
                settingsDict = eval(str(settings[0].getAttribute("settingsDictionary")))
                self.loadedSettingsDict = settingsDict
                  
                # read widgets
                loadedOk = 1
                for widget in widgets.getElementsByTagName("widget"):
                    name = widget.getAttribute("widgetName")
                    #print 'Name: ' + str(name) + ' (orngDoc.py)'
                    settings = cPickle.loads(settingsDict[widget.getAttribute("caption")])
                    #print 'widget settings are' + str(settings)
                    try:
                        for library in settings['RPackages']:
                            rpy.r('require('+library+')')
                    except: pass #there must not be a setting like that one in the dict, must be an orange widget.
                    tempWidget = self.addWidgetByFileName(name, int(widget.getAttribute("xPos")), int(widget.getAttribute("yPos")), widget.getAttribute("caption"), settings, saveTempDoc = False)
                    if not tempWidget:
                        self.addWidgetByFileName('Dummy', int(widget.getAttribute("xPos")), int(widget.getAttribute("yPos")), widget.getAttribute("caption"), setting, saveTempDoc = False)
                        #QMessageBox.information(self, 'Orange Canvas','Unable to create instance of widget \"'+ name + '\"',  QMessageBox.Ok + QMessageBox.Default)
                        failureText += '<nobr>Unable to create instance of a widget <b>%s</b></nobr><br>' %(name)
                        loadedOk = 0
                    qApp.processEvents()

                
                #read lines
                lineList = lines.getElementsByTagName("channel")
                for line in lineList:
                    inCaption = line.getAttribute("inWidgetCaption")
                    outCaption = line.getAttribute("outWidgetCaption")
                    if freeze: enabled = 0
                    else:      enabled = int(line.getAttribute("enabled"))
                    signals = line.getAttribute("signals")
                    inWidget = self.getWidgetByCaption(inCaption)
                    outWidget = self.getWidgetByCaption(outCaption)
                    if inWidget == None or outWidget == None:
                        failureText += "<nobr>Failed to create a signal line between widgets <b>%s</b> and <b>%s</b></nobr><br>" % (outCaption, inCaption)
                        loadedOk = 0
                        continue

                    signalList = eval(signals)
                    for (outName, inName) in signalList:
                        self.addLink(outWidget, inWidget, outName, inName, enabled)
                    qApp.processEvents()
            finally:
                qApp.restoreOverrideCursor()

        for widget in self.widgets: widget.updateTooltip()
        self.canvas.update()

        self.saveTempDoc()

        if not loadedOk:
            QMessageBox.information(self, 'Schema Loading Failed', 'The following errors occured while loading the schema: <br><br>' + failureText,  QMessageBox.Ok + QMessageBox.Default)

        # print 'process new signal'  # removed so that signals aren't processed, this isn't needed when we import a scema
        # if self.widgets:
            # self.signalManager.processNewSignals(self.widgets[0].instance)  
        #print 'finish process'
        #print 'start onload' # we do want to reload the settings of the widgets
        #print 'Widget list ' + str(self.widgets) + ' (orngDoc.py)'
        for widget in self.widgets:
            try: # important to have this or else failures in load saved settings will result in no links able to connect.
                #print 'for widget (orngDoc.oy)'
                SignalManager.loadSavedSession = True
                widget.instance.onLoadSavedSession()
                SignalManager.loadSavedSession = False
            except: print 'Loading Failed for ' + str(widget)
        SignalManager.loadSavedSession = False
        print 'done on load'

        # do we want to restore last position and size of the widget
        if self.canvasDlg.settings["saveWidgetsPosition"]:
            for widget in self.widgets:
                widget.instance.restoreWidgetStatus()
            
            
    # save document as application
    def saveDocumentAsApp(self, asTabs = 1):
        # get filename
        extension = sys.platform == "win32" and ".pyw" or ".py"
        appName = (os.path.splitext(self.schemaName)[0] or "Schema") + extension
        appPath = os.path.exists(self.canvasDlg.settings["saveApplicationDir"]) and self.canvasDlg.settings["saveApplicationDir"] or self.schemaPath
        qname = QFileDialog.getSaveFileName(self, "Save File as Application", os.path.join(appPath, appName) , "Orange Scripts (*%s)" % extension)
        if qname.isEmpty(): return
        (appPath, appName) = os.path.split(str(qname))
        appNameWithoutExt = os.path.splitext(appName)[0]
        if os.path.splitext(appName)[1].lower() not in [".py", ".pyw"]: appName = appNameWithoutExt + extension
        self.canvasDlg.settings["saveApplicationDir"] = appPath

        saveDlg = saveApplicationDlg(None)

        # add widget captions
        for instance in self.signalManager.widgets:
            widget = None
            for i in range(len(self.widgets)):
                if self.widgets[i].instance == instance: saveDlg.insertWidgetName(self.widgets[i].caption)

        if saveDlg.exec_() == QDialog.Rejected:
            return

        #format string with file content
        t = "    "  # instead of tab
        n = "\n"

        start = """#This file is automatically created by Orange Canvas and containing an Orange schema

import orngEnviron
import orngDebugging
import sys, os, cPickle, orange, orngSignalManager, OWGUI
from OWBaseWidget import *

class GUIApplication(OWBaseWidget):
    def __init__(self,parent=None):
        self.signalManager = orngSignalManager.SignalManager()
        OWBaseWidget.__init__(self, title = '%s', signalManager = self.signalManager)
        self.widgets = {}
        self.loadSettings()
        """ % (appNameWithoutExt)

        if asTabs == 1:
            start += """
        self.tabs = QTabWidget(self)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.tabs)
        self.resize(800,600)"""
        else:
            start += """
        self.setLayout(QVBoxLayout())
        self.box = OWGUI.widgetBox(self, 'Widgets')"""


        links = "# add widget signals\n"+t+t + "self.signalManager.setFreeze(1)\n" +t+t
        widgetParameters = ""

        # gui for shown widgets
        for widgetName in saveDlg.shownWidgetList:    # + saveDlg.hiddenWidgetList
            if widgetName != "[Separator]":
                widget = None
                for i in range(len(self.widgets)):
                    if self.widgets[i].caption == widgetName: widget = self.widgets[i]

                shown = widgetName in saveDlg.shownWidgetList
                widgetParameters += "self.createWidget('%s', '%s', '%s', %d, self.signalManager)\n" % (widget.widgetInfo.fileName, widget.widgetInfo.icon, widget.caption, shown) +t+t
            else:
                if not asTabs:
                    widgetParameters += "self.box.layout().addSpacing(10)\n" +t+t

        for line in self.lines:
            if not line.getEnabled(): continue
            for (outName, inName) in line.getSignals():
                links += "self.signalManager.addLink( self.widgets['" + line.outWidget.caption+ "'], self.widgets['" + line.inWidget.caption+ "'], '" + outName + "', '" + inName + "', 1)\n" +t+t

        links += "self.signalManager.setFreeze(0)\n" +t+t
        if not asTabs:
            widgetParameters += """
        box2 = OWGUI.widgetBox(self, 1)
        exitButton = OWGUI.button(box2, self, "Exit", callback = self.accept)
        self.layout().addStretch(100)"""

        if asTabs:
            guiText = "OWGUI.createTabPage(self.tabs, caption, widget)"
        else:
            guiText = "OWGUI.button(self.box, self, caption, callback = widget.reshow)"

        progress = """
        statusBar = QStatusBar(self)
        self.layout().addWidget(statusBar)
        self.caption = QLabel('', statusBar)
        self.caption.setMaximumWidth(230)
        self.progress = QProgressBar(statusBar)
        self.progress.setMaximumWidth(100)
        self.status = QLabel("", statusBar)
        self.status.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        statusBar.addWidget(self.progress)
        statusBar.addWidget(self.caption)
        statusBar.addWidget(self.status)"""

        handlerFuncts = """
    def createWidget(self, fname, iconName, caption, shown, signalManager):
        widgetSettings = cPickle.loads(self.strSettings[caption])
        m = __import__(fname)
        widget = m.__dict__[fname].__new__(m.__dict__[fname], _settingsFromSchema = widgetSettings)
        widget.__init__(signalManager=signalManager)
        widget.setEventHandler(self.eventHandler)
        widget.setProgressBarHandler(self.progressHandler)
        widget.setWidgetIcon(iconName)
        widget.setWindowTitle(caption)
        self.signalManager.addWidget(widget)
        self.widgets[caption] = widget
        if shown: %s
        for dlg in getattr(widget, "wdChildDialogs", []):
            dlg.setEventHandler(self.eventHandler)
            dlg.setProgressBarHandler(self.progressHandler)

    def eventHandler(self, text, eventVerbosity = 1):
        if orngDebugging.orngVerbosity >= eventVerbosity:
            self.status.setText(text)

    def progressHandler(self, widget, val):
        if val < 0:
            self.caption.setText("<nobr>Processing: <b>" + str(widget.captionTitle) + "</b></nobr>")
            self.progress.setValue(0)
        elif val >100:
            self.caption.setText("")
            self.progress.reset()
        else:
            self.progress.setValue(val)
            self.update()

    def loadSettings(self):
        try:
            file = open("%s", "r")
            self.strSettings = cPickle.load(file)
            file.close()

        except:
            print "unable to load settings"
            pass

    def closeEvent(self, ev):
        OWBaseWidget.closeEvent(self, ev)
        if orngDebugging.orngDebuggingEnabled: return
        strSettings = {}
        for (name, widget) in self.widgets.items():
            widget.synchronizeContexts()
            strSettings[name] = widget.saveSettingsStr()
            widget.close()
        file = open("%s", "w")
        cPickle.dump(strSettings, file)
        file.close()

if __name__ == "__main__":
    application = QApplication(sys.argv)
    ow = GUIApplication()
    ow.show()
    # comment the next line if in debugging mode and are interested only in output text in 'signalManagerOutput.txt' file
    application.exec_()
        """ % (guiText, appNameWithoutExt + ".sav", appNameWithoutExt + ".sav")


        #save app
        f = open(os.path.join(appPath, appName), "wt")
        f.write(start + n+n+t+t+ widgetParameters + n+t+t + progress + n+n+t+t + links + n + handlerFuncts)
        f.close()

        # save widget settings
        list = {}
        for widget in self.widgets:
            list[widget.caption] = widget.instance.saveSettingsStr()

        f = open(os.path.join(appPath, appNameWithoutExt) + ".sav", "wt")
        cPickle.dump(list, f)
        f.close
        
        
    def dumpWidgetVariables(self):
        for widget in self.widgets:
            self.canvasDlg.output.write("<hr><b>%s</b><br>" % (widget.caption))
            v = vars(widget.instance).keys()
            v.sort()
            for val in v:
                self.canvasDlg.output.write("%s = %s" % (val, getattr(widget.instance, val)))

    def keyReleaseEvent(self, e):
        self.ctrlPressed = int(e.modifiers()) & Qt.ControlModifier != 0
        e.ignore()

    def keyPressEvent(self, e):
        self.ctrlPressed = int(e.modifiers()) & Qt.ControlModifier != 0
        if e.key() > 127:
            #e.ignore()
            QWidget.keyPressEvent(self, e)
            return

        # the list could include (e.ShiftButton, "Shift") if the shift key didn't have the special meaning
        pressed = "-".join(filter(None, [int(e.modifiers()) & x and y for x, y in [(Qt.ControlModifier, "Ctrl"), (Qt.AltModifier, "Alt")]]) + [chr(e.key())])
        widgetToAdd = self.canvasDlg.widgetShortcuts.get(pressed)
        if widgetToAdd:
            self.addWidget(widgetToAdd)
            if e.modifiers() & Qt.ShiftModifier and len(self.widgets) > 1:
                self.addLine(self.widgets[-2], self.widgets[-1])
        else:
            #e.ignore()
            QWidget.keyPressEvent(self, e)

#    def resizeEvent(self, ev):
#        QWidget.resizeEvent(self, ev)
#        self.canvas.addRect(self.canvasView.size().width()-1, self.canvasView.size().height()-1, 1, 1)