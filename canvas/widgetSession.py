"""Widget Session

Widget session handles loading and saving of data from a previous session.  This holds functions to return pickled or pickleable objects to the core saving routines.
"""

import os, cPickle, numpy, pprint, re, sys, redRLog
import redREnviron
import signals
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import redRGUI 
import signals 
 

class widgetSession():
    def __init__(self,dontSaveList):
        #collect the sent items
        
        #dont save these variables
        self.requiredAtts = ['notes', 'ROutput']
        self.loaded = False
        self.dontSaveList = dontSaveList
        self.defaultGlobalSettingsList = ['windowState']
        self.dontSaveList.extend(self.defaultGlobalSettingsList)
        self.dontSaveList.extend(['outputs','inputs', 'dontSaveList','redRGUIObjects','defaultGlobalSettingsList','globalSettingsList', 'loaded'])
        # self.sqlite = SQLiteHandler()
        self.locked = False
        
    def toggleLocked(self):
        self.locked = not self.locked
        
    def signalLocked(self):
        return self.locked


    def getSettings(self):  
        """collects settings for the save function, these will be included in the output file.  Called in orngDoc during save."""
        redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, 'moving to save'+unicode(self.captionTitle))
        import re
        settings = {}
        if self.saveSettingsList:  ## if there is a saveSettingsList then we just append the required elements to it.
            allAtts = self.saveSettingsList + self.requiredAtts
        else:
            allAtts = self.__dict__
        self.progressBarInit()
        i = 0
        for att in allAtts:
            try:
                if att in self.dontSaveList or re.search('^_', att): continue
                i += 1
                self.progressBarAdvance(i)
                var = getattr(self, att)
                settings[att] = self.returnSettings(var)
            except:
                redRLog.log(redRLog.REDRCORE, redRLog.ERROR,redRLog.formatException())
        #print 'saving custom settings'
        settings['_customSettings'] = self.saveCustomSettings()
        #print 'processing sent items'
        tempSentItems = self.processSentItems()
        #print 'appending sent items'
        settings['sentItems'] = {'sentItemsList':tempSentItems}
        self.progressBarFinished()
        return settings
        
    def saveCustomSettings(self): 
        """Dummy function that should be overwritten in child classes if they want the function."""
        pass

    def isPickleable(self,d):  # check to see if the object can be included in the pickle file
        # try:
            # cPickle.dumps(d)
            # return True
        # except:
            # return False
            
        
        import re
        if re.search('PyQt4|OWGUIEx|OWToolbars',unicode(type(d))) or d.__class__.__name__ in redRGUI.qtWidgets:
            return False
        elif type(d) in [list, dict, tuple]:
            if type(d) in [list, tuple]:
                for i in d:
                    if self.isPickleable(i) == False:
                        return False
                return True
            elif type(d) in [dict]:
                for k in d.keys():
                    if self.isPickleable(d[k]) == False:
                        #ok = False
                        return False
                return True
        elif type(d) in [type(None), str,unicode, int, float, bool, numpy.float64]:  # list of allowed save types, may epand in the future considerably
            return True
        elif isinstance(d, signals.BaseRedRVariable):
            return True
        else:
            redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, 'Type ' + unicode(d) + ' is not supported at the moment..')  # notify the developer that the class that they are using is not saveable
            return False
        
            
    def returnSettings(self,var, checkIfPickleable=True): 
        """Parses through objects returning if they can be saved or not and collecting their settings."""
        
        settings = {}
        from redRGUI import widgetState
        from signals import BaseRedRVariable
        if isinstance(var, widgetState):
            settings['redRGUIObject'] = {}
            settings['redRGUIObject']['widgetSettings'] = var.getSettings()
            settings['redRGUIObject']['defaultSettings'] = var.getDefaultState()
        elif isinstance(var, BaseRedRVariable) or issubclass(var.__class__,BaseRedRVariable) :
            settings['signalsObject'] = var.saveSettings()
        elif not checkIfPickleable: 
            settings['pythonObject'] =  var
        elif self.isPickleable(var):
            settings['pythonObject'] =  var
        elif type(var) in [list]:
           settings['list'] = []
           for i in var:
               settings['list'].append(self.returnSettings(i))
        elif type(var) is dict:
           settings['dict'] = {}
           for k,v in var.iteritems():
               settings['dict'][k] = self.returnSettings(v)
        else:
            settings = None
        return settings
    def processSentItems(self):
        ## make a list of the signal keys and the values of all of the sent items, shouldn't be hard
        items = []
        for (key, item) in self.outputs.getAllOutputs().items():
            if item.value != None:
                items.append((key, item.value.saveSettings()))

        return items
        
        
    def setSettings(self,settings, globalSettings = False):
        redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, 'Loading settings')
        for k,v in settings.iteritems():
            #print 'loading %s in widget %s' % (k, self.captionTitle)
            try:
                #redRLog.log(redRLog.REDRCORE, redRLog.ERROR, 'Loading %s' % k)
                if k in ['inputs', 'outputs']: continue
                
                elif v == None:
                    continue
                elif 'pythonObject' in v.keys():
                    #print '|#| Setting pythonObject %s to %s' % (k,unicode(v['pythonObject']))
                    if k == 'Rvariables':
                        self.Rvariables.update(v['pythonObject'])
                    else:
                        self.__setattr__(k, v['pythonObject'])
                elif 'signalsObject' in v.keys():
                    #print '|#| Setting signalsObject'
                    varClass = self.setSignalClass(v['signalsObject'])
                    self.__setattr__(k, varClass)
                elif 'sentItemsList' in v.keys():
                    #print '|#| settingItemsList'
                    # print v['sentItemsList']
                    #self.setSentItemsList(v['sentItemsList'])        
                    for (sentItemName, sentItemDict) in v['sentItemsList']:
                        #print '|#| setting sent items %s to %s' % (sentItemName, unicode(sentItemDict))
                        #for kk,vv in sentItemDict.items():
                        var = self.setSignalClass(sentItemDict)
                        ## add compatibility layer for the case that the sent item name is not longer in existance or has changed
                        if sentItemName in self.outputs.outputIDs():
                            self.send(sentItemName, var)
                        else:
                            signalItemNames = [name for (key, name) in self.outputs.outputNames().items()]
                            if sentItemName in signalItemNames:
                                signalID = self.outputs.getSignalByName(sentItemName)
                                self.send(signalID, var)
                            else:
                                #print 'Error in matching item name'
                                tempDialog = redRGUI.base.dialog(None)
                                redRGUI.base.widgetLabel(tempDialog, 'Error occured in matching the loaded signal (Name:%s, Value:%s) to the appropriate signal name.\nPlease select the signal that matches the desired output,\n or press cancel to abandon the signal.' % (sentItemName, unicode(var)))
                                
                                #print self.outputs.outputSignals
                                itemListBox = redRGUI.base.listBox(tempDialog, items = signalItemNames)
                                redRGUI.base.button(tempDialog, label = 'Done', callback = tempDialog.accept)
                                redRGUI.base.button(tempDialog, label = 'Cancel', callback = tempDialog.reject)
                                res = tempDialog.exec_()
                                if res != QDialog.rejected:
                                    signalName = unicode(itemListBox.selectedItems()[0])
                                    signalID = self.outputs.getSignalByName(signalName)
                                    self.send(signalID, var)
                                    print 'Sending complete from load'
    #############################################
                elif not hasattr(self,k) or (getattr(self, k) == None):
                    continue
                elif 'redRGUIObject' in v.keys():
                    #print getattr(self, k)
                    if v.get('redRGUIObject').get('widgetSettings', None):
                        #print v['redRGUIObject']['widgetSettings']
                        getattr(self, k).loadSettings(v['redRGUIObject']['widgetSettings'])
                        getattr(self, k).setDefaultState(v['redRGUIObject']['defaultSettings'])
                    else:
                        print v.get('redRGUIObject').keys(), "widgetSettings not in keys but should have been, please check the keys."
                        try:
                            getattr(self, k).loadSettings(v['redRGUIObject'])
                            getattr(self, k).setDefaultState(v['redRGUIObject'])
                            redRLog.log(redRLog.REDRCORE, redRLog.INFO, 'Loading using 180 setting was successful.')
                        except:
                            #print 'Exception occured during loading of settings.  These settings may not be the same as when the widget was closed.'
                            redRLog.log(redRLog.REDRCORE, redRLog.ERROR,redRLog.formatException())
                elif 'dict' in v.keys():
                    var = getattr(self, k)
                    #print 'dict',len(var),len(v['dict'])
                    if len(var) != len(v['dict']): continue
                    self.recursiveSetSetting(var,v['dict'])
                elif 'list' in v.keys():
                    var = getattr(self, k)
                    # print 'list',len(var),len(v['list'])
                    if len(var) != len(v['list']): continue
                    self.recursiveSetSetting(var,v['list'])
            except:
                redRLog.log(redRLog.REDRCORE, redRLog.ERROR, 'Exception occured during loading. The Error will be ignored.')
                redRLog.log(redRLog.REDRCORE, redRLog.DEBUG, redRLog.formatException())
        
        
    def setSignalClass(self, d):
        try: # try to reload the output class from the signals
            import imp
            ## find the libraries directory
            fp, pathname, description = imp.find_module('libraries', [redREnviron.directoryNames['redRDir']])
            #print 'loading module'
            varc = imp.load_module('libraries', fp, pathname, description)
            #print varc
            for mod in d['class'].split('.')[1:]:
                #print varc
                varc = getattr(varc, mod)
            var = varc(widget = self, checkVal = False, **d) 
            var.loadSettings(d)
            
        except: # if it doesn't exist we need to set the class something so we look to the outputs. 
            ## kick over to compatibility layer to add the settings. for 175 attributes
            redRLog.log(redRLog.REDRCORE, redRLog.ERROR, redRLog.formatException())
            try:
                for (key, val) in d.items():
                    ## find the libraries directory
                    fp, pathname, description = imp.find_module('libraries', [redREnviron.directoryNames['redRDir']])
                    #print 'loading module'
                    varc = imp.load_module('libraries', fp, pathname, description)
                    #print varc
                    for mod in val['class'].split('.')[1:]:
                        #print varc
                        varc = getattr(varc, mod)
                    var = varc(widget = self, data = val['data']) 
                    var.loadSettings(val)
                    if fp:
                        fp.close()
            except:
                #print 'something is really wrong we need to set some kind of data so let\'s set it to the signals.RVariable'
                redRLog.log(redRLog.REDRCORE, redRLog.ERROR,redRLog.formatException())
                
                try:
                    var = signals.BaseRedRVariable(widget = self, data = d['data']['data'], checkVal = False)
                except: ## fatal exception, there is no data in the data slot (the signal must not have data) we can't do anything so we except...
                    redRLog.log(redRLog.REDRCORE, redRLog.ERROR,redRLog.formatException())
                    #print 'Fatal exception in loading.  Can\'t assign the signal value'
                    var = None
        finally:
            if fp:
                fp.close()
        return var
            
    def recursiveSetSetting(self,var,d):
        # print 'recursiveSetSetting'
        
        if type(var) in [list,tuple]:
            for k in xrange(len(d)):
                if type(d[k]) is dict and 'redRGUIObject' in d[k].keys():
                    var[k].loadSettings(d[k]['redRGUIObject'])
                    var[k].setDefaultState(d[k]['redRGUIObject'])
                else:
                    self.recursiveSetSetting(var[k],d[k])
        elif type(var) is dict:
            for k,v in d.iteritems():
                if type(v) is dict and 'redRGUIObject' in v.keys():
                    var[k].loadSettings(v['redRGUIObject'])
                    var[k].setDefaultState(v['redRGUIObject'])
                else:
                    self.recursiveSetSetting(var[k],d[k])
        
    def loadCustomSettings(self,settings=None):
        pass

#############widget specific settings#####################
        ##########set global settings#############
    def loadGlobalSettings(self):
        file = self.getGlobalSettingsFile()
        if not os.path.exists(file): return
        try:
            file = open(file, "r")
            settings = cPickle.load(file)
            self.setSettings(settings, globalSettings = True)
        except:
            redRLog.log(redRLog.REDRCORE, redRLog.ERROR, redRLog.formatException())
            pass
        
    
    def getGlobalSettingsFile(self):
        # print 'getSettingsFile in owbasewidget'
        file = os.path.join(redREnviron.directoryNames['widgetSettingsDir'], self._widgetInfo.fileName + ".ini")
        return file
        # if os.path.exists(file): return file
        # else: return False

    
    # save global settings
    def saveGlobalSettings(self):
        settings = {}
        
        if hasattr(self, "globalSettingsList"):
            self.globalSettingsList.extend(self.defaultGlobalSettingsList)
        else:
            self.globalSettingsList =  self.defaultGlobalSettingsList
        print self.globalSettingsList
        for name in self.globalSettingsList:
            settings[name] = self.returnSettings(getattr(self,name),checkIfPickleable=False)
        if settings:
            file = self.getGlobalSettingsFile()
            f = open(file, "w")
            cPickle.dump(settings, f)

