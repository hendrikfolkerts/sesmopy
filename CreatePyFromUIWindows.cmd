@echo off

REM change in path of the current file
REM d is the drive, p is the path and 0 is the filename of this file (%0 is the filename ofthe current file)
pushd "%~dp0"

REM UI: convert .ui to .py
pyuic5 -o main_ui.py main_ui.ui