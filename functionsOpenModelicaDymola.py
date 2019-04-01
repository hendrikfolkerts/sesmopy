# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts'

import os

class functionsOpenModelicaDymola():

    #create a textfile with instructions on how to build the system
    def initModel(self, modelfolderpathname, modelname):
        modelfile = os.path.join(modelfolderpathname, modelname)
        modelfile = modelfile + ".mo"
        fileobject = open(modelfile, "w")
        #begin statement
        fileobject.write("model "+modelname+"\n")
        fileobject.close()
        return modelfile

    def addComponents(self, objects, modelfile, modelname):
        fileobject = open(modelfile, "a")
        for ob in objects:
            #create objects
            blockname = ob[0]
            type = ob[1]
            type = type.replace("/", ".")   #change separator from '/' to '.'
            fileobject.write("  "+type+" "+blockname+"(")
            #set block parameters
            atro = 0
            while atro < len(ob[2]):
                #change definition of list / array constant
                if len(ob[2][atro][1]) > 0 and ob[2][atro][1][0] == "[":
                    ob[2][atro][1].replace("[", "{")
                    ob[2][atro][1].replace("]", "}")
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
        fileobject.close()

    def addConnections(self, couplings, modelfile, modelname):
        fileobject = open(modelfile, "a")
        fileobject.write("equation\n")
        for cpl in couplings:
            sourceblock = cpl[0]
            sourceport = cpl[1]
            sinkblock = cpl[2]
            sinkport = cpl[3]

            #change to Dymola portnames Inn, Onn -> if the portnames are given as integer
            try:
                int(sourceport)
                int(sinkport)
                sourceport = "O" + sourceport
                sinkport = "I" + sinkport
            except:
                pass

            #now write the port information
            fileobject.write("  connect("+sourceblock+"."+sourceport+", "+sinkblock+"."+sinkport+");\n")
        #end statement
        fileobject.write("end "+modelname+";\n")
        fileobject.close()
        return 0