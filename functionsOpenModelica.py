# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import shutil
import subprocess
import platform

class functionsOpenModelica():

    #create the model FMUs as OpenModelica models (.mo)
    def importFMUs(self, modelFMUs):
        #set the system
        syst = platform.system()

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
                    if syst != "Windows":
                        mfmustr = mfmustr.replace("\\", "/")
                    impFMU.write('cd("'+os.path.splitext(mfmustr)[0]+'");\n')
                    impFMU.write('importFMU("'+os.path.basename(mfmu)+'");\n')
                    impFMU.write('\n')
            #run the script
            subprocess.call(["omc", scriptPathName])
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
                    #the basic models (which can be FMUs) are preconfigured, but start parameters for a block need to be written -> in syntax for OpenModelica
                    firstAttribute = True
                    atro = 0
                    while atro < len(ob[2]):
                        if "_start" in ob[2][atro][0]:
                            if not firstAttribute:  # if there are already attributes, a comma is needed
                                fileobject.write(",")
                            if firstAttribute:
                                firstAttribute = False
                            paramadapt = ob[2][atro][0].split("_start")
                            addBracket = False
                            if len(paramadapt) == 2:
                                ob[2][atro][0] = "(start".join(paramadapt)
                                addBracket = True
                            fileobject.write(ob[2][atro][0] + "=" + ob[2][atro][1])
                            if addBracket:
                                fileobject.write(")")
                        # next attribute
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
        #for FMI some portblocks need to be added -> store all information in lists first
        portblocklines = []
        couplinglines = []
        for cp in range(len(couplings)):
            cpl = couplings[cp]
            sourceblock = cpl[0]
            sourceport = cpl[1].split(" / ")[0].strip()
            sourceporttype = cpl[1].split(" / ")[1].strip()
            sinkblock = cpl[2]
            sinkport = cpl[3].split(" / ")[0].strip()
            #sinkporttype = cpl[3].split(" / ")[1].strip()  #not needed for now
            #now write the port information
            if interface == "native":
                couplinglines.append("  connect(" + sourceblock + "." + sourceport + ", " + sinkblock + "." + sinkport + ");\n")
            else:   #FMI interface
                #with signal ports append the coupling and append an Out block of the right type
                if sourceporttype.startswith("SP"):
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
                #physical ports have several variables in their connection: potential variables and flow variables
                # -> the type of the coupling indicates variables there are -> which are potential variables and which are flow variables
                # -> the value of potential variables can be put on a RealOutput block directly
                # -> the value of flow variables can be found out by inserting a type specific indicator, the output is then put on a RealOutput block
                #    therefore in every coupling a type specific indicator block is added
                # e.g. the type is PPEA = PhysicalPortElectricalAnalog -> the connector is of type "Pin" and has the potential variable u (voltage) and the flow variable i (current)
                #      -> add a RealOutput block in every connector and a currentSensor with a RealOutput block in every coupling
                #      -> Name of the RealOutput block for potential variables: Blockname_Portname_Variable_Out, Blockname and Portname from coupling, Variable found out with getComponents(...) function
                #      -> Name of the sensor block for flow variables: Blockname_Sensorname with the RealOutput block Blockname_Variable_Out, Blockname from coupling, Variable found out with getComponents(...) function
                elif sourceporttype.startswith("PP"):
                    if sourceporttype == "PPEA":
                        #Electrical Analog: the connector is of type "Pin" and has the potential variable u (voltage) and the flow variable i (current)
                        potVar = "v"
                        flowVar = "i"
                        #potential: voltage - append RealOutput blocks
                        portblocklines.append("  Modelica.Blocks.Interfaces.RealOutput "+sourceblock+"_"+sourceport+"_"+potVar+"_Out;\n")
                        portblocklines.append("  Modelica.Blocks.Interfaces.RealOutput "+sinkblock+"_"+sinkport+"_"+potVar+"_Out;\n")
                        #potential: voltage - append the couplings
                        couplinglines.append("  connect("+sourceblock+"1."+sourceport+"."+potVar+", "+sourceblock+"_"+sourceport+"_"+potVar+"_Out);\n")
                        couplinglines.append("  connect("+sinkblock+"1."+sinkport+"."+potVar+", "+sinkblock+"_"+sinkport+"_"+potVar+"_Out);\n")
                        #flow: current - append a current sensor block and its RealOutput port
                        portblocklines.append("  Modelica.Electrical.Analog.Sensors.CurrentSensor "+sourceblock+"1_currentSensor;\n")
                        portblocklines.append("  Modelica.Blocks.Interfaces.RealOutput "+sourceblock+"_"+flowVar+"_Out;\n")
                        #flow: current - append the couplings - now two couplings with the current sensor in between and the coupling to the RealOutput
                        ports = ["p", "n"]
                        sensorSourceport = ports[ports.index(sourceport) - 1]
                        sensorSinkport = sourceport
                        couplinglines.append("  connect("+sourceblock+"1."+sourceport+", "+sourceblock+"1_currentSensor."+sensorSourceport+");\n")
                        couplinglines.append("  connect("+sourceblock+"1_currentSensor."+sensorSinkport+", "+sinkblock+"1."+sinkport+");\n")
                        couplinglines.append("  connect("+sourceblock+"1_currentSensor."+flowVar+", "+sourceblock+"_"+flowVar+"_Out);\n")
                        #remove double entries in the portblocklines and couplinglines -> could happen if a component only has one port
                        portblocklines = list(set(portblocklines))
                        couplinglines = list(set(couplinglines))
                    if sourceporttype == "PPMT":
                        #Mechanics Translational: the connector is of type "Flange" and has the potential variable s (path) and the flow variable f (force)
                        potVar = "s"
                        flowVar = "f"
                        #potential: path - append RealOutput blocks
                        portblocklines.append("  Modelica.Blocks.Interfaces.RealOutput "+sourceblock+"_"+sourceport+"_"+potVar+"_Out;\n")
                        portblocklines.append("  Modelica.Blocks.Interfaces.RealOutput "+sinkblock+"_"+sinkport+"_"+potVar+"_Out;\n")
                        #potential: path - append the couplings
                        couplinglines.append("  connect("+sourceblock+"1."+sourceport+"."+potVar+", "+sourceblock+"_"+sourceport+"_"+potVar+"_Out);\n")
                        couplinglines.append("  connect("+sinkblock+"1."+sinkport+"."+potVar+", "+sinkblock+"_"+sinkport+"_"+potVar+"_Out);\n")
                        # if a component has an open end, it is not in the couplings -> add the output for potential variables and its coupling
                        # -> when a mechanics translational component has flange_a port, it has a flange_b port as well
                        # -> only check when the last coupling is set
                        ports = ["flange_a", "flange_b"]
                        if cp == len(couplings) - 1:
                            #get dictionary with the blocks and its ports
                            blockports = {}
                            for cplgs in couplings:
                                soblock = cplgs[0]
                                soport = cplgs[1].split(" / ")[0]
                                soportindic = blockports.get(soblock)
                                if soportindic is None:   #there is no entry of a port for the block already
                                    blockports.update({soblock: [soport]})
                                else:
                                    blockports.update({soblock: soportindic+[soport]})
                                siblock = cplgs[2]
                                siport = cplgs[3].split(" / ")[0]
                                siportindic = blockports.get(siblock)
                                if siportindic is None:   #there is no entry of a port for the block already
                                    blockports.update({siblock: [siport]})
                                else:
                                    blockports.update({siblock: siportindic+[siport]})
                            #now all blocks and ports are in the blockports dictionary -> go through them and add port if necessary
                            addports = []
                            for block in blockports:
                                por = blockports.get(block)
                                if len(por) == 1 and por[0] in ports:
                                    addport = ports[ports.index(por[0]) - 1]
                                    addports.append([block, addport])
                                    #blockports.update({block: por+[addport]})
                            #now add the additional ports and the coupling
                            for ap in addports:
                                portblocklines.append("  Modelica.Blocks.Interfaces.RealOutput "+ap[0]+"_"+ap[1]+"_"+potVar+"_Out;\n")
                                couplinglines.append("  connect("+ap[0]+"1."+ap[1]+"."+potVar+", "+ap[0]+"_"+ap[1]+"_"+potVar+"_Out);\n")
                        #flow: force - append a force sensor block and its RealOutput port
                        portblocklines.append("  Modelica.Mechanics.Translational.Sensors.ForceSensor "+sourceblock+"1_forceSensor;\n")
                        portblocklines.append("  Modelica.Blocks.Interfaces.RealOutput "+sourceblock+"_"+flowVar+"_Out;\n")
                        #flow: force - append the couplings - now two couplings with the force sensor in between and the coupling to the RealOutput
                        sensorSourceport = ports[ports.index(sourceport) - 1]
                        sensorSinkport = sourceport
                        couplinglines.append("  connect("+sourceblock+"1."+sourceport+", "+sourceblock+"1_forceSensor."+sensorSourceport+");\n")
                        couplinglines.append("  connect("+sourceblock+"1_forceSensor."+sensorSinkport+", "+sinkblock+"1."+sinkport+");\n")
                        couplinglines.append("  connect("+sourceblock+"1_forceSensor."+flowVar+", "+sourceblock+"_"+flowVar+"_Out);\n")
                        #remove double entries in the portblocklines and couplinglines -> could happen if a component only has one port
                        portblocklines = list(set(portblocklines))
                        couplinglines = list(set(couplinglines))

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