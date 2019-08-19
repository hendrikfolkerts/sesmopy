# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os
import re
import shutil

class functionsSimulink():

    #create the  FMUs as Simulink models
    def importFMUs(self, modelFMUs):
        #for Simulink the FMUs do not need to be imported but the modelbasefile MB.slx containing the FMU block needs to be
        # copied in the modelbasefolder containing the configured FMUs
        pathOfThisFile = os.path.dirname(os.path.abspath(__file__))
        pathOfSimulinkFMU = os.path.join(pathOfThisFile, 'general_MB_files', 'Simulink_MB_FMU.slx')
        if len(modelFMUs) > 0:
            newPathOfSimulinkFMU = os.path.join(os.path.split(modelFMUs[0])[0], 'Simulink_MB_FMU.slx')
            shutil.copyfile(pathOfSimulinkFMU, newPathOfSimulinkFMU)
        return modelFMUs

    #create a textfile with instructions on how to build the system
    def initModel(self, modelfolderpathname, modelname, additionalFiles):
        modelfile = os.path.join(modelfolderpathname, modelname)
        modelfile = modelfile + ".m"
        fileobject = open(modelfile, "w")
        fileobject.write("load_system('simulink');\n")
        fileobject.write("h = new_system('"+modelname+"');\n")
        fileobject.write("open_system(h);\n")
        fileobject.write("\n")
        fileobject.write("try\n")
        fileobject.write("\n")
        #write the parameter config given in the setParametersXXX.m files into the InitFcn
        if len(additionalFiles) > 0:
            fileobject.write("initText = '';    %text for the InitFcn of the model\n")
            for addFile in additionalFiles:
                if addFile.endswith(".m"):
                    fileobject.write("initText =[initText, fileread('" + addFile + "'), newline, newline];    %read additional files\n")
            fileobject.write("set_param(h, 'InitFcn', initText);    %write the contents of additional files in the InitFcn of the model, the InitFcn shall set the parameterization of the blocks\n")
        fileobject.close()
        return modelfile

    #add the model components
    def addComponents(self, objects, modelfile, modelname, interface):
        fileobject = open(modelfile, "a")
        #for the native interface: blocks need to be added and block parameters need to be written
        if interface == "native":
            for ob in objects:
                fileobject.write("\n%One block\n")
                #create objects
                blockname = ob[0].replace("-", "_")  #Matlab names may not have a -
                type = ob[1]
                fileobject.write("h = add_block('" + type + "', '" + modelname + "/" + blockname + "');    %add the Simulink block from the MB and rename\n")
                #set block parameters
                for atro in ob[2]:
                    #for only one simulator
                    #fileobject.write("set(h, '" + atro[0] + "', '" + atro[1] + "');\n")
                    #just write as variable in workspace -> new, for use for several simulators, the MB has a function that reads and sets these variables
                    fileobject.write(blockname + "_" + atro[0] + " = '" + atro[1] + "';    %variables for the block -> applied to the block in the InitFcn\n")
        #for FMI the Simulink FMU block needs to get the FMU model object (the file) as FMUName attribute,
        #a subsystem needs to be created (to get the portnames later) and the subsystem needs to be renamed
        #block parameters do not need to be written for the FMI interface, since the FMU model is preconfigured
        #for the FMI interface: the path to the FMU needs to be on the Matlab path
        if interface == "FMI":  # for the FMI interface: in order to find the portnames of the imported FMU, the modelDescription.xml of the unzipped FMU needs to be parsed -> variable and import needs to be set
            path = os.path.split(modelfile)[0]
            blockname = objects #for FMI the variable objects is just the current FMU modelname
            fileobject.write("import javax.xml.xpath.*    %import the Java XPath classes for FMI -> needed to parse an XML with XPath\n")
            fileobject.write("\n")
            fileobject.write("addpath('" + path + "');    %add the path of the FMU -> otherwise Matlab has no rights to unpack/read the FMU\n")
            fileobject.write("h = add_block('Simulink_MB_FMU/FMU', '" + modelname + "/ModelFMU');    %add Simulink FMU block from an MB containing only the Simulink FMU block\n")
            fileobject.write("set(h, 'FMUName', '" + os.path.basename(objects) + "');    %set the FMU to use in the Simulink FMU block -> the FMU is imported and unpacked\n")
            fileobject.write("Simulink.BlockDiagram.createSubsystem(h);    %create a subsystem in order to get named ports\n")
            fileobject.write("set_param(gcbh, 'Name', '" + modelname + "');    %set the blockname of the subsystem\n")
            fileobject.write("%get the new folder (where the FMU was unpacked)\n")
            fileobject.write("foldersFilesInfo = dir(fullfile('.', 'slprj', '_fmu'));\n")
            fileobject.write("dirFlags = [foldersFilesInfo.isdir];\n")
            fileobject.write("currentFMUfolders = extractfield(foldersFilesInfo(dirFlags),'name');\n")
            fileobject.write("newFMUfolderstring = '';    %with the loop make sure it is the right folder\n")
            fileobject.write("for i = 1:length(currentFMUfolders)\n")
            fileobject.write("    subDirFoldersFilesInfo = dir(fullfile('.', 'slprj', '_fmu', currentFMUfolders{i}));\n")
            fileobject.write("    subDirFlags = [subDirFoldersFilesInfo.isdir];\n")
            fileobject.write("    subDirFoldernames = extractfield(subDirFoldersFilesInfo(subDirFlags),'name');\n")
            fileobject.write("    if any(strcmp(subDirFoldernames, '" + os.path.splitext(os.path.basename(objects))[0] + "'))\n")
            fileobject.write("        newFMUfolderstring = currentFMUfolders{i};\n")
            fileobject.write("        break;\n")
            fileobject.write("    end\n")
            fileobject.write("end\n")
            fileobject.write("%construct the DOM of modelDescription.xml of the unpacked FMU\n")
            fileobject.write("[curScrFilepath, curScrName, curScrExt] = fileparts(mfilename('fullpath'));\n")
            fileobject.write("xDoc = xmlread(fullfile(curScrFilepath, 'slprj', '_fmu', newFMUfolderstring, '" + os.path.splitext(os.path.basename(objects))[0] + "', 'modelDescription.xml'));\n")
            fileobject.write("%create an XPath expression\n")
            fileobject.write("factory = XPathFactory.newInstance;\n")
            fileobject.write("xpath = factory.newXPath;\n")
            fileobject.write("%1. search for outputs order -> the modelDescription.xml has a dedicated part under ModelStructure where all outputs have to be listed -> page 58 in the FMI 2.0 specification document\n")
            fileobject.write("expression = xpath.compile('//ModelStructure/Outputs');\n")
            fileobject.write("%apply the expression to the DOM\n")
            fileobject.write("outputsNode = expression.evaluate(xDoc,XPathConstants.NODESET);\n")
            fileobject.write("outNodes = outputsNode.item(0).getChildNodes;\n")
            fileobject.write("%iterate through the nodes that are returned\n")
            fileobject.write("outSignalIndices = [];\n")
            fileobject.write("for i = 1:outNodes.getLength\n")
            fileobject.write("    node = outNodes.item(i-1);\n")
            fileobject.write("    nodename = char(node.getNodeName);\n")
            fileobject.write("    if ~startsWith('#text', nodename)\n")
            fileobject.write("        outSignalIndices = [outSignalIndices, char(node.getAttributes.getNamedItem('index').getNodeValue), ','];\n")
            fileobject.write("    end\n")
            fileobject.write("end\n")
            fileobject.write("if ~isempty(outSignalIndices)\n")
            fileobject.write("    outSignalIndices = strsplit(outSignalIndices,',');\n")
            fileobject.write("else\n")
            fileobject.write("    outSignalIndices = '';\n")
            fileobject.write("end\n")
            fileobject.write("%2. search for output names in the found order\n")
            fileobject.write("expression = xpath.compile('//ModelVariables/ScalarVariable');\n")
            fileobject.write("%apply the expression to the DOM\n")
            fileobject.write("scalVarNodes = expression.evaluate(xDoc,XPathConstants.NODESET);\n")
            fileobject.write("%iterate through the nodes that are returned\n")
            fileobject.write("outSignalNames = [];\n")
            fileobject.write("for i = 1:scalVarNodes.getLength\n")
            fileobject.write("    if any(strcmp(int2str(i), outSignalIndices))    %ScalarVariables number in outSignalIndices\n")
            fileobject.write("        node = scalVarNodes.item(i-1);\n")
            fileobject.write("        nodename = char(node.getAttributes.getNamedItem('name').getNodeValue);\n")
            fileobject.write("        nodename = split(nodename, '[');\n")
            fileobject.write("        outSignalNames = [outSignalNames, nodename{1,1}, ','];\n")
            fileobject.write("    end\n")
            fileobject.write("end\n")
            fileobject.write("if ~isempty(outSignalNames)\n")
            fileobject.write("    outSignalNames = strsplit(outSignalNames, ',');\n")
            fileobject.write("end\n")
            fileobject.write("%rename the outports according to the found information\n")
            fileobject.write("outportHandles = find_system(gcbh, 'LookUnderMasks', 'on', 'SearchDepth', 2, 'BlockType', 'Outport');\n")
            fileobject.write("for i = 1:length(outportHandles)\n")
            fileobject.write("    set_param(outportHandles(i), 'Name', outSignalNames{i});\n")
            fileobject.write("end\n")
            fileobject.write("%3. search for inputs in the scalar variables -> no dedicated inputs section in the ModelStructure of an FMU -> the order is taken from the ScalarVariable order in the modelDescription.xml\n")
            fileobject.write("expression = xpath.compile('//ModelVariables/ScalarVariable[@causality=\"input\"]');\n")
            fileobject.write("%apply the expression to the DOM\n")
            fileobject.write("scalVarNodes = expression.evaluate(xDoc,XPathConstants.NODESET);\n")
            fileobject.write("%iterate through the nodes that are returned\n")
            fileobject.write("inSignalNames = [];\n")
            fileobject.write("for i = 1:scalVarNodes.getLength\n")
            fileobject.write("    node = scalVarNodes.item(i-1);\n")
            fileobject.write("    nodename = char(node.getAttributes.getNamedItem('name').getNodeValue);\n")
            fileobject.write("    nodename = split(nodename, '[');\n")
            fileobject.write("    inSignalNames = [inSignalNames, nodename{1,1}, ','];\n")
            fileobject.write("end\n")
            fileobject.write("if ~isempty(inSignalNames)\n")
            fileobject.write("    inSignalNames = strsplit(inSignalNames, ',');\n")
            fileobject.write("end\n")
            fileobject.write("%rename the inports according to the found information\n")
            fileobject.write("inportHandles = find_system(gcbh, 'LookUnderMasks', 'on', 'SearchDepth', 2, 'BlockType', 'Inport');\n")
            fileobject.write("for i = 1:length(inportHandles)\n")
            fileobject.write("    set_param(inportHandles(i), 'Name', inSignalNames{i});\n")
            fileobject.write("end\n")
            fileobject.write("rmpath('" + path + "');    %remove the path again, since the FMU is imported\n")
        fileobject.close()


    #add the connections between the model components
    def addConnections(self, couplings, modelfile, modelname, interface):
        fileobject = open(modelfile, "a")
        for cpl in couplings:
            fileobject.write("\n%One connection between two blocks\n")
            sourceBlock = modelname + "/" + cpl[0].replace("-", "_")     #Matlab names may not have a -
            sinkBlock = modelname + "/" + cpl[2].replace("-", "_")       #Matlab names may not have a -
            fileobject.write("phFrom = get_param('"+ sourceBlock + "','PortHandles');    %get the port handles of the source block\n")
            fileobject.write("phTo = get_param('" + sinkBlock + "','PortHandles');    %get the port handles of the sink block\n")

            #get the portnumber to a portname -> portnames do not need to be integers
            sourcePort = cpl[1].split(" / ")[0].strip()
            sourceporttype = cpl[1].split(" / ")[1].strip()
            sinkPort = cpl[3].split(" / ")[0].strip()
            #sinkporttype = cpl[3].split(" / ")[1].strip()  #not needed for now
            try:
                #for the source -> out port
                fileobject.write("simBlockHandle = get_param('" + sourceBlock + "','Handle');    %get the handle of the source block (which is a subsystem of the functional block(s) and In/Out blocks)\n")
                #fileobject.write("outportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'FollowLinks', 'on', 'SearchDepth', 2, 'BlockType', 'Outport');\n")
                fileobject.write("outportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'SearchDepth', 2, 'BlockType', 'Outport');    %get the handles to Out blocks in the subsystem\n")
                fileobject.write("outNames = get_param(outportHandles, 'Name');    %get the names of the Out blocks\n")
                fileobject.write("outPorts = get_param(outportHandles, 'Port');    %get the ports of the Out blocks\n")
                #If there are several outNames, the values are placed in a cell array outPorts. -> Find the right number to the name. But make sure there are ports found at all! (Block is in subsystem)
                #If there is only one outName, the outPorts is a string with value '1'. It can be used directly.
                fileobject.write("if iscell(outNames) && ~isempty(outportHandles)\n")
                fileobject.write("    idx = find(ismember(outNames, '" + sourcePort + "'));    %If there are several outNames, the values are placed in a cell array outPorts. -> Find the right number to the name. But make sure there are ports found at all! (Block is in subsystem)\n")
                fileobject.write("    pno = str2num(outPorts{idx});\n")
                fileobject.write("elseif isempty(outportHandles)\n")
                fileobject.write("    errordlg('Please make sure the block ''" + sourceBlock.split("/")[-1] + "'' is in a subsystem in order to get named ports!', 'Block not in Subsystem');\n")
                fileobject.write("    error('Block ''" + sourceBlock.split("/")[-1] + "'' is not in a subsystem!');\n")
                fileobject.write("else\n")
                fileobject.write("    pno = str2num(outPorts);    %If there is only one outName, the outPorts is a string with value '1'. It can be used directly.\n")
                fileobject.write("end\n")
                #for the sink -> in port
                fileobject.write("simBlockHandle = get_param('" + sinkBlock + "','Handle');    %get the handle of the sink block (which is a subsystem of the functional block(s) and In/Out blocks\n")
                #fileobject.write("inportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'FollowLinks', 'on', 'SearchDepth', 2, 'BlockType', 'Inport');\n")
                fileobject.write("inportHandles = find_system(simBlockHandle, 'LookUnderMasks', 'on', 'SearchDepth', 2, 'BlockType', 'Inport');    %get the handles to In blocks in the subsystem\n")
                fileobject.write("inNames = get_param(inportHandles, 'Name');    %get the names of the In blocks\n")
                fileobject.write("inPorts = get_param(inportHandles, 'Port');    %get the ports of the In blocks\n")
                #If there are several inNames, the values are placed in a cell array inPorts. -> Find the right number to the name. But make sure there are ports found at all! (Block is in subsystem)
                #If there is only one inName, the inPorts is a string with value '1'. It can be used directly.
                fileobject.write("if iscell(inNames) && ~isempty(inportHandles)\n")
                fileobject.write("    idx = find(ismember(inNames, '" + sinkPort + "'));    %If there are several inNames, the values are placed in a cell array inPorts. -> Find the right number to the name. But make sure there are ports found at all! (Block is in subsystem)\n")
                fileobject.write("    pni = str2num(inPorts{idx});\n")
                fileobject.write("elseif isempty(inportHandles)\n")
                fileobject.write("    errordlg('Please make sure the block ''" + sinkBlock.split("/")[-1] + "'' is in a subsystem in order to get named ports!', 'Block not in Subsystem');\n")
                fileobject.write("    error('Block ''" + sinkBlock.split("/")[-1] + "'' is not in a subsystem!');\n")
                fileobject.write("else\n")
                fileobject.write("    pni = str2num(inPorts);    %If there is only one inName, the inPorts is a string with value '1'. It can be used directly.\n")
                fileobject.write("end\n")
                #now draw the line
                if sourceporttype in ["SPR", "SPI", "SPB"]:
                    fileobject.write("add_line('" + modelname + "', phFrom.Outport(pno), phTo.Inport(pni), 'autorouting', 'on');   %draw a connection between the now found outport and inport\n")
                elif sourceporttype == "PP":
                    fileobject.write("add_line('" + modelname + "', phFrom.RConn(pno), phTo.LConn(pni), 'autorouting', 'on');   %draw a connection between the now found outport and inport\n")
            except:
                fileobject.close()
                return 1
        fileobject.write("\n")
        fileobject.write("catch\n")
        fileobject.write("end\n")
        fileobject.write("\n")
        fileobject.write("%Here the simulator configuration code begins\n")
        fileobject.close()
        return 0