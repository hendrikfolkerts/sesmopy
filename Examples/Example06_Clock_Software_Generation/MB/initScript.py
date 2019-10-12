import os

#get the current directory of this script
scriptpath = os.path.dirname(os.path.realpath(__file__))

#list all files in this directory
files = []
for filename in os.listdir(scriptpath):
    if (filename == os.path.basename(__file__)): continue   #if it is not the file of this script
    files.append(filename)

#go line by line through all files in this directory and add parts
for filename in os.listdir(scriptpath):
    if (filename == os.path.basename(__file__)): continue   #if it is not the file of this script
    filepathname = os.path.join(scriptpath, filename)
    if os.path.isdir(filepathname):
        pass    #it is a directory -> not needed for this example
    elif os.path.isfile(filepathname):
        #it is a normal file
        if filename == "index.html":    #open the file in which lines shall be added
            #open and read the file
            f = open(filepathname, 'r')
            sourcecodeFile = f.read().split("\n")   #read file and split lines
            #add necessary lines in case the respective file is available
            numLines = len(sourcecodeFile)
            l = 0
            while l < numLines:

                if l == 6:
                    if "light.css" in files:
                        sourcecodeFile.insert(l, '		<link rel="stylesheet" href="light.css">')
                    elif "dark.css" in files:
                        sourcecodeFile.insert(l, '		<link rel="stylesheet" href="dark.css">')
                    l += 1
                    numLines += 1

                if l == 15:
                    if "date.js" in files:
                        sourcecodeFile.insert(l, '		<output id="date"></output><br>')
                        sourcecodeFile.insert(l + 1, '		<script language="javascript" type="text/javascript" src="date.js"></script>')
                    l += 2
                    numLines += 2

                l += 1
            #join lines
            sourcecodeFile = "\n".join(sourcecodeFile)
            f.close()
            #open and wrtite the changed file
            f = open(filepathname, 'w')
            f.write(sourcecodeFile)
            f.close()
    else:
        pass    #it is a special file (e.g. device file)