# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import shutil
import subprocess

class functionsDymola():

    #create the FMUs as Dymola models (.mo)
    def importFMUs(self, objects, newmodelbasefolderpath):
        #move each FMU in an own directory
        cdList = []
        importFMUList = []
        for obj in objects:
            mofilepathname, file_extension = os.path.splitext(obj[1])
            cdList.append(mofilepathname)
            if not os.path.exists(mofilepathname):
                os.makedirs(mofilepathname)
            newmofilepathname = os.path.join(mofilepathname, obj[0]+".fmu")
            shutil.move(obj[1], newmofilepathname)
            importFMUList.append(newmofilepathname)
        #write a Dymola script to import the FMUs
        scriptPathName = os.path.join(newmodelbasefolderpath, "importFMU.mos")
        with open(scriptPathName, "w") as impFMU:
            for f in range(len(cdList)):
                #replace the folderseparators to the Dymola type "\\"
                cdstr = cdList[f].replace("/", "\\\\")  # "/" to "\\"
                cdstr = cdstr.replace("\\", "\\\\")  # "\" to "\\"
                cdstr = cdstr.replace("\\\\\\", "\\")  # "\\\" to "\"
                impFMU.write('cd("'+cdstr+'");\n')
                impFMU.write('importFMU("'+os.path.basename(importFMUList[f])+'");\n')
            impFMU.write('Modelica.Utilities.System.exit();\n') #otherwise Dymola does not return
        #run the script
        subprocess.call(["dymola", "-nowindow", scriptPathName], shell=True)
        #delete the mos script
        os.remove(scriptPathName)
        #delete the FMU
        for f in range(len(cdList)):
            os.remove(importFMUList[f])
        #rename and rework the names in the imported .mo file
        newmodelbasefilespathname = []
        for iFMUFolder in cdList:
            for filename in os.listdir(iFMUFolder):  # list the files in the directory
                #rename the file
                if not (filename.endswith('.mo')): continue
                mofile = os.path.join(iFMUFolder, filename)
                oldmoname, moext = os.path.splitext(filename)
                newmoname = os.path.basename(iFMUFolder)
                renmofile = os.path.join(iFMUFolder, newmoname+".mo")
                os.rename(mofile, renmofile)
                #edit the file -> all oldmoname in the text needs to be replaced with newmoname
                with open(renmofile, 'r') as updatemofile:     #read the file
                    mofiledata = updatemofile.read()
                mofiledata = mofiledata.replace(oldmoname, newmoname)                   #replace the string oldmoname with the string newmoname
                with open(renmofile, 'w') as updatemofile:     #write the updated file
                    updatemofile.write(mofiledata)
                #append the renamed .mo file to the list where the modelbasefiles are
                newmodelbasefilespathname.append(renmofile)
        return newmodelbasefilespathname

    #create a textfile with instructions on how to build the system
    def initModel(self, modelfolderpathname, modelname):
        modelfile = os.path.join(modelfolderpathname, modelname)
        modelfile = modelfile + ".mo"
        fileobject = open(modelfile, "w")
        #begin statement
        fileobject.write("model "+modelname+"\n")
        fileobject.close()
        return modelfile

    def addComponents(self, objects, modelfile, modelname, interface):
        fileobject = open(modelfile, "a")
        for ob in objects:
            #create objects
            blockname = ob[0]
            if interface == "native":
                type = ob[1]
                type = type.replace("/", ".")   #change separator from '/' to '.'
                fileobject.write("  "+type+" "+blockname+"(")
                #set block parameters
                atro = 0
                while atro < len(ob[2]):
                    #change definition of list / array constant -> the modelbase cares for that now or FMI is used
                    #if len(ob[2][atro][1]) > 0 and ob[2][atro][1][0] == "[":
                        #ob[2][atro][1].replace("[", "{")
                        #ob[2][atro][1].replace("]", "}")
                    #now insert the parameter in the text
                    fileobject.write(ob[2][atro][0]+"="+ob[2][atro][1])
                    #if there are more attributes, a comma is needed
                    if atro < len(ob[2])-1:
                        fileobject.write(",")
                    #next attribute
                    atro += 1
            else:
                type, ext = os.path.splitext(os.path.basename(ob[1]))
                fileobject.write("  " + type + " " + blockname + "1(")
                #block parameters do not need to be written for the FMI interface, since the FMUs are preconfigured
            #close parameters
            fileobject.write(")")
            #add placement information (all will be on each other) (without placement information, the objects are not shown, just in sourcecode)
            #fileobject.write(" annotation(\nPlacement(visible = true, transformation(origin = {-176, 26}, extent = {{-10, -10}, {10, 10}}, rotation = 0)))")
            #close the object
            fileobject.write(";\n")
        fileobject.close()

    def addConnections(self, couplings, modelfile, modelname, interface):
        fileobject = open(modelfile, "a")
        fileobject.write("equation\n")
        for cpl in couplings:
            sourceblock = cpl[0]
            sourceport = cpl[1]
            sinkblock = cpl[2]
            sinkport = cpl[3]
            #now write the port information
            if interface == "native":
                fileobject.write("  connect(" + sourceblock + "." + sourceport + ", " + sinkblock + "." + sinkport + ");\n")
            else:
                fileobject.write("  connect("+sourceblock+"1."+sourceport+", "+sinkblock+"1."+sinkport+");\n")
        #end statement
        fileobject.write("end "+modelname+";\n")
        fileobject.close()
        return 0