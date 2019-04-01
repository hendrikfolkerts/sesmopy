# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts, University of Applied Sciences Wismar, RG CEA'

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QUrl
from time import strftime
import os
from pathlib import Path
from os.path import splitext

from modelBuilder import *
from readJson import *

__version__ = strftime("%Y"+"."+"%m"+"."+"%d") #for development
#__version__ = str(1.0)

"""
This program is written in Python3 with the Qt5 bindings PyQt5
The project has been started using Python3.4.1 and PyQt5.5 and is running with current versions of Python3 and PyQt5.

Call this program with:
python3 main.py

Start building without using the graphical editor:
python3 main.py -b ~/HDD/Promotion/SES_Tests/BuildTest.jsonsestree

For more options please call:
python main.py -h
"""

#import ui class
from main_ui import Ui_MainWindow

class Main(QtWidgets.QMainWindow, Ui_MainWindow):
    
    #initialize
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        #signals
        self.bselectfpesfile.clicked.connect(self.selectFPES)
        self.bbuildmodel.clicked.connect(self.buildModel)
        self.bdoc.clicked.connect(self.documentation)

    def selectFPES(self):
        fname = QFileDialog.getOpenFileName(self, "Open an FPES from JSON", '', "FPES SES Tree (*.jsonsestree);;All files (*)")
        self.leselectedfpesfile.setText(fname[0])

    def buildModel(self, selectedfpesfile="", calledFromUi=True):
        try:
            # get the fpesfile
            if calledFromUi:    #if the modelbuilder was called from the UI
                selectedfpesfile = self.leselectedfpesfile.text()

            # only if a file is selected
            if selectedfpesfile != "":
                # read file
                f = open(selectedfpesfile, "r")
                filestr = f.read()
                f.close()
                readJsonObj = readJson  #create an instance of the class readJson
                okay, nodelist, sespes = readJsonObj.fromJSON(self, filestr)
                #only if the file is okay and an FPES
                if okay and sespes[0][0] == "fpes" and len(nodelist) > 0:
                    #read the FPES file
                    objects, couplings, nodesWithOutMbAttribute = readJsonObj.readFPES(self, nodelist)
                    if objects:
                        print("The nodes\n" + ",\n".join(nodesWithOutMbAttribute) + "\nhave no MB-Attribute. Are their attributes needed for the simulation? This is just a hint in case of searching for a mistake.\n")
                        #get a name for the folder including the path, in which the models are created -> it shall get the name of the FPES .jsonsestree file
                        fpesfilepathname, fpesfileext = os.path.splitext(selectedfpesfile)
                        modelfolderpathname = fpesfilepathname + "_models"
                        #get a name for the model -> it shall get the name of the FPES .jsonsestree file
                        modelname = os.path.basename(fpesfilepathname) + "_model"
                        #get the path and names of the modelbases -> they shall lie in the same directory as the FPES .jsonsestree file and the fileending depends on the simulator
                        fpesfilepath = os.path.split(selectedfpesfile)[0]   #get the path to the modelbase from the fpesfile
                        mblinks = []
                        for ob in objects:      #get the filenames of the modelbases from the mb-attributes
                            #mblinks.append(os.path.split(ob[1])[0].replace("/", ""))   #only the first part before / determines the MB -> for native models it is like that -> in the modelBuilder object now
                            mblinks.append(ob[1])
                        mblinks = list(set(mblinks))
                        #modelbaselinkspathname = [os.path.join(fpesfilepath, mblink) for mblink in mblinks]  #the modelbasefilepathname has no ending yet
                        #get the attributes of the nodes without MB-Attribute from the nodelist (they may be necessary for the simulator configuration)
                        #execute the modelbuilder
                        moBuObj = modelBuilder #create an instance of the class modelBuilder
                        modelCreated = moBuObj.build(self, objects, nodesWithOutMbAttribute, couplings, modelname, modelfolderpathname, fpesfilepath, mblinks)   #execute the build method
                        if modelCreated == 0:
                            if calledFromUi:
                                QMessageBox.information(None, "Model(s) created", "The model(s) was/were created in the folder \"%s\" (a subdirectory of the folder in which \"%s\" lies)." % (modelfolderpathname, selectedfpesfile), QtWidgets.QMessageBox.Ok)
                            else:
                                print("\n")
                                print("OK - The model(s) was/were created in the \nMODELFOLDER: \""+modelfolderpathname+"\"\nThis is a subdirectory of the folder in which \""+selectedfpesfile+"\" lies.")
                                print("\n")
                        elif modelCreated == 1:
                            QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. The simulator or interface is not supported. Please refer to the documentation for simulators and the interface.", QtWidgets.QMessageBox.Ok)
                            print("Not OK - The model(s) could not be created. The simulator or interface is not supported. Please refer to the documentation for simulators and the interface.")
                        elif modelCreated == 2:
                            QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. The portnames for the basic models are not okay. Please refer to the documentation.", QtWidgets.QMessageBox.Ok)
                            print("Not OK - The model(s) could not be created. The portnames for the basic models are not okay. Please refer to the documentation.")
                        elif modelCreated == 3:
                            QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. The modelbasefile cannot be copied. Please check, that the modelbasefile is lying in the same folder as the .jsonsestree file containing the FPES. Furthermore the mb-attribute needs to refer to the modelbasefilename (see documentation).", QtWidgets.QMessageBox.Ok)
                            print("Not OK - The model(s) could not be created. The modelbasefile cannot be copied. Please check, that the modelbasefile is lying in the same folder as the .jsonsestree file containing the FPES. Furthermore the mb-attribute needs to refer to the modelbasefilename (see documentation).")
                        elif modelCreated == 4:
                            QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. A parametervalue to vary could not be interpreted as a Python variable.", QtWidgets.QMessageBox.Ok)
                            print("Not OK - The model(s) could not be created. A parametervalue to vary could not be interpreted as a Python variable.")
                    elif not objects:
                        QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. Objects cannot be created from the nodelist.", QtWidgets.QMessageBox.Ok)
                        print("Not OK - The model(s) could not be created. Objects cannot be created from the nodelist.")
                    else:
                        nWoMbA = ', '.join(nodesWithOutMbAttribute)
                        QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. The nodes \"%s\" do not have an mb-attribute." % nWoMbA, QtWidgets.QMessageBox.Ok)
                        print("Model(s) not created", "The model(s) could not be created. The nodes \"" + nWoMbA + "\" do not have an mb-attribute.")
                else:
                    QMessageBox.warning(None, "Can not read file", "The file \"%s\" seems not to contain an FPES. Please open this file in SESToPy, make sure it represents an FPES and that the Selector in the Information ToolBox is set to flattened PES." % selectedfpesfile, QtWidgets.QMessageBox.Ok)
                    print("Not OK - The file \"" + selectedfpesfile + "\" seems not to contain an FPES. Please open this file in SESToPy, make sure it represents an FPES and that the Selector in the Information ToolBox is set to flattened PES.")
            else:
                QMessageBox.information(None,  "Selection missing", "Please select an FPES .jsonsestree file.", QtWidgets.QMessageBox.Ok)
                print("Not OK - Please select an FPES .jsonsestree file.")
        except:
            QMessageBox.critical(None, "Can not read file", "The file \"%s\" could not be read or there was an unknown error." % selectedfpesfile, QtWidgets.QMessageBox.Ok)
            print("Not OK - The file \"" + selectedfpesfile + "\" could not be read or there was an unknown error.")



    """documentation"""
    def documentation(self):
        #QDesktopServices.openUrl(QUrl(self.programPath + "Documentation/Doc_LaTeX/doc.pdf"))
        if not QDesktopServices.openUrl(QUrl("file:Documentation/Doc_LaTeX/doc.pdf")):
            QDesktopServices.openUrl(QUrl("file:doc.pdf"))  #if the doc.pdf is in the main folder (e.g. after building executable)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    #Main.buildModel(Main, "C:\\Users\\win10\\Desktop\\SES_Feedback_pruned_feedforwarde0_flattened.jsonsestree", False)  #for purpose of testing: comment out the lines until the end of the file

    #check if the application is called for building -> no graphical interface shall be started -> sys.argv contains more elements
    if len(sys.argv) == 1:
        window = Main(None)
        window.show()
        sys.exit(app.exec_())
    if len(sys.argv) > 1:
        printHowToCall = False
        if sys.argv[1] == "-h" or sys.argv[1] == "--help":         #help called
            printHowToCall = True
        elif sys.argv[1] != "-b":           #no switch to build
            printHowToCall = True
        elif sys.argv[1] == "-b" and len(sys.argv) != 3:  # length of arguments does not fit for building
            printHowToCall = True

        if printHowToCall:
            print("\n")
            print("For building please call \"python3 main.py -b /path/to/fpesfilename.jsonsestree\" e.g. \"python3 main.py -b /home/linux/fpes.jsonsestree\".")
            print("Remember to take the operating system's specific folder separator (/ or \) and the command \"python3\" may just be called \"python\" in Windows.")
            print("Exiting the program.")
            print("\n")
        else:
            fpesfile = sys.argv[2]
            # check if the path is okay and it could be an SES JSON file
            if not Path(fpesfile).is_file() or splitext(fpesfile)[1] != ".jsonsestree":
                # the file does not exist
                print("The file containing the FPES as JSON you stated does not exist or is no file with the ending \"jsonsestree\". Exiting the program.")
            else:
                print("\nBuilding using the FPES file: " + fpesfile)
                #now build
                Main.buildModel(Main, fpesfile, False)