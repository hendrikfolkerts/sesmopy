# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import shutil
import subprocess

class functionsOpenModelica():

    #create the model FMUs as OpenModelica models (.mo)
    def importFMUs(self, modelFMUs):
        #move each FMU in an own directory
        for mfmu in modelFMUs:
            mofilepathname, file_extension = os.path.splitext(mfmu)
            if not os.path.exists(mofilepathname):
                os.makedirs(mofilepathname)
            newmofilepathname = os.path.join(mofilepathname, os.path.split(mfmu)[1])
            shutil.move(mfmu, newmofilepathname)
        #write a OpenModelica script to import the model FMU
        if len(modelFMUs) > 0:
            scriptPathName = os.path.join(os.path.split(modelFMUs[0])[0], "importFMU.mos")
            with open(scriptPathName, "w") as impFMU:
                for mfmu in modelFMUs:
                    #replace the folderseparators to the OpenModelica type "\\"
                    mfmustr = mfmu.replace("/", "\\\\")  # "/" to "\\"
                    mfmustr = mfmustr.replace("\\", "\\\\")  # "\" to "\\"
                    mfmustr = mfmustr.replace("\\\\\\", "\\")  # "\\\" to "\"
                    impFMU.write('cd("'+os.path.splitext(mfmustr)[0]+'");\n')
                    impFMU.write('importFMU("'+os.path.basename(mfmu)+'");\n')
                    impFMU.write('\n')
            #run the script
            subprocess.call(["omc", scriptPathName])
            #delete the mos script
            os.remove(scriptPathName)
            #delete the FMU
            for mfmu in modelFMUs:
                newfmupath = os.path.join(os.path.splitext(mfmu)[0], os.path.basename(mfmu))
                os.remove(newfmupath)

            #rename and rework the names in the imported .mo file
            newmodelbasefilespathname = []
            for iFMUFolderFull in modelFMUs:
                iFMUFolder = os.path.splitext(iFMUFolderFull)[0]
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

        else:
            return []

    #create a textfile with instructions on how to build the system
    def initModel(self, modelfolderpathname, modelname, additionalFiles):
        modelfile = os.path.join(modelfolderpathname, modelname)
        modelfile = modelfile + ".mo"
        fileobject = open(modelfile, "w")
        #begin statement
        fileobject.write("model "+modelname+"\n")
        fileobject.close()
        return modelfile

    def addComponents(self, objects, modelfile, modelname, interface):
        fileobject = open(modelfile, "a")
        if interface in  ["native", "createModelFMI"]:  #the interface is native or it is called for creating a model FMU
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
                else:   #a model FMU shall be created of the components given in objects
                    type, ext = os.path.splitext(os.path.basename(ob[1]))
                    fileobject.write("  " + type + " " + blockname + "1(")
                    #block parameters do not need to be written for the FMI interface, since the basic models (which can be FMUs) are preconfigured
                #close parameters
                fileobject.write(")")
                #add placement information (all will be on each other) (without placement information, the objects are not shown, just in sourcecode)
                #fileobject.write(" annotation(\nPlacement(visible = true, transformation(origin = {-176, 26}, extent = {{-10, -10}, {10, 10}}, rotation = 0)))")
                #close the object
                fileobject.write(";\n")

        else:   #the interface is FMI -> the complete model as FMU
            type = os.path.basename(os.path.splitext(objects)[0])
            fileobject.write("  " + type + " " + type + "1();\n")

        fileobject.close()

    def addConnections(self, couplings, modelfile, modelname, interface):
        #for FMI some portblocks need to be added -> store all information in lists first
        portblocklines = []
        couplinglines = []
        for cpl in couplings:
            sourceblock = cpl[0]
            sourceport = cpl[1].split(" / ")[0].strip()
            sourceporttype = cpl[1].split(" / ")[1].strip()
            sinkblock = cpl[2]
            sinkport = cpl[3].split(" / ")[0].strip()
            #sinkporttype = cpl[3].split(" / ")[1].strip()  #not needed for now
            #now write the port information
            if interface == "native":
                couplinglines.append("  connect(" + sourceblock + "." + sourceport + ", " + sinkblock + "." + sinkport + ");\n")
            else:
                #append the coupling
                couplinglines.append("  connect(" + sourceblock + "1." + sourceport + ", " + sinkblock + "1." + sinkport + ");\n")
                #append the out block (right type) and the coupling
                if sourceporttype == "SPR":
                    portblocklines.append("  Modelica.Blocks.Interfaces.RealOutput "+sourceblock+"_"+sourceport+"_Out;\n")
                elif sourceporttype == "SPI":
                    portblocklines.append("  Modelica.Blocks.Interfaces.IntegerOutput "+sourceblock+"_"+sourceport+"_Out;\n")
                elif sourceporttype == "SPB":
                    portblocklines.append("  Modelica.Blocks.Interfaces.BooleanOutput "+sourceblock+"_"+sourceport+"_Out;\n")
                couplinglines.append("  connect("+sourceblock+"1."+sourceport+", "+sourceblock+"_"+sourceport+"_Out);\n")

        #now write in file
        fileobject = open(modelfile, "a")
        #first write any blocks stored in portblocklines, that need to be inserted
        for pbl in portblocklines:
            fileobject.write(pbl)
        #next section
        fileobject.write("equation\n")
        #write the couplings stored in couplinglines
        for cl in couplinglines:
            fileobject.write(cl)
        #end statement
        fileobject.write("end "+modelname+";\n")
        fileobject.close()
        return 0