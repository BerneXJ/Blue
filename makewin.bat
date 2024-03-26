@echo off

REM Run PyInstaller to package main.py
pyinstaller --onefile --windowed main.py

REM Copy tasks.tmpl to the dist folder
copy tasks.tmpl dist\