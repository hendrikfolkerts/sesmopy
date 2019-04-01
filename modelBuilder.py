# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
from shutil import copyfile
import ast
from copy import deepcopy
from functionsSimulink import *
from functionsOpenModelicaDymola import *

class modelBuilder():

    def build(self, objects, nodesWithoutMbAttribute, couplings, modelname, modelfolderpathname, fpesfilepath, mblinks):
        #create the folder for the models
        if not os.path.exists(modelfolderpathname):
            os.makedirs(modelfolderpathname)

        #the FPES defines the attributes necessary for the simulation run (defining the simulation method) and the attributes to vary
        simulator = "not defined"
        interface = "native"
        paramvary = []
        for nd in nodesWithoutMbAttribute:
            att = nodesWithoutMbAttribute.get(nd)
            for at in att:
                if at[0] == "SIMULATOR":
                    simulator = at[1]
                elif at[0] == "INTERFACE":
                    interface = at[1]
                elif "PARAMVARY" in at[0]:
                    paramvary.append(at[1])

        #create objects of the classes with the functions for the respective simulator
        #and set the modelbasefilespathname
        if simulator == "Simulink":
            simulatorFunObj = functionsSimulink
            if interface == "native":
                modelbaselinkspathname = [os.path.join(fpesfilepath, os.path.split(mblink)[0].replace("/", "")) for mblink in mblinks]
                modelbaselinkspathname = list(set(modelbaselinkspathname))
                modelbasefilespathname = [mbfilename + ".slx" for mbfilename in modelbaselinkspathname]
            elif interface == "FMI":
                modelbasefilespathname = [mbfilename + ".fmu" for mbfilename in modelbaselinkspathname]
            else:
                return 1
        elif simulator == "OpenModelica" or simulator == "Dymola":
            simulatorFunObj = functionsOpenModelicaDymola
            if interface == "native":
                modelbaselinkspathname = [os.path.join(fpesfilepath, os.path.split(mblink)[0].replace("/", "")) for mblink in mblinks]
                modelbaselinkspathname = list(set(modelbaselinkspathname))
                modelbasefilespathname = [mbfilename + ".mo" for mbfilename in modelbaselinkspathname]
            elif interface == "FMI":
                modelbasefilespathname = [mbfilename + ".fmu" for mbfilename in modelbasefilespathname]
            else:
                return 1
        else:
            return 1

        #copy the modelbase file in the newly created folder, in which the models will be created
        newmodelbasefilespathname = []
        for modelbasefilepathname in modelbasefilespathname:
            modelbasefilename = os.path.basename(modelbasefilepathname)
            newmodelbasefilepathname = os.path.join(modelfolderpathname, modelbasefilename)
            try:
                copyfile(modelbasefilepathname, newmodelbasefilepathname)
                newmodelbasefilespathname.append(newmodelbasefilepathname)
            except:
                return 3

        #for the FMI configure the basic models
        #FMUs are zip files which have an xml file in which the parameters of the block are stored -> update the parameters in the xml with the block parameters
        #therefore unzip the FMU file, update the XML and zip it again with the fileextension .fmu
        if interface == "FMI":
            pass




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
            objectscopy = deepcopy(objects)
            for pv in paramvary:
                objectnameparameter = pv.split("=")[0].split(".")[0]
                objectparametername = pv.split("=")[0].split(".")[1]
                try:
                    parametervalue = ast.literal_eval(pv.split("=")[1])
                except:
                    print("The parametervalue to vary " + pv + " could not be interpreted as a Python variable.")
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
            newmodelname = (simulator + "_" + modelname + "_" + modelnamevary).replace(".", "d").replace("-", "m")	#OpenModelica does not accept a dot or a minus in a filename and OpenModelica modelnames are not allowed to begin with a number -> just always write the simulator as first part of the name
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





        #build the models
        portsOk = []
        modelfiles = []
        for i in range(len(modelnames)):
            modelfile = simulatorFunObj.initModel(self, modelfolderpathname, modelnames[i])
            simulatorFunObj.addComponents(self, objectsvariations[i], modelfile, modelnames[i])
            pOk = simulatorFunObj.addConnections(self, couplings, modelfile, modelnames[i])
            portsOk.append(pOk)
            modelfiles.append(modelfile)
        allPortsOk = sum(portsOk)

        #if all models are ok, write a configuration file
        if allPortsOk == 0:
            conffile = os.path.join(modelfolderpathname, "config.txt")
            with open(conffile, "w") as fileobject:	#it is closed after finishing the block, even if an exception is raised
                fileobject.write("Configuration file for model execution with SESEuPy. DO NOT EDIT THIS FILE MANUALLY!\n")
                for i in range(len(modelnamesParameters)):
                    fileobject.write("MODELNAMEPARAM: " + modelnamesParameters[i]+"\n")
                for i in range(len(modelnames)):
                    fileobject.write("MODEL: "+modelfiles[i].replace("\\", "/")+"\n")
                fileobject.write("SIMULATOR: "+simulator+"\n")
                fileobject.write("INTERFACE: " + interface + "\n")
                for newmodelbasefilepathname in newmodelbasefilespathname:
                    fileobject.write("MODELBASE: "+newmodelbasefilepathname.replace("\\", "/")+"\n")
            return 0
        elif allPortsOk > 0:
            return 2