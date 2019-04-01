#setup-File for cx_Freeze
from cx_Freeze import setup, Executable
import main
 
includefiles = ["Documentation/Doc_LaTeX/doc.pdf", "i2rightarrow.ico", "i2rightarrow.png", "ibook.png", "ifileopen.png", "iforward.png"] # include files
includes = []
excludes = []
packages = []
version = main.__version__.replace(".", "_")

exe = Executable(
 # what to build
   script = "main.py", # the name of the main python script
   initScript = None,
   base = 'Win32GUI', # "Win32GUI" because no console app
   targetName = "SESMoPy_" + version + ".exe", #name of exe
   copyDependentFiles = True,
   compress = True,
   appendScriptToExe = True,
   appendScriptToLibrary = True,
   icon = "i2rightarrow.ico" # the icon
)
 
setup(
    name = "SESMoPy", # name of program
    version = main.__version__,
    description = 'SESMoPy',
    author = "Hendrik Martin Folkerts",
    author_email = "hendrikmartinfolkerts@gmail.com",
    options = {"build_exe": {"excludes":excludes,"packages":packages,
      "include_files":includefiles}},
    executables = [exe]
)
