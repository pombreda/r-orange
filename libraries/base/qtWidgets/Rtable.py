"""
RTable visualizes tabular R data in a spreadsheet like table. Columns are sortable and filterable. The qtWidget uses the QT model/view architecture, so only data visible on the screen is loaded into memory, making this widget very efficient when viewing large data sets.
"""
from redRGUI import widgetState
from RSession import Rcommand
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from libraries.base.qtWidgets.groupBox import groupBox
import redRi18n
_ = redRi18n.get_(package = 'base')
class Rtable(widgetState,QTableView):
    """
    Rtable class handles all the QT GUI functionality like creating header with menus, 
    and row/column/cell selection.
    """
    def __init__(self,widget, label=None, displayLabel=True, Rdata=None, editable=False, rows=None, columns=None,
    sortable=False, selectionMode = -1, addToLayout = 1,callback=None,**kwargs):
        kwargs.setdefault('includeInReports', True)
        kwargs.setdefault('sizePolicy', QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        widgetState.__init__(self,widget, widget.label,**kwargs)
        if displayLabel:
            mainBox = groupBox(self.controlArea,label=label, orientation='vertical')
        else:
            mainBox = widgetBox(self.controlArea,orientation='vertical')
        
        QTableView.__init__(self,mainBox)
        mainBox.layout().addWidget(self)

        
        self.R = Rcommand
        self.sortIndex = None
        self.oldSortingIndex = None
        self.Rdata = None
        self.parent = widget
        self.tm=None
        self.editable=editable
        
        
        self.setAlternatingRowColors(True)
        
        if widget and addToLayout and widget.layout():
            widget.layout().addWidget(self)
        elif widget and addToLayout:
            try:
                widget.addWidget(self)
            except: # there seems to be no way to add this widget
                pass
        if selectionMode != -1:
            self.setSelectionMode(selectionMode)
                
        if Rdata:
            self.setRTable(Rdata)
        if sortable:
            self.setSortingEnabled(True)
            self.connect(self.horizontalHeader(), SIGNAL("sectionClicked(int)"), self.sort)
        # if editable:
            # self.horizontalHeader().hide()
            # self.verticalHeader().hide()
        if callback:
            QObject.connect(self, SIGNAL('cellClicked(int, int)'), callback)

        

    def setRTable(self,Rdata, setRowHeaders = 1, setColHeaders = 1):
        """
        Set the R data set to visual. The GUI will be updated with the new data.
        """
        #print Rdata
        self.Rdata = Rdata
        # if self.tm:
            # self.tm.initData(Rdata)
        # else:
        self.tm = MyTableModel(Rdata,self,editable=self.editable)
        self.setModel(self.tm)

    def columnCount(self):
        """Return the number of column."""
        if self.tm:
            return self.tm.columnCount(self)
        else:
            return 0
    
    def addRows(self,count,headers=None):
        """Insert a new blank row"""
        self.tm.insertRows(self.tm.rowCount(self),count,headers=headers)
    def addColumns(self,count,headers=None):
        """Insert a new blank column"""
        self.tm.insertColumns(self.tm.columnCount(self),count,headers)
        
    def sort(self, index):
        """Sort column by given index. If column is already sorted, reverse the order."""
        if index == self.oldSortingIndex:
            order = self.oldSortingOrder == Qt.AscendingOrder and Qt.DescendingOrder or Qt.AscendingOrder
        else:
            order = Qt.AscendingOrder
        self.oldSortingIndex = index
        self.oldSortingOrder = order

    def clear(self):
        """Remove the current data set"""
        self.setRTable('matrix("")')
        

    def getSettings(self):
        """Save qtWidget state"""
        r = {'Rdata': self.Rdata,
        'selection':[[i.row(),i.column()] for i in self.selectedIndexes()]}
        if self.oldSortingIndex != None:
            r['sortIndex'] = self.oldSortingIndex
            r['order'] = self.oldSortingOrder

        return r
    def loadSettings(self,data):
        """Load qtWidget state"""
        if not data['Rdata']: return 
        
        self.setRTable(data['Rdata'])
        
        if 'sortIndex' in data.keys():
            self.sortByColumn(data['sortIndex'],data['order'])
        if 'selection' in data.keys() and len(data['selection']):
            for i in data['selection']:
                self.setItemSelected(self.item(i[0],i[1]),True)

    def getReportText(self, fileDir):
        """return data to :mod:`redRReports` module for creating reports."""
        if self.Rdata:
            data = self.R('as.matrix(%s)'% self.Rdata)
            colNames = self.R('colnames(%s)' % self.Rdata)
            text = redRReports.createTable(data, columnNames = colNames)
        else:
            text = ''
        return {self.widgetName:{'includeInReports': self.includeInReports, 'text': text}}


class MyTableModel(QAbstractTableModel): 
    """
    This helper class should never be accessed directly. It will maintain a link with the R data set 
    and serve the data as the GUI is updated to view new rows and columns. It maintains only a small
    amount of data in memory and recycles as new section of table is in view. All the sorting and filtering
    options selected in the GUI are passed to this class, which translates the requests into R.
    """
    def __init__(self, Rdata, parent,editable=False): 
        """ Rdata: a R varible
            parent: the parent qtWidget
        """
        self.R = Rcommand
        self.editable = editable

        #print parent
        QAbstractTableModel.__init__(self,parent) 
        
        #print 'length rownams %d' % len(self.rownames)
        
        # if self.editable:
            # self.arraydata = self.R('as.matrix(rbind(c("rownames",colnames(as.data.frame(' +Rdata+ '))), cbind(rownames(as.data.frame(' +Rdata+')),'+Rdata+')))', wantType = 'list')
            # self.colnames.insert(0,_('Row Names'))
            # self.rownames.insert(0,_('Row Names'))
        # else:
        #self.arraydata = self.R('as.matrix('+Rdata+')', wantType = 'list')
        self.initData(Rdata)
        # print self.arraydata
        # print 'arraydata type:' ,type(self.arraydata)
    def flags(self,index):
        """internal function. DO NOT USE OR OVERWRITE. consult QT documentation"""
        if self.editable:
            return (Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        else:
            return (Qt.ItemIsSelectable | Qt.ItemIsEnabled)
    
 
    def initData(self,Rdata):
        """internal function. DO NOT USE OR OVERWRITE. consult QT documentation"""
        self.Rdata = Rdata
        self.colnames = self.R('colnames(as.data.frame(' +Rdata+ '))', wantType = 'list',silent=True)
        self.rownames = self.R('rownames(as.data.frame(' +Rdata+'))', wantType = 'list',silent=True)
        self.arraydata = self.R('as.matrix('+Rdata+')', wantType = 'listOfLists',silent=True)
    def columnCount(self, parent):
        """internal function. DO NOT USE OR OVERWRITE. consult QT documentation"""
        if not self.arraydata or self.arraydata == None: return 0
        return len(self.arraydata[0])
    def rowCount(self, parent):
        """internal function. DO NOT USE OR OVERWRITE. consult QT documentation"""
        if not self.arraydata or self.arraydata == None: return 0
        return len(self.arraydata)
    def data(self, index, role):
        """internal function. DO NOT USE OR OVERWRITE. consult QT documentation"""
        # print _('in data')
        if not index.isValid(): 
            return QVariant() 
        elif role != Qt.DisplayRole: 
            return QVariant() 
        return QVariant(self.arraydata[index.row()][index.column()]) 

    def setData(self,index,data, role):
        """internal function. DO NOT USE OR OVERWRITE. consult QT documentation"""
        print _('in setData'), data.toString(), index.row(),index.column(), role
        if not index.isValid(): 
            return False
        elif role == Qt.EditRole: 
            print self.arraydata[index.row()][index.column()]
            self.arraydata[index.row()][index.column()] = data.toString()
            Rcmd = '%s[%d,%d]="%s"' % (self.Rdata, index.row(), index.column(), data.toString())
            # print Rcmd
            self.R(Rcmd, wantType = 'NoConversion')
            print self.arraydata
            print self.arraydata[index.row()][index.column()]
            self.emit(SIGNAL("dataChanged()"))
            return True
        # elif role == Qt.BackgroundRole:
            # print _('in BackgroundRole')
            # d = self.itemDelegate(index)
            # d.paint(QBrush(Qt.red))
            # return True
        
        return False
    
    def headerData(self, col, orientation, role):
        """internal function. DO NOT USE OR OVERWRITE. consult QT documentation"""
        # print _('in headerData'), col
        try:
            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return QVariant(self.colnames[col])
            elif orientation == Qt.Vertical and role == Qt.DisplayRole:     
                return QVariant(self.rownames[col])
            return QVariant()
        except IndexError:
            return QVariant()
    
    def setHeaderData(self,col,orientation,data,role):
        """internal function. DO NOT USE OR OVERWRITE. consult QT documentation"""
        # print _('in setHeaderData')
        if orientation == Qt.Horizontal and role == Qt.EditRole:
            self.colnames[col] = data.toString()
            self.emit(SIGNAL("headerDataChanged()"))
            return True
        else:
            return False
        ## please reimplement in a later version
    def insertRows(self,beforeRow,count,headers=None):
        """internal function. DO NOT USE OR OVERWRITE. consult QT documentation"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.emit(SIGNAL("beginInsertRows()"))
        size= self.columnCount(self)
        toAppend= ['' for i in xrange(self.columnCount(self))]
        # print size
        # print toAppend
        # print count
        for i in xrange(count):
            self.arraydata.append(toAppend)

        if headers:
            self.rownames.extend(headers)
        else:
            size = len(self.rownames)+1
            # print self.rownames
            # print size
            headers = [unicode(i) for i in range(size,size+count)]
            # print headers
            self.rownames.extend(headers)
        self.R('t = matrix("",nrow='+str(count)+',ncol=ncol('+self.Rdata+'))', wantType = 'NoConversion')
        self.R('colnames(t) = colnames('+self.Rdata+')', wantType = 'NoConversion')
        self.R('rownames(t) = rownames("%s")' % '","'.join(headers), wantType = 'NoConversion')
        self.R(self.Rdata+'=rbind('+self.Rdata+',t)', wantType = 'NoConversion')


        self.emit(SIGNAL("endInsertRows()"))
        self.emit(SIGNAL("layoutChanged()"))
        return True
    def insertColumns(self,beforeColumn,count,headers=None):
        """internal function. DO NOT USE OR OVERWRITE. consult QT documentation"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.emit(SIGNAL("beginInsertRows()"))

        toAppend = ['' for i in xrange(count)]
        for x in self.arraydata:
            x.extend(toAppend)

        if headers:
            self.colnames.extend(headers)
        else:
            size = len(self.colnames)+1
            # print self.colnames
            # print size
            headers = ['V'  +unicode(i) for i in range(size,size+count)]
            # print headers
            self.colnames.extend(headers)
        
        #self.R('%s = cbind(%s,

        self.emit(SIGNAL("endInsertRows()"))
        self.emit(SIGNAL("layoutChanged()"))

    def sort(self, Ncol, order):
        
        """Sort table by given column number.
            
        Internal function. DO NOT USE OR OVERWRITE. consult QT documentation.
        """
        if self.editable: return
        print _('in sort')
        import operator
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        
        for r,x in zip(self.rownames, self.arraydata):
            x.append(r)
        # self.arraydata.append(self.rownames)
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
       
        self.rownames = [x.pop() for x in self.arraydata]
        self.emit(SIGNAL("layoutChanged()"))

        
"""
class MyTableModel(QAbstractTableModel): 
    def __init__(self, Rdata, parent,editable=False): 
        self.R = Rcommand
        self.editable = editable

        #print parent
        QAbstractTableModel.__init__(self,parent) 
        self.Rdata = Rdata
        self.orgRdata = Rdata
        
        self.colnames = self.R('colnames(as.data.frame(' +self.Rdata+ '))', wantType = 'list')
        self.rownames = self.R('rownames(as.data.frame(' +self.Rdata+'))', wantType = 'list')
        self.nrow = self.R('nrow(%s)' % self.Rdata,silent=True)
        self.ncol = self.R('ncol(%s)' % self.Rdata,silent=True)
        # nrows = self.R('nrow(%s)' % self.Rdata)
        #print 'length rownams %d' % len(self.rownames)
        
        # if self.editable:
            # self.arraydata = self.R('as.matrix(rbind(c("rownames",colnames(as.data.frame(' +Rdata+ '))), cbind(rownames(as.data.frame(' +Rdata+')),'+Rdata+')))', wantType = 'list')
            # self.colnames.insert(0,_('Row Names'))
            # self.rownames.insert(0,_('Row Names'))
        # else:
        # self.arraydata = self.R('as.matrix('+Rdata+')', wantType = 'list')
        
        # print self.arraydata
        # print 'arraydata type:' ,type(self.arraydata)
    def flags(self,index):
        if self.editable:
            return (Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        else:
            return (Qt.ItemIsSelectable | Qt.ItemIsEnabled)
    def rowCount(self, parent): 
        return self.nrow
        #return len(self.arraydata)
    def columnCount(self, parent): 
        return self.ncol
        #return len(self.arraydata[0])
    def data(self, index, role): 
        # print _('in data')
        if not index.isValid(): 
            return QVariant() 
        elif role != Qt.DisplayRole: 
            return QVariant() 
        return self.R('%s[%d,%d]' % (self.Rdata,index.row()+1,index.column()+1))
        #return QVariant(self.arraydata[index.row()][index.column()]) 

    def setData(self,index,data, role):
        print _('in setData'), data.toString(), index.row(),index.column(), role
        if not index.isValid(): 
            return False
        elif role == Qt.EditRole: 
            # print self.arraydata[index.row()][index.column()]
            # self.arraydata[index.row()][index.column()] = data.toString()
            Rcmd = '%s[%d,%d]="%s"' % (self.Rdata, index.row(), index.column(), data.toString())
            # print Rcmd
            self.R(Rcmd)
            # print self.arraydata
            # print self.arraydata[index.row()][index.column()]
            self.emit(SIGNAL("dataChanged()"))
            return True
        # elif role == Qt.BackgroundRole:
            # print _('in BackgroundRole')
            # d = self.itemDelegate(index)
            # d.paint(QBrush(Qt.red))
            # return True
        
        return False
    
    def headerData(self, col, orientation, role):
        # print _('in headerData'), col
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.colnames[col])
            # return self.R('colnames(as.data.frame(%s))[%d]' % (self.Rdata,col),silent=True)
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:     
            return QVariant(self.rownames[col])
            # return self.R('rownames(as.data.frame(%s))[%d]' % (self.Rdata,col),silent=True)
        return QVariant()
    
    def setHeaderData(self,col,orientation,data,role):
        # print _('in setHeaderData')
        if orientation == Qt.Horizontal and role == Qt.EditRole:
            self.colnames[col] = data.toString()
            self.emit(SIGNAL("headerDataChanged()"))
            return True
        else:
            return False
    def clear(self):
        pass
        ## please reimplement in a later version
    def insertRows(self,beforeRow,count,headers=None):
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.emit(SIGNAL("beginInsertRows()"))
        size= self.columnCount(self)
        toAppend= ['' for i in xrange(self.columnCount(self))]
        # print size
        # print toAppend
        # print count
        for i in xrange(count):
            self.arraydata.append(toAppend)

        if headers:
            self.rownames.extend(headers)
        else:
            size = len(self.rownames)+1
            # print self.rownames
            # print size
            headers = [unicode(i) for i in range(size,size+count)]
            # print headers
            self.rownames.extend(headers)
        self.R('t = matrix("",nrow='+unicode(count)+',ncol=ncol('+self.Rdata+'))')
        self.R('colnames(t) = colnames('+self.Rdata+')')
        self.R('rownames(t) = rownames("%s")' % '","'.join(headers))
        self.R(self.Rdata+'=rbind('+self.Rdata+',t)')


        self.emit(SIGNAL("endInsertRows()"))
        self.emit(SIGNAL("layoutChanged()"))
        return True
    def insertColumns(self,beforeColumn,count,headers=None):
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.emit(SIGNAL("beginInsertRows()"))

        toAppend = ['' for i in xrange(count)]
        for x in self.arraydata:
            x.extend(toAppend)

        if headers:
            self.colnames.extend(headers)
        else:
            size = len(self.colnames)+1
            # print self.colnames
            # print size
            headers = ['V'  +unicode(i) for i in range(size,size+count)]
            # print headers
            self.colnames.extend(headers)
        
        #self.R('%s = cbind(%s,

        self.emit(SIGNAL("endInsertRows()"))
        self.emit(SIGNAL("layoutChanged()"))

    def sort(self, Ncol, order):
        if self.editable: return
        
        if order == Qt.DescendingOrder:
            self.Rdata = '%s[order(%s[,%d]),]' % (self.orgRdata,self.orgRdata,Ncol+1)
        else:
            self.Rdata = '%s[order(%s[,%d],decreasing=TRUE),]' % (self.orgRdata,self.orgRdata,Ncol+1)
            
        self.colnames = self.R('colnames(as.data.frame(' +self.Rdata+ '))', wantType = 'list')
        self.rownames = self.R('rownames(as.data.frame(' +self.Rdata+'))', wantType = 'list')
        self.nrow = self.R('nrow(%s)' % self.Rdata)
        self.ncol = self.R('ncol(%s)' % self.Rdata)

        # print _('in sort')
        # import operator
        # self.emit(SIGNAL("layoutAboutToBeChanged()"))
        
        # for r,x in zip(self.rownames, self.arraydata):
            # x.append(r)
        # self.arraydata.append(self.rownames)
        # self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        
        # if order == Qt.DescendingOrder:
            # self.arraydata.reverse()
       
        # self.rownames = [x.pop() for x in self.arraydata]
        self.emit(SIGNAL("layoutChanged()"))

    def delete(self):
        sip.delete(self)  
"""