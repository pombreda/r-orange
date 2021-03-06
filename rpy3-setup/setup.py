
import os, os.path, sys, shutil, re, itertools
from distutils.command.build_ext import build_ext as _build_ext
from distutils.command.build import build as _build

from distutils.core import setup
from distutils.core import Extension


pack_name = 'rpy3'
pack_version = __import__('rpy').__version__


class build(_build):
    user_options = _build.user_options + \
        [
        #('r-autoconfig', None,
        # "guess all configuration paths from " +\
        #     "the R executable found in the PATH " +\
        #     "(this overrides r-home)"),
        ('r-home=', None, 
         "full path for the R home to compile against " +\
             "(see r-autoconfig for an automatic configuration)"),
        ('r-home-lib=', None,
         "full path for the R shared lib/ directory " +\
             "(<r-home>/lib otherwise)"),
        ('r-home-modules=', None,
         "full path for the R shared modules/ directory " +\
             "(<r-home>/modules otherwise)") 
        ]
    boolean_options = _build.boolean_options #+ \
        #['r-autoconfig', ]


    def initialize_options(self):
        _build.initialize_options(self)
        self.r_autoconfig = None
        self.r_home = None
        self.r_home_lib = None
        self.r_home_modules = None

class build_ext(_build_ext):
    """
    -DRPY_VERBOSE
    -DRPY_DEBUG_PRESERV
    -DRPY_DEBUG_PROMISE    : evaluation of promises
    -DRPY_DEBUG_OBJECTINIT : initialization of PySexpObject
    -DRPY_DEBUG_CONSOLE    : console I/O
    -DRPY_DEBUG_COBJECT    : SexpObject passed as a CObject
    -DRPY_DEBUG_GRDEV
    """
    user_options = _build_ext.user_options + \
        [
        #('r-autoconfig', None,
        #  "guess all configuration paths from " +\
        #      "the R executable found in the PATH " +\
        #      "(this overrides r-home)"),
        ('r-home=', None, 
         "full path for the R home to compile against " +\
             "(see r-autoconfig for an automatic configuration)"),
        ('r-home-lib=', None,
         "full path for the R shared lib/ directory" +\
             "(<r-home>/lib otherwise)"),
        ('r-home-modules=', None,
         "full path for the R shared modules/ directory" +\
             "(<r-home>/modules otherwise)")]

    boolean_options = _build_ext.boolean_options #+ \
        #['r-autoconfig', ]

    def initialize_options(self):
        _build_ext.initialize_options(self)
        self.r_autoconfig = None
        self.r_home = None
        self.r_home_lib = None
        self.r_home_modules = None

    def finalize_options(self):
        self.set_undefined_options('build',
                                   #('r_autoconfig', 'r_autoconfig'),
                                   ('r_home', 'r_home'))
        _build_ext.finalize_options(self) 
        if self.r_home is None:
            self.r_home = os.popen("R RHOME").readlines()
            if len(self.r_home) == 0:
                raise SystemExit("Error: Tried to guess R's HOME but no R command in the PATH.")

    #Twist if 'R RHOME' spits out a warning
            if self.r_home[0].startswith("WARNING"):
                self.r_home = self.r_home[1]
            else:
                self.r_home = self.r_home[0]
            #self.r_home = [self.r_home, ]

        if self.r_home is None:
            raise SystemExit("Error: --r-home not specified.")
        else:
            self.r_home = self.r_home.split(os.pathsep)

        rversions = []
        for r_home in self.r_home:
            r_home = r_home.strip()
        rversion = get_rversion(r_home)
        if cmp_version(rversion[:2], [2, 8]) == -1:
            raise SystemExit("Error: R >= 2.8 required.")
        rversions.append(rversion)

        config = RConfig()
        for about in ('--ldflags', '--cppflags', 
                      'LAPACK_LIBS', 'BLAS_LIBS'):
            config += get_rconfig(r_home, about)

        print(config.__repr__())

        self.include_dirs.extend(config._include_dirs)
        self.libraries.extend(config._libraries)
        self.library_dirs.extend(config._library_dirs)
        
        if self.r_home_modules is None:
            self.library_dirs.extend([os.path.join(r_home, 'modules'), ])
        else:
            self.library_dirs.extends([self.r_home_modules, ])
            
        #for e in self.extensions:
        #    self.extra_link_args.extra_link_args(config.extra_link_args)
        #    e.extra_compile_args.extend(extra_compile_args)

    def run(self):
        _build_ext.run(self)



def get_rversion(r_home):
    print 'checking r-home %s' % r_home
    ## i386 added for 64 bit support
    r_exec = os.path.abspath(os.path.join(r_home, 'bin', "i386", 'R'))
    # Twist if Win32
    if sys.platform == "win32":
        print 'opening R for version %s' % r_exec
        rp = os.popen3('"'+r_exec+'" --version')[2]
    else:
        rp = os.popen('"'+r_exec+'" --version')
    rversion = rp.readline()
    #Twist if 'R RHOME' spits out a warning
    if rversion.startswith("WARNING"):
        rversion = rp.readline()
    m = re.match('^R version ([^ ]+) .+$', rversion)
    rversion = m.groups()[0]
    rversion = rversion.split('.')
    rversion[0] = int(rversion[0])
    rversion[1] = int(rversion[1])
    return rversion

def cmp_version(x, y):
    if (x[0] < y[0]):
        return -1
    if (x[0] > y[0]):
        return 1
    if (x[0] == y[0]):
        if len(x) == 1 or len(y) == 1:
            return 0
        return cmp_version(x[1:], y[1:])

class RConfig(object):
    _include_dirs = None
    _libraries = None
    _library_dirs = None 
    _extra_link_args = None
    _frameworks = None
    _framework_dirs = None
    def __init__(self,
                 include_dirs = tuple(), libraries = tuple(),
                 library_dirs = tuple(), extra_link_args = tuple(),
                 frameworks = tuple(),
                 framework_dirs = tuple()):
        for k in ('include_dirs', 'libraries', 
                  'library_dirs', 'extra_link_args'):
            v = locals()[k]
            if not isinstance(v, tuple):
                if isinstance(v, str):
                    v = [v, ]
            v = tuple(set(v))
            self.__dict__['_'+k] = v
        # frameworks are specific to OSX
        for k in ('framework_dirs', 'frameworks'):
            v = locals()[k]
            if not isinstance(v, tuple):
                if isinstance(v, str):
                    v = [v, ]
            v = tuple(set(v))
            self.__dict__['_'+k] = v
            self.__dict__['_'+'extra_link_args'] = tuple(set(v + self.__dict__['_'+'extra_link_args']))
            
            
    def __repr__(self):
        s = 'Configuration for R as a library:' + os.linesep
        s += os.linesep.join(
            ['  ' + x + ': ' + self.__dict__['_'+x].__repr__() \
                 for x in ('include_dirs', 'libraries',
                           'library_dirs', 'extra_link_args')])
        s += os.linesep + ' # OSX-specific (included in extra_link_args)' + os.linesep 
        s += os.linesep.join(
            ['  ' + x + ': ' + self.__dict__['_'+x].__repr__() \
                 for x in ('framework_dirs', 'frameworks')]
            )
        
        return s

    def __add__(self, config):
        assert isinstance(config, RConfig)
        res = RConfig(include_dirs = self._include_dirs + \
                          config._include_dirs,
                      libraries = self._libraries + config._libraries,
                      library_dirs = self._library_dirs + \
                          config._library_dirs,
                      extra_link_args = self._extra_link_args + \
                          config._extra_link_args)
        return res
    @staticmethod
    def from_string(string, allow_empty = False):
        possible_patterns = ('^-L(?P<library_dirs>[^ ]+)$',
                             '^-l(?P<libraries>[^ ]+)$',
                             '^-I(?P<include_dirs>[^ ]+)$',
                             '^(?P<framework_dirs>-F[^ ]+?)$',
                             '^(?P<frameworks>-framework [^ ]+)$')
        pp = [re.compile(x) for x in possible_patterns]
        # sanity check of what is returned into rconfig
        rconfig_m = None        
        span = (0, 0)
        rc = RConfig()
        print 'from_string string: %s' % string
        for substring in re.split('(?<!-framework) ', string):
            ok = False
            for pattern in pp:
                rconfig_m = pattern.match(substring)
                if rconfig_m is not None:
                    rc += RConfig(**rconfig_m.groupdict())
                    span = rconfig_m.span()
                    ok = True
                    break
                elif rconfig_m is None:
                    if allow_empty and (rconfig == ''):
                        print(cmd + '\nreturned an empty string.\n')
                        rc += RConfig()
                        ok = True
                        break
                    else:
                        # if the configuration points to an existing library, 
                        # use it
                        print string
                        if os.path.exists(string):
                            rc += RConfig(library = substring)
                            ok = True
                            break
            if not ok:
                raise ValueError('Invalid substring\n' + substring 
                                 + '\nin string\n' + string)
	print rc
        return rc
            
def get_rconfig(r_home, about, allow_empty = False):
    r_exec = os.path.join(r_home, 'bin', 'R')
    cmd = '"'+r_exec+'" CMD config '+about
    rp = os.popen(cmd)
    print cmd
    ## override here for my path, R CMD not working for some reason
    
    rconfig = {"--ldflags":"-LC:/PROGRA~1/R/R-215~1.0/bin/i386 -lR",
            "--cppflags":"-IC:/PROGRA~1/R/R-215~1.0/include -IC:/PROGRA~1/R/R-215~1.0/include/i386",
            "LAPACK_LIBS":"-LC:PROGRA~1/R/R-215~1.0/bin/i386 -lRlapack",
            "BLAS_LIBS":"-LC:PROGRA~1/R/R-215~1.0/bin/i386 -lRblas"}[about]
        #= rp.readline()
    #Twist if 'R RHOME' spits out a warning
    if rconfig.startswith("WARNING"):
        rconfig = rp.readline()
    rconfig = rconfig.strip()
    #try:
    rc = RConfig.from_string(rconfig)
    # except Exception as inst:
        # print str(inst)
    return rc


def getRinterface_ext():
    #r_libs = [os.path.join(RHOME, 'lib'), os.path.join(RHOME, 'modules')]
    r_libs = []
    extra_link_args = []

    #FIXME: crude way (will break in many cases)
    #check how to get how to have a configure step
    define_macros = []

    if sys.platform == 'win32':
        define_macros.append(('Win32', 1))
    else:
        define_macros.append(('R_INTERFACE_PTRS', 1))
        define_macros.append(('HAVE_POSIX_SIGJMP', 1))

    define_macros.append(('CSTACK_DEFNS', 1))
    define_macros.append(('RIF_HAS_RSIGHAND', 1))

    include_dirs = []
    
    rinterface_ext = Extension(
            name = pack_name + '.rinterface.rinterface',
            sources = [ \
            #os.path.join('rpy', 'rinterface', 'embeddedr.c'), 
            #os.path.join('rpy', 'rinterface', 'r_utils.c'),
            #os.path.join('rpy', 'rinterface', 'buffer.c'),
            #os.path.join('rpy', 'rinterface', 'sequence.c'),
            #os.path.join('rpy', 'rinterface', 'sexp.c'),
            os.path.join('rpy', 'rinterface', 'rinterface.c')
                       ],
            depends = [os.path.join('rpy', 'rinterface', 'embeddedr.h'), 
                       os.path.join('rpy', 'rinterface', 'r_utils.h'),
                       os.path.join('rpy', 'rinterface', 'buffer.h'),
                       os.path.join('rpy', 'rinterface', 'sequence.h'),
                       os.path.join('rpy', 'rinterface', 'sexp.h'),
                       os.path.join('rpy', 'rinterface', 'rpy_rinterface.h')
                       ],
            include_dirs = [os.path.join('rpy', 'rinterface'),] + include_dirs,
            libraries = ['R', ],
            library_dirs = r_libs,
            define_macros = define_macros,
            runtime_library_dirs = r_libs
            #extra_compile_args=['-O0', '-g'],
            #extra_link_args = ['-arch', 'i386','-arch','x86_64']
            )
    #print extra_link_args
    
    rpy_device_ext = Extension(
        pack_name + '.rinterface.rpy_device',
            [
            os.path.join('rpy', 'rinterface', 'rpy_device.c'),
             ],
            include_dirs = include_dirs + 
                            [os.path.join('rpy', 'rinterface'), ],
            libraries = ['R', ],
            library_dirs = r_libs,
            define_macros = define_macros,
            runtime_library_dirs = r_libs,
            #extra_compile_args=['-O0', '-g'],
            extra_link_args = extra_link_args
        )

    return [rinterface_ext, rpy_device_ext]


rinterface_exts = []
ri_ext = getRinterface_ext()
rinterface_exts.append(ri_ext)

pack_dir = {pack_name: 'rpy'}

import distutils.command.install
for scheme in distutils.command.install.INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']
##import os
#os.environ['R_SHARE_DIR'] = '/Users/anupparikh/redr/makeR/Rbuild/R-2.11.1/Resources/share'
#os.environ['LD_LIBRARY_PATH'] = '/Users/anupparikh/redr/makeR/Rbuild/'

print os.environ
setup(
    #install_requires=['distribute'],
    cmdclass = {'build': build,
                'build_ext': build_ext},
    name = pack_name,
    version = pack_version,
    description = "Python interface to the R language",
    url = "http://rpy.sourceforge.net",
    license = "AGPLv3.0 (except rpy3.rinterface: LGPL)",
    author = "Laurent Gautier, modified by Kyle Covington",
    author_email = "lgautier@gmail.com, kyle@red-r.org",
    ext_modules = rinterface_exts[0],
    package_dir = pack_dir,
    packages = [pack_name,
                pack_name + '.rlike',
                pack_name + '.rlike.tests',
                pack_name + '.rinterface',
                pack_name + '.rinterface.tests',
                pack_name + '.robjects',
                pack_name + '.robjects.tests',
                pack_name + '.robjects.lib',
                ],
    classifiers = ['Programming Language :: Python',
                   'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
                   'License :: OSI Approved :: GNU Affero General Public License v3',
                   'Intended Audience :: Developers',
                   'Intended Audience :: Science/Research',
                   'Development Status :: 5 - Production/Stable'
                   ],
    data_files = [(os.path.join('rpy3', 'images'), 
                   [os.path.join('doc', 'source', 'rpy2_logo.png')])]
    
    #[pack_name + '.rinterface_' + x for x in rinterface_rversions] + \
        #[pack_name + '.rinterface_' + x + '.tests' for x in rinterface_rversions]
    )

