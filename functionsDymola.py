# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET

class functionsDymola():

    #create the FMUs as Dymola models (.mo)
    def importFMUs(self, modelFMUs):
        #move each FMU in an own directory
        for mfmu in modelFMUs:
            mofilepathname, file_extension = os.path.splitext(mfmu)
            if not os.path.exists(mofilepathname):
                os.makedirs(mofilepathname)
            newmofilepathname = os.path.join(mofilepathname, os.path.split(mfmu)[1])
            shutil.move(mfmu, newmofilepathname)

        #Dymola has problems importing FMUs when "Structured declaration of variables" is checked:
        # Open Dymola -> Simulation -> Setup -> Tab FMI -> Area Import -> Checkbox "Structured declaration of variables"
        # However, this option cannot be controlled by Dymola's importFMU() function.
        # In the modelDescription.xml of an FMU there is an entry variableNamingConvention="...". It can be "flat" or "structured".
        # In this variable is the convention defined how the ScalarVariable.names have been constructed.
        # However, Dymola seems to have problems when the value is "structured" -> replace with "flat".
        for mfmu in modelFMUs:
            #update the path
            fmufile = os.path.join(os.path.splitext(mfmu)[0], os.path.basename(mfmu))
            #unzip FMUs to a subfolder
            with zipfile.ZipFile(fmufile, 'r') as zipObj:
                #Extract all the contents of zip file in directory obj[0]
                unzippedFMUPath = os.path.split(fmufile)[0]
                zipObj.extractall(unzippedFMUPath)
            #remove the FMU which is just unzipped
            os.remove(fmufile)
            #find the parameter variableNamingConvention and edit it
            for filename in os.listdir(unzippedFMUPath):  # listdir just in case there are more xml files (there should not be according to the definition)
                if not (filename.endswith('.xml') or filename.endswith('.XML')): continue
                xmlfile = os.path.join(unzippedFMUPath, filename)
                # read XML file
                tree = ET.parse(xmlfile)
                # use XPath
                modDesElem = tree.findall('./[@variableNamingConvention]')   #there should be only one
                for elem in modDesElem:
                    # elem.tag return the name of the tag, here "fmiModelDescription"
                    # elem.attrib returns the attributes as dictionary
                    attribNamConDict = elem.attrib
                    # attrXMLval = attribNamConDict.get('variableNamingConvention')  # value of attribute "variableNamingConvention" in XML -> "structured" or "flat"
                    attribNamConDict.update({'variableNamingConvention': 'flat'})
                # write back to file
                tree.write(xmlfile)
            # zip the folder again -> FMU
            cwd = os.getcwd()
            os.chdir(unzippedFMUPath)
            with zipfile.ZipFile(unzippedFMUPath + ".fmu", 'w', zipfile.ZIP_DEFLATED) as zipObj:
                for root, dirs, files in os.walk("./"):
                    for file in files:
                        zipObj.write(os.path.join(root, file))
            os.chdir(cwd)
            # delete the folder zipped as FMU
            shutil.rmtree(unzippedFMUPath)
            #now move the FMU
            if not os.path.exists(unzippedFMUPath):
                os.makedirs(unzippedFMUPath)
            shutil.move(unzippedFMUPath + ".fmu", unzippedFMUPath)

        #write a Dymola script to import the FMUs
        if len(modelFMUs) > 0:
            scriptPathName = os.path.join(os.path.split(modelFMUs[0])[0], "importFMU.mos")
            with open(scriptPathName, "w") as impFMU:
                for mfmu in modelFMUs:
                    #replace the folderseparators to the Dymola type "\\"
                    mfmustr = mfmu.replace("/", "\\\\")  # "/" to "\\"
                    mfmustr = mfmustr.replace("\\", "\\\\")  # "\" to "\\"
                    mfmustr = mfmustr.replace("\\\\\\", "\\")  # "\\\" to "\"
                    impFMU.write('cd("'+os.path.splitext(mfmustr)[0]+'");\n')
                    impFMU.write('importFMU("'+os.path.basename(mfmu)+'");\n')
                impFMU.write('Modelica.Utilities.System.exit();\n') #otherwise Dymola does not return
            #run the script
            subprocess.call(["dymola", "-nowindow", scriptPathName], shell=True)
            #delete the mos script
            os.remove(scriptPathName)
            #delete the FMU
            """
            for mfmu in modelFMUs:
                newfmupath = os.path.join(os.path.splitext(mfmu)[0], os.path.basename(mfmu))
                os.remove(newfmupath)
            """

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
        if interface == "native":   #for the native interface
            for ob in objects:
                #create objects
                blockname = ob[0]
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
        fileobject = open(modelfile, "a")
        fileobject.write("equation\n")
        for cpl in couplings:
            sourceblock = cpl[0]
            sourceport = cpl[1].split(" / ")[0].strip()
            #sourceporttype = cpl[1].split(" / ")[1].strip()    #not needed for now
            sinkblock = cpl[2]
            sinkport = cpl[3].split(" / ")[0].strip()
            #sinkporttype = cpl[3].split(" / ")[1].strip()  #not needed for now
            #now write the port information
            if interface == "native":
                fileobject.write("  connect(" + sourceblock + "." + sourceport + ", " + sinkblock + "." + sinkport + ");\n")
            else:
                fileobject.write("  connect("+sourceblock+"1."+sourceport+", "+sinkblock+"1."+sinkport+");\n")
        #end statement
        fileobject.write("end "+modelname+";\n")
        fileobject.close()
        return 0