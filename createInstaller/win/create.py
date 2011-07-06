# python create.py 1 1, argv[1] = create compiled, argv[2] = make nsis installer

import os, subprocess, sys
 
#redRDir = 'C:/Users/anup/Documents/red/develop/makeInstallers/code/Version1.85_gold'
redRDir = 'C:/Python26/Lib/site-packages/RedRTrunk'  # change for system specific for sandbox version
 
runCompile = sys.argv[1]
runInstaller = sys.argv[2]
# runupload = sys.argv[3]

cmd = 'python createCompiledCode.py py2exe %s' % redRDir 
if runCompile == '1':
    print 'Running: ' + cmd
    os.system(cmd)


#makensisw = "C:/Program Files/NSIS/makensis.exe" # change for system specific for kyle
makensisw = "C:/Program Files/NSIS/makensis.exe" # change for system specific
##########compiled version
defines = {}
defines['REDRVERSION1'] =  "1.85b"
defines['Red-RDIR']=       redRDir
# defines['RDIRECTORY'] =    "C:/Installer/R/R-2.11.1"  # system specific for Kyle
defines['RDIRECTORY'] =    "C:/Installer/R/R-2.11.1"  # system specific
defines['RVER']=           "R-2.11.1"
#defines['OUTPUTDIR'] =     "C:/Users/anup/Documents/red/develop/makeInstallers/installer"  # system specific
defines['OUTPUTDIR'] =     "C:/Installer/Red-RInstallers"  # system specific for kyle

params = ''
for k,v in defines.items():
    params+= '/D"%s=%s" ' % (k,v)


if runInstaller =='1':

    cmd = '"%s" /X"SetCompressor /FINAL /SOLID lzma" %s Red-R-compiled.nsi' % (makensisw,params)
    print 'Running installer: ' + cmd
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE).communicate()[0]
    print p
    cmd = '"%s" /X"SetCompressor /FINAL /SOLID lzma" %s Red-R-compiled-updater.nsi' % (makensisw,params)
    print 'Running updated: ' + cmd
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE).communicate()[0]
    print p

    # cmd = 'python %s/googlecode_upload.py -s "Compiled version" -p r-orange -u anup.parikh -w VF6NG8Mr3Nc6 %s' % (baseDir, compiledVersion.replace('\\','/'))
    # if runupload== '1':
        # print 'Running: ' + cmd
        # subprocess.call(cmd)

