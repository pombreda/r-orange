from PyQt4.QtCore import *
from PyQt4.QtGui import *
import redRObjects, redRLog
import redRi18n, gc
# def _(a):
    # return a
_ = redRi18n.Coreget_()


_linkPairs = []  ## should be a list of tuples, (outsocket, insocket, enabled, none)

"""Return a link pair or None"""
def getLinkPairBySignal(outSig, inSig):
    for o, i, e, n in _linkPairs:
        if o == outSig and i == inSig:
            return (o, i, e, n)
    return None
            
def getLinksByWidgetInstance(outInst, inInst):
    """Returns a list of tupes for each link pair that matches the out and in instances."""
    r = []
    for o, i, e, n in _linkPairs:
        if o.parent == outInst and i.parent == inInst:
            r.append((o,i,e,n))
    return r

def getInputConnectionsFromOutput(signal):
    r = []
    for o, i, e, n in _linkPairs:
        if o == signal:
            r.append(i)
    return r

def getLinkPairsByInput(signal, inWidgetInstance):
    r = []
    #print 'Checking for links with signal: %s, owner %s' % (unicode(signal), unicode(signalOwner.instance()))
    for o, i, e, n in _linkPairs:
        if i.wid == signal and i.parent == inWidgetInstance:
            r.append(o)
    return r
    
def getInputInstances(inWidgetInstance):
    r = []
    for o, i, e, n in _linkPairs:
        if i.parent == inWidgetInstance and (o.parent not in r):
            r.append(o.parent)
    return r
    
class OutputSocket():
    def __init__(self, wid, name, signalClass, parent, value = None):
        self.wid= wid
        self.name = name
        self.signalClass = signalClass
        self.value = value
        self.parent = parent
        self.connections = {}
    def setValue(self, value):
        try: 
            if self.value:
                oldData = self.value.getData() # delete the value of the data socket so that it doesn't get lost, this is the last reference to it.
                del oldData
                gc.collect() # clears the old data out of memeory.  This is diminutive for r signal classes, but very important for other signal classes
        except Exception as inst:
            print inst
            print type(self.value)
        self.value = value
    def getValue(self):
        return self.value
    def getSettings(self):
        """Returns a pickleable data structure"""
        pass
        
        
    def setSettings(self, d):
        """Accepts an unpickled data structure for loading."""
        pass

class InputSocket():
    def __init__(self, wid, name, signalClass, handler, parent, multiple = False):
        self.wid = wid
        self.name = name
        self.signalClass = signalClass
        self.handler = handler
        self.multiple = multiple
        self.parent = parent
        
        

class OutputHandler:
    def __init__(self, parent):                         ## set up the outputHandler, this will take care of sending signals to 
        self.outputs = {} # a list of output signals
        self.parent = parent # the parent that owns the OutputHandler
        
    def getAllOutputs(self):
        """Returns a dict of all output sockets in this handler."""
        return self.outputs
    
    def addOutput(self, wid, name, signalClass):
        self.outputs[wid] = OutputSocket(wid, name, signalClass, self.parent)   # set up an 'empty' signal
    
    def clearAll(self):
        """Clears all output signals in this handler, called when a widget is being deleted."""
        for outputSignal in self.outputs.values():
            val = outputSignal.getValue()
            if val == None: continue
            val.deleteSignal() # calls the distructor function for the signal
        self.outputs = {}
    def connectSignal(self, signal, wid, enabled = 1, process = True):
        try:
            outSig = self.outputs[wid]
            #print '!@#$ adding signal %s %s' % (unicode(outSig), unicode(signal))
            _linkPairs.append((outSig, signal, enabled, 1))
            # now send data through
            redRObjects.addLine(self.parent, signal.parent) # add a line between the two widget on the canvas
            if process:
                #print _('processing signal')
                self._processSingle(outSig, signal)
            #print 'returning true'
            return True
        except:
            redRLog.log(redRLog.REDRCORE, redRLog.ERROR, redRLog.formatException())
            redRLog.log(redRLog.REDRCORE, redRLog.ERROR, _('redRSignalManager connectSignal: error in connecting signal'))
            return False
        #redRLog.logConnection(self.parent.widgetInfo.fileName, signal['parent'].widgetInfo.fileName)
        #redRObjects.updateLines()
    def outputIDs(self):
        """Returns a list of output ids"""
        return self.outputs.keys()
    def outputNames(self):
        """Returns a dict of ouptut names"""
        #return [o.name for o in self.outputs.values()]
        out = {}
        for key, value in self.outputs.items():
            out[key] = value.name
        return out
    def outputValues(self):
        """Return a dict of id-signalValues pairs."""
        out = {}
        for o in self.outputs:
            out[o.wid] = o.getValue()
        return out
        
    def removeSignal(self, signal, wid):
        """Remove the connection between the inSocket and outSocket (specified by id)"""
        redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, _('Removing signal %s, %s') % (unicode(signal), unicode(wid)))
        ## send None through the signal to the handler before we disconnect it.
        
        l = getLinkPairBySignal(self.outputs[wid], signal)
        if l:
            try:
                if signal.multiple:
                    signal.handler(
                        None,
                        self.parent.widgetID
                        )
                else:
                    signal.handler(
                        #self.outputs[signalName]['value']
                        None
                        )
            except:
                redRLog.log(redRLog.REDRCORE, redRLog.ERROR, redRLog.formatException())
            finally:
                ## remove the signal from the outputs
                rm = [l for l in _linkPairs if l[0] == self.outputs[wid] and l[1] == signal]
                for s in rm:
                    #print 'Links before remove', _linkPairs
                    _linkPairs.remove(s)
                    #print 'Links after remove', _linkPairs
                try:
                    signal.parent.outputs.propogateNone()
                except:
                    redRLog.log(redRLog.REDRCORE, redRLog.ERROR, redRLog.formatException())
                    pass
    def setOutputData(self, signalName, value):
        """Called by widgetSignals to set the output data of a socket."""
        self.outputs[signalName].setValue(value)
    
    def getSignal(self, wid):
        return self.outputs.get(wid, None)
    def _processSingle(self, outsig, insig, enabled = 1):
        """Process the data in the outsig socket through the handler specified by the insig socket."""
        #print 'Processing signal %s, %s' % (outsig.name, insig.name)
        try:
            #print signal
            if not enabled: return 0
            handler = insig.handler
            multiple = insig.multiple
            if outsig.getValue() == None: # if there is no data then it doesn't matter what the signal class is, becase none will be sent anyway
                self._handleSignal(outsig.getValue(), handler, multiple, insig.parent) 
            elif (insig.signalClass == 'All') or ('All' in insig.signalClass) or (outsig.signalClass in insig.signalClass):
                #print '\n\n\nprocessing signal %s using handler: %s with multiple: %s\n\n\n\n' % (signal['value'], handler, multiple)
                self._handleSignal(outsig.getValue(), handler, multiple, insig.parent) 
            else:
                sentSignal = False
                for sig in insig.signalClass:
                    try:
                        if sig in outsig.signalClass.convertToList:
                            newVal = outsig.getValue().convertToClass(sig)
                            self._handleSignal(newVal, handler, multiple, insig.parent)
                            sentSignal = True
                            break
                        elif outsig.signalClass in sig.convertFromList:
                            tempSignal = sig(self.parent, data = '', checkVal = False)                       ## make a temp holder to handle the processing.
                            newVal = tempSignal.convertFromClass(outsig.getValue())
                            self._handleSignal(newVal, handler, multiple, insig.parent)
                            sentSignal = True
                            break
                    except Exception as inst:
                        redRLog.log(redRLog.REDRCORE, redRLog.ERROR, unicode(inst))
                        redRLog.log(redRLog.REDRCORE, redRLog.ERROR,redRLog.formatException())
                if sentSignal == False:
                    ## we made it this far and the signal is still not sent.  The user must have allowed this to get this far so we send the signal anyway.
                    self._handleSignal(outsig.getValue(), handler, multiple, insig.parent)
        except:
            redRLog.log(redRLog.REDRCORE, redRLog.ERROR,redRLog.formatException())
            
    def processData(self, wid):
        """Begins sending of data to downstream widgets connected to the output socket specified by wid"""
        # collect the signal ID
        outSig = self.getSignal(wid)
        
        # collect the connections
        connections = getInputConnectionsFromOutput(outSig)
        
        ## handle conversions and send data.
        for inSig in connections:
            self._processSingle(outSig, inSig)

    def _handleNone(self, parentWidget, wid, none):
        parentWidget.inputs.markNone(wid, none)
        links = self.getWidgetConnections(parentWidget)
        lines = redRObjects.getLinesByInstanceIDs(self.parent.widgetID, parentWidget.widgetID)
        for line in lines:
            #print _('The line is '), line, _('the signal is '), none
            for l in links:
                if parentWidget.inputs.getSignal(l['signal']['sid'])['none']:
                    line.setNoData(True)
                    redRObjects.activeCanvas().update()
                    return
                else:
                    line.setNoData(False)
                    redRObjects.activeCanvas().update()
    def _handleSignal(self, value, handler, multiple, parentWidget):
        #print 'handling signal'
        try:
            if multiple:
                handler(value, self.parent.widgetID)
            else:   
                handler(value)
            parentWidget.status.setText(_('New Data Received'))
            parentWidget.removeWarning(id = 'signalHandlerWarning')
        except:
            
            error = _("Error occured in processing signal in this widget.\nPlease check the widgets.\n")
            parentWidget.setWarning(id = 'signalHandlerWarning', text = unicode(error))
            #print error
            redRLog.log(redRLog.REDRCORE, redRLog.ERROR,redRLog.formatException())
            parentWidget.status.setText(_('Error in processing signal'))
        #print 'signal success'
    def hasOutputName(self, name):
        return name in self.outputs.keys()
        
    def getSignalByName(self, name):
        for signal in self.outputs:
            if fullSignal.name == name:
                return signal
            
    ########  Loading and Saving ##############
    
    def returnOutputs(self):
        ## move through the outputs and return a list of outputs and connections.  these connections should be reconnected on reloading of the widget, ideally we will only put atomics into this outputHandler
        data = {'version':1.90}
        for (key, outSig) in self.outputs.items():
            #print 'isolation 1'
            data[key] = {'name':outSig.name, 'signalClass':unicode(outSig.signalClass), 'connections':[]}
            if outSig.value != None:
                data[key]['value'] = outSig.value.saveSettings()
            else:
                data[key]['value'] = None
            for inSig in getInputConnectionsFromOutput(outSig):
                data[key]['connections'].append({'wid':inSig.wid, 'parentID':inSig.parent.widgetID, 'enabled':getLinkPairBySignal(outSig, inSig)[2]})
            #for (vKey, vValue) in value['connections'].items():
                #data[key]['connections'][vKey] = {'wid':vValue['signal']['sid'], 'parentID':vValue['signal']['parent'].widgetID, 'enabled':vValue['enabled']} ## now we know the widgetId and the signalID (sid) used for connecting widgets in the future.
                
            
        return data
        
    def setOutputs(self, data, tmp = False):
        """Accepts a dict of key values and an optional arg tmp indicating if this is a template.
        The structure of the data dict is
        {
        version: version number
        id {
        
        name = outputSocket.name,
        signalClass = unicode(outputSocket.signalClass,
        value = None or outputSocket.signalCalss.saveSettings()
        }...
        }
        """
        
        if data.get('version', 1.85) > 1.85:
            #redRLog.log(redRLog.REDRCPRE, redRLog.DEBUG, "Adding Outputs using prior 1.85 settings.")
            for (key, value) in data.items():
                if key not in self.outputs.keys() or 'connections' not in value:
                    #print _('Signal does not exist')
                    continue
                ## find the signal from the widget and connect it
                for vValue in value['connections']:
                    ### find the widget
                    if not tmp:
                        widget = redRObjects.getWidgetInstanceByID(vValue['parentID'])
                    elif tmp:
                        widget = redRObjects.getWidgetInstanceByTempID(vValue['parentID'])
                    redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, 'Input widget is %s' % widget)
                    if not widget:
                        redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, 'Failed to find input widget %s' % vValue['parentID'])
                        return
                    inputSignal = widget.inputs.getSignal(vValue['wid'])
                    #redRLog.log(redRLog.REDRCPRE, redRLog.DEBUG, "Adding canvas line to using 1.85 settings.")
                    self.connectSignal(inputSignal, key, vValue['enabled'], process = False)  # connect the signal but don't send data through it.
                    if tmp:
                        self.propogateNone(ask = False)
        elif data.get('version', 1.85) <= 1.85: # 1.85 is the last supported version to not have version numbers in the output data containers.
            redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, "Adding Outputs using pre 1.85 settings.")
            for (key, value) in data.items():
                if key not in self.outputs.keys() or 'connections' not in value: continue
                for (vKey, vValue) in value['connections'].items():
                    if not tmp:
                        widget = redRObjects.getWidgetInstanceByID(vValue['parentID'])
                    elif tmp:
                        widget = redRObjects.getWidgetInstanceByTempID(vValue['parentID'])
                    redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, 'Input widget is %s' % widget)
                    if not widget:
                        redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, 'Failed to find input widget %s' % vValue['parentID'])
                        return
                    
                    if 'wid' in vValue.keys():
                        inputSignal = widget.inputs.getSignal(vValue['wid'])
                    elif 'id' in vValue.keys():
                        inputSignal = widget.inputs.getSignal(vValue['id'])
                        redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, "Adding canvas line to using < 1.85 settings.")
                    self.connectSignal(inputSignal, key, vValue['enabled'], process = False)  # connect the signal but don't send data through it.
                    if tmp:
                        self.propogateNone(ask = False)
    #def linkingWidgets(self):
        #widgets = []
        #for (i, s) in self.outputs.items():
            #for (wid, ls) in s['connections'].items():
                #if ls['signal']['parent'] not in widgets:
                    #widgets.append(ls['signal']['parent'])
        #return widgets
        
    def propogateNone(self, ask = True):    
        ## send None through all of my output channels
        if self.parent.signalLocked(): return
        try:
            redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, _('Propagating None through signal'))
            for wid in self.outputIDs():
                self.parent.send(wid, None)
            
            ## identify all of the downstream widgets and send none through them, then propogateNone in their inputs
            dWidgets = []
            for c in _linkPairs:
                if c[0].parent == self.parent:
                    dWidgets.append(c[1].parent)
            for w in dWidgets:
                w.outputs.propogateNone(ask = False)    
        except Exception as inst:
            redRLog.log(redRLog.REDRCORE, redRLog.WARNING, 'Failed to remove a signal')
            redRLog.log(redRLog.REDRCORE, redRLog.WARNING, redRLog.formatException())
            
    
class InputHandler:
    def __init__(self, parent):
        self.inputs = {}
        self.links = {}
        self.parent = parent # the parent widget that owns the InputHandler
    def getAllInputs(self):
        return self.inputs
    def addInput(self, wid, name, signalClass, handler, multiple = False):
        if type(signalClass) != list:
            signalClass = [signalClass]
        self.inputs[wid] = InputSocket(wid, name, signalClass, handler, parent = self.parent, multiple = multiple)
    def signalIDs(self):
        return self.inputs.keys()
    def getSignal(self, wid):
        return self.inputs.get(wid, None)
    def matchConnections(self, outputHandler):
        ## determine if there are any valid matches between the signal handlers
        for outputKey in outputHandler.outputs.keys():
            for inputKey in self.inputs.keys():
                OSignalClass = outputHandler.outputs[outputKey].signalClass
                for ISignalClass in self.inputs[inputKey].signalClass:
                    if OSignalClass == 'All' or ISignalClass == 'All':
                        return True
                    elif OSignalClass == ISignalClass:
                        return True
                    elif 'convertToList' in dir(OSignalClass) and ISignalClass in OSignalClass.convertToList:
                        return True
                    elif 'convertFromList' in dir(ISignalClass) and OSignalClass in ISignalClass.convertFromList:
                        return True
                    # else:
                        # print OSignalClass
                        # print ISignalClass
                        
                        # print unicode(OSignalClass.convertToList)
                        # print unicode(ISignalClass.convertFromList)
        return False
        
    def getPossibleConnections(self, outputHandler):
        ## determine if there are any valid matches between the signal handlers
        connections = []
        for outputKey in outputHandler.outputs.keys():
            for inputKey in self.inputs.keys():
                OSignalClass = outputHandler.outputs[outputKey].signalClass
                for ISignalClass in self.inputs[inputKey].signalClass:
                    if OSignalClass == 'All' or ISignalClass == 'All':
                        connections.append((outputKey, inputKey))
                        break
                    elif OSignalClass == ISignalClass:
                        connections.append((outputKey, inputKey))
                        break
                    elif 'convertToList' in dir(OSignalClass) and ISignalClass in OSignalClass.convertToList:
                        connections.append((outputKey, inputKey))
                        break
                    elif 'convertFromList' in dir(ISignalClass) and OSignalClass in ISignalClass.convertFromList:
                        connections.append((outputKey, inputKey))
                        break
        return connections
    def doesSignalMatch(self, wid, signalClass):
        if signalClass == 'All': return True
        elif 'All' in self.getSignal(wid).signalClass: return True
        elif signalClass in self.getSignal(wid).signalClass: return True
        for s in self.getSignal(wid).signalClass:
            if s in signalClass.convertToList:
                return True
            else:
                if signalClass in s.convertFromList:
                    return True
                    
        return False
    def addLink(self, sid, signal):
        if sid not in self.links.keys():
            self.links[sid] = []
        if self.getSignal(sid).multiple:
            self.links[sid].append(signal)
        else:
            for link in self.links[sid]:
                link['parent'].removeSignal(self.getSignal(sid), link['sid'])
            self.links[sid].append(signal)
    def removeLink(self, sid, signal):
        if sid not in self.links.keys(): return
        self.links[sid].remove(signal)
        
    
    def getLinks(self, sid):
        if sid not in self.links.keys():
            self.links[sid] = []
        return self.links[sid]
    ######### Loading and Saving ##############
    def returnInputs(self):
        return None  ## no real reason to return any of this becasue the outputHandler does all the signal work
