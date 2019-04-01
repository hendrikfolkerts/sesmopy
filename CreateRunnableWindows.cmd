@echo off
REM for Python 3.4 with cx_Freeze 4.3.4
REM change in path of current file
pushd "%~dp0"
REM create executable with cx_Freeze
python.exe setupwindows.py build
REM change folder
cd build

REM old (without date):
REM get processor architecture
REM reg Query "HKLM\Hardware\Description\System\CentralProcessor\0" | find /i "x86" > NUL && set OS=32BIT || set OS=64BIT
REM IF "%PROCESSOR_ARCHITECTURE%"=="x86" (set OS=32BIT) else (set OS=64BIT)
REM rename folder
REM if %OS%==32BIT ren exe.win32-3.4 SESMoPy_Windows_Executable_x86
REM if %OS%==64BIT ren exe.win-amd64-3.4 SESMoPy_Windows_Executable_x86_64
REM copy the Examples folder, for xcopy \ at the end defaults to a folder, * at the end to a file
REM if %OS%==32BIT xcopy ..\Examples SESMoPy_Windows_Executable_x86\Examples\ /s /e /h
REM if %OS%==64BIT xcopy ..\Examples SESMoPy_Windows_Executable_x86_64\Examples\ /s /e /h
REM move folder 2 directories up
REM if %OS%==32BIT move SESMoPy_Windows_Executable_x86 ..\..
REM if %OS%==64BIT move SESMoPy_Windows_Executable_x86_64 ..\..

REM new (with date):
REM get processor architecture
IF "%PROCESSOR_ARCHITECTURE%"=="x86" (set OS=x86) else (set OS=x86_64)
REM get the date and replace spaces with 0
set datetimef=%date:~-4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
set datetimef=%datetimef: =0%
REM rename folder
if %OS%==x86 ren exe.win32-3.4 SESMoPy_Windows_Executable_%OS%_%datetimef%
if %OS%==x86_64 ren exe.win-amd64-3.4 SESMoPy_Windows_Executable_%OS%_%datetimef%
REM copy the Examples folder, for xcopy \ at the end defaults to a folder, * at the end to a file
xcopy ..\Examples SESMoPy_Windows_Executable_%OS%_%datetimef%\Examples\ /s /e /h
REM move folder 2 directories up
move SESMoPy_Windows_Executable_%OS%_%datetimef% ..\..

REM go directory up again
cd ..
REM remove build folder
rmdir build