INTRODUCTION

The software SESMoPy has been developed by the research group Computational
Engineering and Automation (CEA) at Wismar University of Applied Sciences.
The software implements a modelbuilder according to the System Entity
Structure / Model Base (SES/MB) infrastructure introduced for automatic
execution of simulation experiments. The focus of the software is the model
generation for different simulators.
Please read the documentation for further information. A comprehensive
introduction to the SES/MB theory is given in the documentation of the SES
modeling tool SESToPy.
The software is written in Python3 with PyQt5 as user interface.
It was tested with the simulation softwares Matlab R2018a (for Simulink),
OpenModelica 1.12.0, and Dymola 2018.
Furthermore it makes use of the FMU Compliance Checker developed by Modelon AB.

EXECUTE

Copy the directory SESMoPy in your home folder, e.g. C:\Users\\\<Username>
(necessary if simulation models are built for Dymola, simulation cannot be executed 
in Dymola otherwise).
Make sure, that the command "omc" is on the path and the program is thus startable
from the shell (needed for model generation using the Functional Mock-up Interface
(FMI)). If models using FMI model generation are built for Dymola, the command
"dymola" has to be on the path as well. This is described in the documentation in
detail.  
The program can be executed from source. Python3 with PyQt5 needs to be installed
and the Python executable needs to be on the path. Open a shell and change with the
cd command to the SESMoPy directory. The program then can be started with the shell
command:
- in Windows: python main.py
- in Linux: python3 main.py

Build as executable  
SESMoPy can alternatively be built as executable for Windows and Linux. More
information on this is in the documentation. This is not preferred and not
tested in new program versions. The created executable file in the program
directory has the name "SESMoPy".

CHANGELOG


KNOWN BUGS, NOTES, TODO

- Usage of the Experimental Frame

- Simulink models can be nicely arranged with the Matlab command:
Simulink.BlockDiagram.arrangeSystem('\<systemname\>');

LICENSE

This application is licensed under GNU GPLv3.

HOW TO CITE

Folkerts, H., Pawletta, T., Deatcu, C., and Hartmann, S. (2019). A Python Framework for
Model Specification and Automatic Model Generation for Multiple Simulators. In: Proc. of
ASIM Workshop 2019 - ARGESIM Report 57, ASIM Mitteilung AM 170. ARGESIM/ASIM Pub.
TU Vienna, Austria, 02/2019, 69-75. (Print ISBN 978-3-901608-06-3)

Folkerts, H., Deatcu, C., Pawletta, T., Hartmann, S. (2019). Python-Based eSES/MB
Framework: Model Specification and Automatic Model Generation for Multiple Simulators.
SNE - Simulation Notes Europe Journal, ARGESIM Pub. Vienna, SNE 29(4)2019, 207-215.
(DOI: 10.11128/sne.29.tn.10497),(Selected EUROSIM 2019 Postconf. Publ.)

Folkerts, H., Pawletta, T., Deatcu, C., Santucci, J.F., Capocchi, L. (2019). An Integrated
Modeling, Simulation and Experimentation Environment in Python Based on SES/MB and DEVS.
Proc. of the 2019 Summer Simulation Conference, ACM Digital Lib., 2019 July 22-24, Berlin,
Germany, 12 pages.

Folkerts, H., Pawletta, T., Deatcu, C. (2021). Model Generation for Multiple Simulators
Using SES/MB and FMI. SNE - Simulation Notes Europe Journal, ARGESIM Pub. Vienna,
SNE 31(1) 2021, 25-32. (DOI: 10.11128/sne.31.tn.10554), (Selected ASIM 2020 Postconf. Publ.)