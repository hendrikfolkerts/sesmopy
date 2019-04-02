# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os

class functionsSimulink():

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
    def addComponents(self, objects, modelfile, modelname):
        fileobject = open(modelfile, "a")
        for ob in objects:
            #create objects
            blockname = ob[0]
            type = ob[1]
            fileobject.write("h = add_block('"+type+"', '"+modelname+"/"+blockname+"');\n")
            #set block parameters
            for atro in ob[2]:
                fileobject.write("set(h, '" + atro[0] + "', '" + atro[1] + "');\n")
        fileobject.close()

    #add the connections between the model components
    def addConnections(self, couplings, modelfile, modelname):
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

            #new way -> get the portnumber to a portname -> portnames do not need to be integres
            sourcePort = cpl[1]
            sinkPort = cpl[3]
            try:
                #for the source -> out port
                fileobject.write("simBlockHandle = get_param('" + sourceBlock + "','Handle');\n")
                fileobject.write("outportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'FollowLinks', 'on', 'SearchDepth', 2, 'BlockType', 'Outport');\n")
                fileobject.write("outNames = get_param(outportHandles, 'Name');\n")
                fileobject.write("outPorts = get_param(outportHandles, 'Port');\n")
                fileobject.write("if iscell(outNames)\n")
                fileobject.write("idx = find(ismember(outNames, '" + sourcePort + "'));\n")
                fileobject.write("pno = str2num(outPorts{idx});\n")
                fileobject.write("else\n")
                fileobject.write("pno = str2num(outPorts);\n")
                fileobject.write("end\n")
                #for the sink -> in port
                fileobject.write("simBlockHandle = get_param('" + sinkBlock + "','Handle');\n")
                fileobject.write("inportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'FollowLinks', 'on', 'SearchDepth', 2, 'BlockType', 'Inport');\n")
                fileobject.write("inNames = get_param(inportHandles, 'Name');\n")
                fileobject.write("inPorts = get_param(inportHandles, 'Port');\n")
                fileobject.write("if iscell(inNames)\n")
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