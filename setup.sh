# red-r linux setup.  Several things we need to do here.

BASEDIR=$PWD
echo $BASEDIR
last=$(uname -m)

# install all of the dependencies

sudo apt-get install python-qt4
sudo apt-get install python-docutils
sudo apt-get install python-numpy
sudo apt-get install python-qwt5-qt4
sudo apt-get install python-rpy python-dev python-numarray-ext python-numeric-ext python-matplotlib python-qt4-dev libqwt5-qt4-dev pyqt4-dev-tools sip4 python-qwt5-qt4

# install the rpy3 and conversion libraries
cd rpy3-setup
python setup.py build
cd ..


echo "Your architecture is $last"

if [ $last="x84_64" ];
then 
    cp -r rpy3-setup/build/lib.linux*/rpy3 linux64/
else
    cp -r rpy3-setup/build/lib.linux*/rpy3 linux32/
fi

cd redrrpy-setup
python setup.py build
cd ..

if [ $last="x86_64" ];
then 
    cp -r redrrpy-setup/build/lib.linux*/_conversion.so linux64/redrrpy/_conversion.so
else 
    cp -r redrrpy-setup/build/lib.linux*/_conversion.so linux32/redrrpy/_conversion.so
fi
 
echo "Your base dir is $BASEDIR" 
 
echo  "#!/bin/bash
# Shell wrapper for R executable.
 
python $BASEDIR/canvas/red-RCanvas.pyw" > /usr/bin/RedR

sudo chmod 755 /usr/bin/RedR

echo "Thanks for setting up Red-R, you can run Red-R by typing RedR"

# # output the shell script file
# with open("/usr/bin/RedR", 'w') as f:
#     f.write("""
# #!/bin/bash
# # Shell wrapper for R executable.
# 
# python %s/canvas/red-RCanvas.pyw""" % os.path.abspath(os.path.split(sys.argv[0])[0]))
#     f.close()
#     
# os.system('chmod 755 /usr/bin/RedR')