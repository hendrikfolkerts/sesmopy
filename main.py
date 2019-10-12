# -*- coding: utf-8 -*-

__author__ = 'Hendrik Folkerts, University of Applied Sciences Wismar, RG CEA'

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QUrl, QThread
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

    #signals
    #parameters = pyqtSignal(list, list, list, str, str, str)

    #initialize
    def __init__(self, parent=None):
        #QtWidgets.QMainWindow.__init__(self, parent)
        super(Main, self).__init__()

        ##################################################
        # execute the modelbuilder in an own thread -> as seen when starting the thread in the buildModel function,
        # a thread is only started if called from UI

        # create objects
        self.moBuThread = QThread()
        self.moBuObj = modelBuilder()                           # create an instance of the class modelBuilder

        # move modelbuilder object to thread
        self.moBuObj.moveToThread(self.moBuThread)

        # connect modelbuilder signals to slots in this class
        self.moBuObj.statusUpdate.connect(self.onStatusUpdate)  # the function onStatusUpdate is a slot in this class

        # connect modelbuilder signals to slots in this class -> the function onModelCreated contains a slot of the thread object (self.moBuThread.quit)
        self.moBuObj.finished.connect(self.onModelCreated)  # the function onModelCreated is a slot in this class

        # connect thread started signal to modelbuilder's slot
        # pass parameters as well: if you want to "pass parameters to QThread", then it's quite straightforward.
        # 1. You can access member variable of your subclass from any methods of your subclass.
        # 2. The slot of your worker object, that will be executed in another thread can take as many argument as you want.
        # 3. Use a lambda function: self.moBuThread.started.connect(lambda: self.moBuObj.build(objects, nodesWithoutMbAttribute, couplings, modelname, self.modelfolderpathname, fpesfilepath))
        # Just for information: if build was executed in the main thread: modelCreated = self.moBuObj.build(self, objects, nodesWithoutMbAttribute, couplings, modelname, modelfolderpathname, fpesfilepath)  # execute the build method (in the same thread)
        # Here the first method is used: The build method of the modelbuilder object is called without arguments, when the thread is started the build function waits until it receives data.
        # The data is set directly before the thread is started (see "set data for the modelbuilder object").
        self.moBuThread.started.connect(self.moBuObj.build)

        ###################################################

        self.setupUi(self)

        #ui signals
        self.bselectfpesfile.clicked.connect(self.selectFPES)
        self.bbuildmodel.clicked.connect(self.buildModel)
        self.bdoc.clicked.connect(self.documentation)

    #slot
    #when the modelbuilder is finished, this function is called
    def onModelCreated(self, i):
        #when the thread has finished, quit it
        self.moBuThread.quit()
        modelCreated = i
        if modelCreated == 0:
            if self.calledFromUi:
                QMessageBox.information(None, "Model(s) created", "The model(s) was/were created in the folder \"%s\" (a subdirectory of the folder in which \"%s\" lies). In the <b>config.txt</b> file the model file(s) and the respective modelbase file(s) are listed." % (self.modelfolderpathname, self.selectedfpesfile), QtWidgets.QMessageBox.Ok)
            else:
                print("OK - The model(s) was/were created in the \nMODELFOLDER: \"" + self.modelfolderpathname + "\"\nThis is a subdirectory of the folder in which \"" + self.selectedfpesfile + "\" lies. In the config.txt file the model file(s) and the respective modelbase file(s) are listed.")
                print("\n")
        elif modelCreated == 1:
            QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. The simulator or interface is not supported. Please refer to the documentation for simulators and the interface.", QtWidgets.QMessageBox.Ok)
            print("Not OK - The model(s) could not be created. The simulator or interface is not supported. Please refer to the documentation for simulators and the interface.")
        elif modelCreated == 2:
            QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. The portnames for the basic models are not okay. Please refer to the documentation.", QtWidgets.QMessageBox.Ok)
            print("Not OK - The model(s) could not be created. The portnames for the basic models are not okay. Please refer to the documentation.")
        elif modelCreated == 3:
            QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. The modelbasefile cannot be copied. Please check, that the modelbasefile is lying in the same folder (or a subdirectory, see documentation) as the .jsonsestree file containing the FPES. Furthermore the mb-attribute needs to refer to the modelbasefilename (see documentation). Using FMI there could also be a problem parameterizing the MB.", QtWidgets.QMessageBox.Ok)
            print("Not OK - The model(s) could not be created. The modelbasefile cannot be copied. Please check, that the modelbasefile is lying in the same folder as the .jsonsestree file containing the FPES. Furthermore the mb-attribute needs to refer to the modelbasefilename (see documentation).")
        elif modelCreated == 4:
            QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. A parametervalue to vary could not be interpreted as a Python variable.", QtWidgets.QMessageBox.Ok)
            print("Not OK - The model(s) could not be created. A parametervalue to vary could not be interpreted as a Python variable.")
        elif modelCreated == 5:
            QMessageBox.warning(None, "Model(s) not imported in the simulator", "The model(s) could not be imported in the simulator. The simulator could not be found. Please make sure it is accessible via Shell/Command.", QtWidgets.QMessageBox.Ok)
            print("Not OK - The model(s) could not be imported in the simulator. The simulator could not be found. Please make sure it is accessible via Shell/Command.")
        elif modelCreated == 6:
            QMessageBox.warning(None, "FMU(s) not created", "The FMU(s) could not be created. OpenModelica is necessary for creating FMU(s). Please make sure OpenModelica's omc executable is accessible via Shell/Command.", QtWidgets.QMessageBox.Ok)
            print("Not OK - The FMUs could not be created. OpenModelica is necessary for creating FMUs. Please make sure OpenModelica's omc executable is accessible via Shell/Command.")
        elif modelCreated == 7:
            QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. The old model directory could not be removed automatically. For automatic remove no program may access any content of it. Please make sure no model directory is in the same directory as the FPES.", QtWidgets.QMessageBox.Ok)
            print("Not OK - The model(s) could not be created. An old model directory could not be removed automatically. For automatic remove no program may access any content of it. Please make sure no model directory is in the same directory as the FPES.")
        elif modelCreated == 8:
            QMessageBox.warning(None, "Model FMU(s) not imported in the simulator", "Model FMUs(s) could not be imported in the simulator (for OpenModelica / Dymola).", QtWidgets.QMessageBox.Ok)
            print("Not OK - Model FMU(s) could not be imported in the simulator (for OpenModelica / Dymola).")
        elif modelCreated == 9:
            QMessageBox.warning(None, "Model(s) not imported in the simulator", "One FMU did not pass the compliance check. Check the statusmessage (it is reset when this message is closed)!", QtWidgets.QMessageBox.Ok)
            print("Not OK - One FMU did not pass the compliance check. Check the statusmessage!")
        elif modelCreated == 10:
            QMessageBox.warning(None, "FMU(s) not created", "Please check the FPES and the created model which shall be translated to an FMU.", QtWidgets.QMessageBox.Ok)
            print("Not OK - FMU(s) could not be created of the model(s)! Please check the FPES and the created model which shall be translated to an FMU.")
        elif modelCreated == 11:
            if self.calledFromUi:
                QMessageBox.information(None, "Created", "Created in the folder \"%s\" (a subdirectory of the folder in which \"%s\" lies)." % (self.modelfolderpathname, self.selectedfpesfile), QtWidgets.QMessageBox.Ok)
            else:
                print("OK - Created in the \nFOLDER: \"" + self.modelfolderpathname + "\"\nThis is a subdirectory of the folder in which \"" + self.selectedfpesfile + "\" lies.")
        #if called from ui, the build model button needs to be activated again and clear the status
        if self.calledFromUi:
            self.bbuildmodel.setEnabled(True)
            self.lstatustext.setText("")

    #slot
    #show the statusmessage from the thread
    def onStatusUpdate(self, message):
        if self.calledFromUi:   #update the UI
            self.lstatustext.setText(message)
        else:
            print(message + "\n")

    def selectFPES(self):
        fname = QFileDialog.getOpenFileName(self, "Open an FPES from JSON", '', "FPES SES Tree (*.jsonsestree);;All files (*)")
        self.leselectedfpesfile.setText(fname[0])

    def buildModel(self, selectedfpesfile="", calledFromUi=True):
        #make variables class variables
        self.calledFromUi = calledFromUi

        #deactivate the build model button
        if self.calledFromUi:
            self.bbuildmodel.setEnabled(False)

        try:
            # get the fpesfile
            if self.calledFromUi:    #if the modelbuilder was called from the UI
                self.selectedfpesfile = self.leselectedfpesfile.text()
            else:
                self.selectedfpesfile = selectedfpesfile

            # only if a file is selected
            if self.selectedfpesfile != "" and not " " in self.selectedfpesfile:
                # read file
                f = open(self.selectedfpesfile, "r")
                filestr = f.read()
                f.close()
                readJsonObj = readJson  #create an instance of the class readJson
                okay, nodelist, sespes = readJsonObj.fromJSON(self, filestr)
                #only if the file is okay and an FPES
                if okay and sespes[0][0] == "fpes" and len(nodelist) > 0:
                    #read the FPES file
                    objects, couplings, nodesWithoutMbAttribute = readJsonObj.readFPES(self, nodelist)
                    if objects:
                        print("The nodes\n" + ",\n".join(nodesWithoutMbAttribute) + "\nhave no MB-Attribute. Are their attributes needed for the simulation? This is just a hint in case of searching for a mistake.\n")
                        #get a name for the folder including the path, in which the models are created -> it shall get the name of the FPES .jsonsestree file
                        fpesfilepathname, fpesfileext = os.path.splitext(self.selectedfpesfile)
                        self.modelfolderpathname = fpesfilepathname + "_models"
                        #get a name for the model -> it shall get the name of the FPES .jsonsestree file
                        modelname = os.path.basename(fpesfilepathname) + "_model"
                        #get the path of the selected FPES .jsonsestree file
                        fpesfilepath = os.path.split(self.selectedfpesfile)[0]   #get the path to the modelbase from the fpesfile

                        #set data for the modelbuilder object
                        self.moBuObj.objects = objects
                        self.moBuObj.nodesWithoutMbAttribute = nodesWithoutMbAttribute
                        self.moBuObj.couplings = couplings
                        self.moBuObj.modelname = modelname
                        self.moBuObj.modelfolderpathname = self.modelfolderpathname
                        self.moBuObj.fpesfilepath = fpesfilepath

                        #if called from ui: start the modelbuilder thread
                        #if called from shell: start the build function (not in an own thread)
                        if self.calledFromUi:
                            self.moBuThread.start()
                        else:
                            self.moBuObj.build()

                    elif not objects:
                        QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. Objects cannot be created from the nodelist.", QtWidgets.QMessageBox.Ok)
                        print("Not OK - The model(s) could not be created. Objects cannot be created from the nodelist.")
                        # if called from ui, the build model button needs to be activated again and clear the status
                        if self.calledFromUi:
                            self.bbuildmodel.setEnabled(True)
                            self.lstatustext.setText("")
                    else:
                        nWoMbA = ', '.join(nodesWithoutMbAttribute)
                        QMessageBox.warning(None, "Model(s) not created", "The model(s) could not be created. The nodes \"%s\" do not have an mb-attribute." % nWoMbA, QtWidgets.QMessageBox.Ok)
                        print("Model(s) not created", "The model(s) could not be created. The nodes \"" + nWoMbA + "\" do not have an mb-attribute.")
                        # if called from ui, the build model button needs to be activated again and clear the status
                        if self.calledFromUi:
                            self.bbuildmodel.setEnabled(True)
                            self.lstatustext.setText("")
                else:
                    QMessageBox.warning(None, "Can not read file", "The file \"%s\" seems not to contain an FPES. Please open this file in SESToPy, make sure it represents an FPES and that the Selector in the Information ToolBox is set to flattened PES." % self.selectedfpesfile, QtWidgets.QMessageBox.Ok)
                    print("Not OK - The file \"" + self.selectedfpesfile + "\" seems not to contain an FPES. Please open this file in SESToPy, make sure it represents an FPES and that the Selector in the Information ToolBox is set to flattened PES.")
                    # if called from ui, the build model button needs to be activated again and clear the status
                    if self.calledFromUi:
                        self.bbuildmodel.setEnabled(True)
                        self.lstatustext.setText("")
            else:
                QMessageBox.information(None,  "Selection missing or the path/filename contains whitespaces", "Please select an FPES .jsonsestree file. In the name of the .jsonsestree file and the path to it no whitespaces are allowed!", QtWidgets.QMessageBox.Ok)
                print("Not OK - Please select an FPES .jsonsestree file.")
                # if called from ui, the build model button needs to be activated again and clear the status
                if self.calledFromUi:
                    self.bbuildmodel.setEnabled(True)
                    self.lstatustext.setText("")

        except:
            QMessageBox.critical(None, "Can not read file", "The file \"%s\" could not be read or there was an unknown error." % self.selectedfpesfile, QtWidgets.QMessageBox.Ok)
            print("Not OK - The file \"" + self.selectedfpesfile + "\" could not be read or there was an unknown error.")
            # if called from ui, the build model button needs to be activated again and clear the status
            if self.calledFromUi:
                self.bbuildmodel.setEnabled(True)
                self.lstatustext.setText("")



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
                main = Main()
                main.buildModel(fpesfile, False)