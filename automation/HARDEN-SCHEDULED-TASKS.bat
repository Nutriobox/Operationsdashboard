@echo off
REM Launches HARDEN-SCHEDULED-TASKS.ps1 elevated (it edits scheduled-task settings,
REM which requires Administrator). Double-click this file and approve the UAC prompt.
cd /d "C:\Users\hp\Downloads\Operationsdashboard\automation"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','\"%CD%\HARDEN-SCHEDULED-TASKS.ps1\"','-NoExit'"
