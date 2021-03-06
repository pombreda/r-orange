import os, sys
import tempfile
import rpy3.rinterface

rpy3.rinterface.initr()

import conversion

class RObjectMixin(object):
    """ Class to provide methods common to all RObject instances """
    __rname__ = None

    __tempfile = rpy3.rinterface.baseenv.get("tempfile")
    __file = rpy3.rinterface.baseenv.get("file")
    __fifo = rpy3.rinterface.baseenv.get("fifo")
    __sink = rpy3.rinterface.baseenv.get("sink")
    __close = rpy3.rinterface.baseenv.get("close")
    __readlines = rpy3.rinterface.baseenv.get("readLines")
    __unlink = rpy3.rinterface.baseenv.get("unlink")
    __rclass = rpy3.rinterface.baseenv.get("class")
    __rclass_set = rpy3.rinterface.baseenv.get("class<-")
    __show = rpy3.rinterface.baseenv.get("show")

    def __str__(self):
        if sys.platform == 'win32':
            tmpf = tempfile.NamedTemporaryFile()
            tmp = self.__file(rpy3.rinterface.StrSexpVector([tmpf.name,]), 
                              open = rpy3.rinterface.StrSexpVector(["r+", ]))
            self.__sink(tmp)
        else:
            writeconsole = rpy3.rinterface.get_writeconsole()
            s = []
            def f(x):
                s.append(x)
            rpy3.rinterface.set_writeconsole(f)
        self.__show(self)
        if sys.platform == 'win32':
            self.__sink()
            s = tmpf.readlines()
            tmpf.close()
            s = str.join(os.linesep, s)
        else:
            rpy3.rinterface.set_writeconsole(writeconsole)
            s = str.join('', s)
        return s

    def r_repr(self):
        """ String representation for an object that can be
        directly evaluated as R code.
        """
        return repr_robject(self, linesep='\n')

    def _rclass_get(self):
        try:
            res = self.__rclass(self)
            #res = conversion.ri2py(res)
            return res
        except rpy3.rinterface.RRuntimeError, rre:
            if self.typeof == rpy3.rinterface.SYMSXP:
                #unevaluated expression: has no class
                return (None, )
            else:
                raise rre
    def _rclass_set(self, value):
        res = self.__rclass_set(self, value)
        self.__sexp__ = res.__sexp__
            
    rclass = property(_rclass_get, _rclass_set, None,
                      "R class for the object, stored an R string vector.")


def repr_robject(o, linesep=os.linesep):
    s = rpy3.rinterface.baseenv.get("deparse")(o)
    s = str.join(linesep, s)
    return s



class RObject(RObjectMixin, rpy3.rinterface.Sexp):
    """ Base class for all R objects. """
    def __setattr__(self, name, value):
        if name == '_sexp':
            if not isinstance(value, rpy3.rinterface.Sexp):
                raise ValueError("_attr must contain an object " +\
                                     "that inherits from rpy3.rinterface.Sexp" +\
                                     "(not from %s)" %type(value))
        super(RObject, self).__setattr__(name, value)

