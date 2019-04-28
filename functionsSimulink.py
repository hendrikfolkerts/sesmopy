# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import re
import shutil

class functionsSimulink():

    #create the FMUs as Simulink models
    def importFMUs(self, objects, newmodelbasefolderpath):
        #for Simulink the FMUs do not need to be imported but the modelbasefile MB.slx containing the FMU block needs to be
        # copied in the modelbasefolder containing the configured FMUs
        pathOfThisFile = os.path.dirname(os.path.abspath(__file__))
        pathOfSimulinkFMU = os.path.join(pathOfThisFile, 'general_MB_files', 'Simulink_MB_FMU.slx')
        newPathOfSimulinkFMU = os.path.join(newmodelbasefolderpath, 'Simulink_MB_FMU.slx')
        shutil.copyfile(pathOfSimulinkFMU, newPathOfSimulinkFMU)
        newmodelbasefolderpathlist = [newmodelbasefolderpath]
        return newmodelbasefolderpathlist

    #create a textfile with instructions on how to build the system
    def initModel(self, modelfolderpathname, modelname):
        modelfile = os.path.join(modelfolderpathname, modelname)
        modelfile = modelfile + ".m"
        fileobject = open(modelfile, "w")
        fileobject.write("load_system('simulink');\n")
        fileobject.write("h = new_system('"+modelname+"');\n")
        fileobject.write("open_system(h);\n")
        fileobject.close()
        return modelfile

    #add the model components
    def addComponents(self, objects, modelfile, modelname, interface):
        fileobject = open(modelfile, "a")
        for ob in objects:
            #for the native interface blocks need to be added and block parameters need to be written
            if interface == "native":
                #create objects
                blockname = ob[0]
                type = ob[1]
                fileobject.write("h = add_block('" + type + "', '" + modelname + "/" + blockname + "');\n")
                #set block parameters
                for atro in ob[2]:
                    #for only one simulator
                    #fileobject.write("set(h, '" + atro[0] + "', '" + atro[1] + "');\n")
                    #just write as variable in workspace -> new, for use for several simulators, the MB has a function that reads these variables
                    fileobject.write(blockname + "_" + atro[0] + " = '" + atro[1] + "';\n")
            #for FMI the Simulink FMU block needs to get the FMU object (the file) as FMUName attribute,
            #a subsystem needs to be created (to get the portnames later) and the subsystem needs to be renamed
            #block parameters do not need to be written for the FMI interface, since the FMUs are preconfigured
            elif interface == "FMI":
                # For the FMI interface: the path to the FMU needs to be on the Matlab path
                if interface == "FMI":
                    path, file = os.path.split(ob[1])
                    path = path.replace("/", "\\")  # "/" to "\"
                    path = path.replace("\\\\", "\\")  # "\\" to "\"
                    blockname = ob[0]
                    fileobject.write("addpath('" + path + "');\n")
                    fileobject.write("h = add_block('Simulink_MB_FMU/FMU', '" + modelname + "/" + blockname + "');\n")
                    fileobject.write("set(h, 'FMUName', '" + blockname + ".fmu');\n")
                    fileobject.write("Simulink.BlockDiagram.createSubsystem(h);\n")
                    fileobject.write("set_param(gcbh, 'Name', '" + blockname + "');\n")
                    fileobject.write("rmpath('" + path + "');\n")
        fileobject.close()

    #add the connections between the model components
    def addConnections(self, couplings, modelfile, modelname, interface):
        fileobject = open(modelfile, "a")
        for cpl in couplings:
            sourceBlock = modelname + "/" + cpl[0]
            sinkBlock = modelname + "/" +cpl[2]
            fileobject.write("phFrom = get_param('"+sourceBlock+"','PortHandles');\n")
            fileobject.write("phTo = get_param('" + sinkBlock + "','PortHandles');\n")

            #old way -> not for several simulators
            """
            #Problem: ports are given as numbers in SES, but Simulink has two lists of numbers for normal ports and entity ports.
            #Simple solution: SES portnames in couplings have the form 'XN' for normal ports and 'CN' for entity ports (where N is an integer and X is an integer != "C", X is optional).
            sourcePort = cpl[1]
            sinkPort = cpl[3]
            try:
                if len(sourcePort) > 1 and sourcePort[0] != "C":
                    sourcePort = sourcePort[1:]
                if len(sinkPort) > 1 and sinkPort[0] != "C":
                    sinkPort = sinkPort[1:]
                #try to convert the port number to integer: normal port only consist of numbers, so they can be made to integers -> that way it can be distinguished between normal ports and entity ports
                int(sourcePort)
                int(sinkPort)
                fileobject.write("add_line('"+modelname+"', phFrom.Outport("+str(sourcePort)+"), phTo.Inport("+str(sinkPort)+"), 'autorouting', 'on');\n")   #make sure, that source and sink ports are strings when inserted
            except:
                try:
                    #the portname cannot be converted to an integer completely, but make sure, it is an entity port beginning with a 'C'
                    if sourcePort[0] == "C" and sinkPort[0] == "C":
                        soP = int(sourcePort[1:])
                        siP = int(sinkPort[1:])
                        fileobject.write("add_line('"+modelname+"', phFrom.RConn("+str(soP)+"), phTo.LConn("+str(siP)+"));\n")
                    else:
                        fileobject.close()
                        return 1
                except:
                    fileobject.close()
                    return 1
            """

            #new way -> get the portnumber to a portname -> portnames do not need to be integers
            sourcePort = cpl[1]
            sinkPort = cpl[3]
            try:
                #for the source -> out port
                fileobject.write("simBlockHandle = get_param('" + sourceBlock + "','Handle');\n")
                #fileobject.write("outportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'FollowLinks', 'on', 'SearchDepth', 2, 'BlockType', 'Outport');\n")
                fileobject.write("outportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'SearchDepth', 2, 'BlockType', 'Outport');\n")
                fileobject.write("outNames = get_param(outportHandles, 'Name');\n")
                fileobject.write("outPorts = get_param(outportHandles, 'Port');\n")
                #If there are several outNames, the values are placed in a cell array outPorts. -> Find the right number to the name.
                # For FMI the FMU is placed in a subsystem (see before), the portnames of the outports of the subsystem are Out1, Out2, ...
                # The portnames of the outports of the FMU is y if there is only one, or y1, y2, ... if there are several.
                # The outportname can be another letter than y.
                #If there is only one outName, the outPorts is a string with value '1'. It can be used directly.
                # For FMI: If there is only one outport, the name does not interest, since the port has number 1 anyway (as written above). -> Nothing to adapt.
                fileobject.write("if iscell(outNames)\n")
                if interface == "FMI":
                    portnum = re.findall(r'\d+', sourcePort)
                    if len(portnum) == 1:
                        portnum = portnum[0]    #take the only element
                    elif len(portnum) > 1:
                        portnum = portnum[-1]   #take the last element
                    else: # len(portnum) == 0 -> actually this case should not happen, since if the portname of the FMU has no number, it is a single port (and the else part of if iscell(outNames) is entered)
                        portnum = '1'
                    sourcePort = "Out" + portnum
                fileobject.write("idx = find(ismember(outNames, '" + sourcePort + "'));\n")
                fileobject.write("pno = str2num(outPorts{idx});\n")
                fileobject.write("else\n")
                fileobject.write("pno = str2num(outPorts);\n")
                fileobject.write("end\n")
                #for the sink -> in port
                fileobject.write("simBlockHandle = get_param('" + sinkBlock + "','Handle');\n")
                #fileobject.write("inportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'FollowLinks', 'on', 'SearchDepth', 2, 'BlockType', 'Inport');\n")
                fileobject.write("inportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'SearchDepth', 2, 'BlockType', 'Inport');\n")
                fileobject.write("inNames = get_param(inportHandles, 'Name');\n")
                fileobject.write("inPorts = get_param(inportHandles, 'Port');\n")
                #If there are several inNames, the values are placed in a cell array inPorts. -> Find the right number to the name.
                # For FMI the FMU is placed in a subsystem (see before), the portnames of the inports of the subsystem are In1, In2, ...
                # The portnames of the inports of the FMU is u if there is only one, or u1, u2, ... if there are several.
                # The inportname can be another letter than u.
                #If there is only one inName, the inPorts is a string with value '1'. It can be used directly.
                # For FMI: If there is only one inport, the name does not interest, since the port has number 1 anyway (as written above). -> Nothing to adapt.
                fileobject.write("if iscell(inNames)\n")
                if interface == "FMI":
                    portnum = re.findall(r'\d+', sinkPort)
                    if len(portnum) == 1:
                        portnum = portnum[0]    #take the only element
                    elif len(portnum) > 1:
                        portnum = portnum[-1]   #take the last element
                    else: # len(portnum) == 0 -> actually this case should not happen, since if the portname of the FMU has no number, it is a single port (and the else part of if iscell(outNames) is entered)
                        portnum = '1'
                    sinkPort = "In" + portnum
                fileobject.write("idx = find(ismember(inNames, '" + sinkPort + "'));\n")
                fileobject.write("pni = str2num(inPorts{idx});\n")
                fileobject.write("else\n")
                fileobject.write("pni = str2num(inPorts);\n")
                fileobject.write("end\n")
                #now draw the line
                fileobject.write("add_line('" + modelname + "', phFrom.Outport(pno), phTo.Inport(pni), 'autorouting', 'on');\n")
            except:
                fileobject.close()
                return 1

        fileobject.close()
        return 0