#!/bin/bash
# make sure, this script is executable
# go to directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR
# create runnable with pyinstaller
#   if pyinstaller is installed, but it cannot be executed:
#   sudo find / -name pyinstaller
#   sudo ln -s /path/to/pyinstaller /usr/bin/pyinstaller
#   -> now it can be executed
pyinstaller --windowed --name=SESMoPy --icon=i2rightarrow.ico main.py
# copy files
cp *.png dist/SESMoPy
cp *.ico dist/SESMoPy
cp Documentation/Doc_LaTeX/doc.pdf dist/SESMoPy
% copy Examples
cp -r Examples dist/SESMoPy/Examples
% change folder
cd dist
% get processor architecture
MACHINETYPE=`uname -m`
# get the date
DATE=$(date +%Y-%m-%d_%H-%M-%S)
# tar folder
destname="SESMoPy_Linux_Executable_$MACHINETYPE"_"$DATE.tar.gz"
tar -czf $destname SESMoPy/
# move tar in directory 2 above
mv $destname ../../
# go directory back
cd ..
# remove created directories
rm -r build dist
rm SESMoPy.spec