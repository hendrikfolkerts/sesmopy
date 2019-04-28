# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import shutil
import ast
import xml.etree.ElementTree as ET
from copy import deepcopy
import zipfile

from PyQt5.QtCore import (QCoreApplication, QObject, QRunnable, QThread, QThreadPool, pyqtSignal, pyqtSlot)

from functionsSimulink import *
from functionsOpenModelica import *
from functionsDymola import *

class modelBuilder(QObject):

    #signals
    statusUpdate = pyqtSignal(str)  #this signal takes a string to indicate progress
    finished = pyqtSignal(int)  #this signal takes an integer to indicate the error or show success

    def __init__(self):
        super(modelBuilder, self).__init__()
        #these variables are empty on initialization of the modelBuilder class, the values are set from the main thread
        self.objects = []
        self.nodesWithoutMbAttribute = []
        self.couplings = []
        self.modelname = ""
        self.modelfolderpathname = ""
        self.fpesfilepath = ""

    #def build(self, objects, nodesWithoutMbAttribute, couplings, modelname, modelfolderpathname, fpesfilepath):    # -> now build is called without parameters, the necessary variables (given here as parameters of the build function) are set from the main thread
    def build(self):

        #delete if existing and create the folder for the models
        try:
            if os.path.exists(self.modelfolderpathname):
                shutil.rmtree(self.modelfolderpathname)
            os.makedirs(self.modelfolderpathname)
        except:
            self.finished.emit(7)
            return 7

        self.statusUpdate.emit("Find variations.")



        ################################################################################################################
        #get the attributes of the nodes without MB-Attribute from the nodelist (they may be necessary for the simulator configuration)
        #the FPES defines the attributes necessary for the simulation run (defining the simulation method) and the attributes to vary
        simulator = "not defined"   # Simulink or OpenModelica or Dymola
        interface = "native"        # native or FMI
        paramvary = []
        for nd in self.nodesWithoutMbAttribute:
            att = self.nodesWithoutMbAttribute.get(nd)
            for at in att:
                if at[0] == "SIMULATOR":
                    simulator = at[1]
                elif at[0] == "INTERFACE":
                    interface = at[1]
                elif "PARAMVARY" in at[0]:
                    paramvary.append(at[1])

        #create all models for this FPES as list of objects and their parameterization: vary the parameterization and store the variants of building the model in the following variables
        #every new parameterization gets a new name, so there is no name conflict
        #which parameters of which block to vary is encoded in the SES/FPES
        modelnames = []
        modelnamesParameters = [] #only for information in the config file: varying parameterization of a modelname
        objectsvariations = []
        #the parameters to vary need to be vectors with the equal number of elements:
        # the first element of the first parameter along with the first element of the second parameter is used for the first model,
        # the second element of the first parameter along with the second element of the second parameter is used for the second model...

        #model number v
        v=0
        varyListIncomplete = True
        while varyListIncomplete:
            parameterVaryDict = {}
            parametervalue = []
            objectscopy = deepcopy(self.objects)
            for pv in paramvary:
                objectnameparameter = pv.split("=")[0].split(".")[0]
                objectparametername = pv.split("=")[0].split(".")[1]
                try:
                    parametervalue = ast.literal_eval(pv.split("=")[1])
                except:
                    print("The parametervalue to vary " + pv + " could not be interpreted as a Python variable.")
                    self.finished.emit(4)
                    return 4

                #if the objectnameparameter is already filled, append it
                parameterlist = parameterVaryDict.get(objectnameparameter)
                if not parameterlist:
                    parameterVaryDict.update({objectnameparameter: [[objectparametername, str(parametervalue[v])]]})
                else:
                    parameterlist.append([objectparametername, str(parametervalue[v])])
                    parameterVaryDict.update({objectnameparameter: parameterlist})

            #create the modelname and the objects for this variation, parameterVaryDict has all information
            keylist = list(parameterVaryDict.keys())
            paramstring = ""
            for key in keylist:
                params = parameterVaryDict.get(key)
                paramstring = paramstring + key + ": "
                for param in params:
                    paramstring = paramstring + '='.join(param) + " "
                paramstring = paramstring[:-1] + " "
            paramstring = paramstring[:-1]

            #create a new modelname indicating the parameter variation
            #modelnamevary = paramstring.replace(";", "_").replace(",", "_").replace(" ", "").replace(":", "_").replace("=", "e")
            #instead of coding the variation in the modelname (see line above) just number the model
            modelnamevary = str(v+1)
            newmodelname = (simulator + "_" + self.modelname + "_" + modelnamevary).replace(".", "d").replace("-", "m")	#OpenModelica does not accept a dot or a minus in a filename and OpenModelica modelnames are not allowed to begin with a number -> just always write the simulator as first part of the name
            modelnames.append(newmodelname)
            if paramstring != "":
                modelnamesParameters.append(newmodelname + " with varying parameterization: " + paramstring)

            #update the objects with the current variation
            for ob in objectscopy:
                paramsForObject = parameterVaryDict.get(ob[0])  #get the new parameterlist for the object with parameters to vary
                if paramsForObject: #if the object has parameters to vary
                    currentObjectParams = ob[2]
                    #the parameters the object currently has are in currentObjectParams, some of which shall be replaced by the parameters in paramsForObject
                    for coPar in range(len(currentObjectParams)):   #go through the current parameterlist of the object
                        for pfObj in range(len(paramsForObject)):
                            if paramsForObject[pfObj][0] == currentObjectParams[coPar][0]:
                                currentObjectParams[coPar][1] =  paramsForObject[pfObj][1]

            #the object is updated with the current parameter variation, insert the object
            objectsvariations.append(objectscopy)

           #next model, if there are still parameters to vary
            v += 1
            if v >= len(parametervalue):
                varyListIncomplete = False
        ################################################################################################################



        #modelnames is a list with the names of the models
        #objectsvariations is a list with the links to the blocks and their parameterization
        #modelnames and objectsvariations correspond to each other - e.g. the first element in modelnames (a name of a model) has the blocks and their configurations as listed in objectsvariations
        #the same applies for all further elements in the lists

        #Create an object of the classes with the functions for the respective simulator
        if simulator == "Simulink":
            simulatorFunObj = functionsSimulink
        elif simulator == "OpenModelica":
            simulatorFunObj = functionsOpenModelica
        elif simulator == "Dymola":
            simulatorFunObj = functionsDymola
        else:
            self.finished.emit(1)
            return 1

        #For native modelbuilding: set the modelbasefilespathname (with correct ending) and copy the modelbasefiles and accompanying files in the simulationfolder
        newmodelbasefilespathname = []
        if interface == "native":
            self.statusUpdate.emit("Native modelbuilding: Copy modelbase.")
            # get the path and names of the modelbases -> they shall lie in the same directory as the FPES .jsonsestree file and the fileending depends on the simulator
            mblinks = []
            for ob in self.objects:  # get the filenames of the modelbases from the mb-attributes
                mblinks.append(ob[1])
            modelbaselinkspathname = [os.path.join(self.fpesfilepath, os.path.split(mblink)[0]) for mblink in mblinks]  # the modelbaselinkspathname has no ending yet
            modelbaselinkspathname = list(set(modelbaselinkspathname))
            if simulator == "Simulink":
                simulatorFunObj = functionsSimulink
                modelbasefilespathname = [mbfilename + ".slx" for mbfilename in modelbaselinkspathname]
            elif simulator == "OpenModelica":
                simulatorFunObj = functionsOpenModelica
                modelbasefilespathname = [mbfilename + ".mo" for mbfilename in modelbaselinkspathname]
            elif simulator == "Dymola":
                simulatorFunObj = functionsDymola
                modelbasefilespathname = [mbfilename + ".mo" for mbfilename in modelbaselinkspathname]
            else:
                self.finished.emit(1)
                return 1

            # copy the modelbase file(s) in the newly created folder, in which the models will be created
            for modelbasefilepathname in modelbasefilespathname:
                modelbasefilename = os.path.basename(modelbasefilepathname)
                newmodelbasefilepathname = os.path.join(self.modelfolderpathname, modelbasefilename)
                try:
                    shutil.copyfile(modelbasefilepathname, newmodelbasefilepathname)
                    newmodelbasefilespathname.append(newmodelbasefilepathname)
                except:
                    self.finished.emit(3)
                    return 3
                # copy other files needed for the modelbase (e.g. .m-files for MATLAB) in the modelfolder
                for hfile in os.listdir(os.path.split(modelbasefilepathname)[0]):
                    if hfile.endswith(".m"):
                        hfilepathname = os.path.join(os.path.split(modelbasefilepathname)[0], hfile)
                        newhfilepathname = os.path.join(self.modelfolderpathname, hfile)
                        try:
                            shutil.copyfile(hfilepathname, newhfilepathname)
                        except:
                            self.finished.emit(3)
                            return 3

            self.statusUpdate.emit("Native modelbuilding: Modelbase copied!")

        #For modelbuilding using FMI an OpenModelica MB is created by the user and the basic models (=blocks) in this OpenModelica MB are configured according to the information in the FPES in the modelbuilder.
        #Each block needed in the model is copied from the OpenModelica MB, the name and the parameters are updated to the desired block defined in the FPES,
        # and finally an FMU is built from this configured block (so a preconfigured FMU modelbase is created).
        #FMUs are zip files which have an xml file in which the interface is defined (FMI) and the parameters of the block are stored.
        # -> no configuration of the FMUs in the simulator, because once imported in a simulator they need simulator specific syntax for configuration again
        elif interface == "FMI":
            #Create configured FMUs from the objects (with their varying configurations) by going through each object of a variation, find its type in the respective modelbase,
            # copy the code to create an OpenModelica block (=basic model) with the name of the object, configure it and, finally, create an FMU of the configured block.
            #For each variation the FMUs are put in an own folder in the modelfolder (the folder where the model is created).
            #only continue if there are objects
            if len(objectsvariations) > 0:
                #go through each variation
                #the list modelnames fits to the objectsvariations list -> first object in modelnames has the objects and their configuration like in objectsvariations etc.
                # -> so these are the steps to create a preconfigured modelbase for each variation
                for i in range(len(modelnames)):
                    newblocklinkpathfiles = []
                    newmodelbasefolderpath = ""
                    #in variation i go through all objects
                    self.statusUpdate.emit("FMI modelbuilding: Extract and configure OpenModelica basic models (variation " + str(i + 1) + ").")
                    for obj in objectsvariations[i]:
                        mblinkpathname = os.path.join(self.fpesfilepath, os.path.split(obj[1])[0]) + ".mo"     #the MB in which this type of object can be found (this information is in obj[1])
                        #load the file containing the MB and store the parts defining the block in a new file
                        try:
                            mblines = []
                            startlinenumber = 0
                            endlinenumber = 0
                            #read the MB file
                            with open(mblinkpathname, 'r') as mbfile:
                                for line in mbfile:
                                    mblines.append(line)
                            #find the block
                            blocktype = os.path.split(obj[1])[1]
                            blockname = obj[0]
                            for l in range(len(mblines)):
                                if "block " + blocktype in mblines[l]:
                                    startlinenumber = l
                                if "end " + blocktype + ";" in mblines[l]:
                                    endlinenumber = l + 1

                            #create new file for the block and configure it -> therefore some directories need to be set first
                            modelbasefolder = os.path.split(os.path.dirname(obj[1]))[-1]  # -> a folder with this name as first part shall be created for the modelbase
                            newmodelbasefolder = modelbasefolder + "_" + modelnames[i]  # set a name for a variation (model configuration) specific modelbase
                            newmodelbasefolderpath = os.path.join(self.fpesfilepath, self.modelfolderpathname, newmodelbasefolder)  # as before, now including the path
                            newblocklinkpath = os.path.join(newmodelbasefolderpath, obj[0]) # as before, now including the object
                            if not os.path.exists(newmodelbasefolderpath):  # create the folder for the variation specific modelbase -> otherwise shutil.copyfile exits with error
                                os.makedirs(newmodelbasefolderpath)
                            with open(newblocklinkpath + ".mo", 'w') as blockfile:  #create the new file
                                lineno = startlinenumber
                                while lineno < endlinenumber:
                                    if lineno == startlinenumber:
                                        blockfile.write("block " + blockname + "\n")
                                    elif lineno + 1 == endlinenumber:
                                        blockfile.write("end " + blockname + ";")
                                    else:
                                        #take the line and find out whether a configuration needs to be set in this line
                                        linetext = mblines[lineno]  #take the line

                                        #if the block extends a library block: add configuration at the end
                                        if "extends " in linetext and "." + blocktype in linetext:
                                            linetext = linetext[:-2] + "("
                                            atro = 0
                                            while atro < len(obj[2]):
                                                # now insert the parameter in the text
                                                linetext = linetext + obj[2][atro][0] + "=" + obj[2][atro][1]
                                                # if there are more attributes, a comma is needed
                                                if atro < len(obj[2]) - 1:
                                                    linetext = linetext + ","
                                                # next attribute
                                                atro += 1
                                            linetext = linetext + ");\n"
                                        #if the block is in sourcecode: find parameter to set value
                                        elif "parameter " in linetext:
                                            lineelements = linetext.split()
                                            for le in range(len(lineelements)):
                                                if "=" in lineelements[le]:  #in the lineelement with "=" is the parameter
                                                    equalsplit = lineelements[le].split("=") #equalsplit[0] is the parametername, equalsplit[1] is the parametervalue
                                                    param = equalsplit[0].split("[")[0]
                                                    atro = 0
                                                    while atro < len(obj[2]):
                                                        if obj[2][atro][0] == param:
                                                            equalsplit[1] = obj[2][atro][1]
                                                        atro += 1
                                                    lineelements[le] = '='.join(equalsplit)
                                            linetext = ' '.join(lineelements)

                                        #write the (maybe updated) line back
                                        blockfile.write(linetext)   #finally write the text of the line
                                    lineno = lineno + 1
                            newblocklinkpathfiles.append(newblocklinkpath + ".mo")

                        except:
                            self.finished.emit(3)
                            return 3

                    #export the OpenModelica configured basic models as FMUs
                    exportFMUScript = os.path.join(newmodelbasefolderpath, "exportFMUs.mos")
                    with open(exportFMUScript, 'w') as expfile:
                        # replace the folderseparators to the OpenModelica type "\\"
                        newmodelbasefolderpathOm = newmodelbasefolderpath.replace("/", "\\\\")  # "/" to "\\"
                        newmodelbasefolderpathOm = newmodelbasefolderpathOm.replace("\\", "\\\\")  # "\" to "\\"
                        newmodelbasefolderpathOm = newmodelbasefolderpathOm.replace("\\\\\\", "\\")  # "\\\" to "\"
                        expfile.write('cd("' + newmodelbasefolderpathOm + '");\n')
                        expfile.write('loadModel(Modelica);\n')
                        expfile.write('getErrorString();\n')
                        for blpf in newblocklinkpathfiles:
                            expfile.write('loadFile("' + os.path.split(blpf)[1] + '");\n')
                            expfile.write('getErrorString();\n')
                            expfile.write('translateModelFMU(' + os.path.splitext(os.path.split(blpf)[1])[0] + ');\n')
                            expfile.write('getErrorString();\n')
                    # -> try to execute the created script for exporting the configured basic models as FMUs with OpenModelica
                    try:
                        subprocess.check_output(["omc", "--version"], shell=True)
                    except:
                        print("The omc.exe used for executing OpenModelica scripts can not be found.")
                        print("For Windows, please make sure, that the bin folder of OpenModelica is on the path of the user / system and restart this program.")
                        print("For Linux, please make sure, that the OpenModelica command 'omc' is startable from the Shell. Otherwise place a symbolic link to the omc executable with the name 'omc' in the /usr/bin folder.\n")
                        self.finished.emit(6)
                        return 6
                    #if OpenModelica would not have been found, the program would have returned (and this code would not have been reached)
                    self.statusUpdate.emit("FMI modelbuilding: Create FMUs from preconfigured OpenModelica basic models (variation " + str(i + 1) + ").")
                    subprocess.check_output(["omc", exportFMUScript], shell=True)

                    #delete all files except the FMUs
                    for filename in os.listdir(newmodelbasefolderpath):  # list the files in the directory
                        #delete the file
                        if not filename.endswith('.fmu'):
                            try:
                                os.remove(os.path.join(newmodelbasefolderpath, filename))
                            except:
                                pass

                    #update the information in objectsvariations -> whole path to an FMU
                    for obj in objectsvariations[i]:
                        obj[1] = os.path.join(newmodelbasefolderpath, obj[0]) + ".fmu"

                    #import the FMU in the used simulator (simulator specific) and return a list with the links to the imported files
                    #This only applies for OpenModelica and Dymola. OpenModelica and Dymola import the FMU in the modelbuilder and create
                    # a .mo file to be used with the respective program, whereas Simulink imports the FMU only on execution (and not in the modelbuilder).
                    #Try to find the simulator to use on the disk.
                    openModelicaDymolaFound = True
                    if simulator == "OpenModelica":
                        pass    #this was checked before because FMUs needed to be created using OpenModelica
                    elif simulator == "Dymola":
                        # subprocess.check_output(["dymola", "-nowindow"], shell=True)
                        print("Currently it can not be checked automatically whether Dymola is installed.")
                        print("In case there are problems during execution:")
                        print("For Windows, please make sure, that the bin or bin64 folder of Dymola is on the path of the user / system and restart this program.")
                        print("For Linux, please make sure, that Dymola can be started with the command 'dymola' from the Shell. Otherwise place a symbolic link to the Dymola executable with the name 'dymola' in the /usr/bin folder.\n")
                    if openModelicaDymolaFound:
                        self.statusUpdate.emit("FMI modelbuilding: Import FMUs of variation " + str(i+1) + " for the chosen simulator.")
                        newmodelbasefilespathname.append(simulatorFunObj.importFMUs(self, objectsvariations[i], newmodelbasefolderpath))
                    else:
                        self.finished.emit(5)
                        return 5

                    self.statusUpdate.emit("FMI modelbuilding: FMUs for variation " +str(i+1)+" ("+modelnames[i]+") imported!")
        else:
            self.finished.emit(1)
            return 1

        #build the models
        portsOk = []
        modelfiles = []
        for i in range(len(modelnames)):
            modelfile = simulatorFunObj.initModel(self, self.modelfolderpathname, modelnames[i])
            simulatorFunObj.addComponents(self, objectsvariations[i], modelfile, modelnames[i], interface)
            pOk = simulatorFunObj.addConnections(self, self.couplings, modelfile, modelnames[i], interface)
            portsOk.append(pOk)
            modelfiles.append(modelfile)
        allPortsOk = sum(portsOk)

        self.statusUpdate.emit("Models built!")

        #if all models are ok, write a configuration file
        if allPortsOk == 0:
            conffile = os.path.join(self.modelfolderpathname, "config.txt")
            with open(conffile, "w") as fileobject:	#it is closed after finishing the block, even if an exception is raised
                fileobject.write("Configuration file for model execution with SESEuPy. DO NOT EDIT THIS FILE MANUALLY!\n")
                for i in range(len(modelnamesParameters)):
                    fileobject.write("MODELNAMEPARAM: " + modelnamesParameters[i]+"\n")
                for i in range(len(modelnames)):
                    fileobject.write("MODEL: "+modelfiles[i].replace("\\", "/")+"\n")
                fileobject.write("SIMULATOR: "+simulator+"\n")
                fileobject.write("INTERFACE: " + interface + "\n")
                if interface == "native":
                    for newmodelbasefilepathname in newmodelbasefilespathname:
                        fileobject.write("MODELBASE: "+newmodelbasefilepathname.replace("\\", "/")+"\n")
                if interface == "FMI":
                    for varnum in range(len(modelnames)):
                        for newmodelbasefilepathname in newmodelbasefilespathname[varnum]:
                            fileobject.write("MODELBASE: (" + modelfiles[varnum].replace("\\", "/") + ") " + newmodelbasefilepathname.replace("\\", "/") + "\n")

            self.finished.emit(0)
            return 0
        elif allPortsOk > 0:
            self.finished.emit(2)
            return 2
