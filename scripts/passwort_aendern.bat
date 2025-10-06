@echo off
setlocal enabledelayedexpansion

:: Benutzername abfragen
set /p username=Bitte Benutzernamen eingeben: 

:: Passwort abfragen
set /p password=Bitte neues Passwort eingeben: 

:: Befehl ausführen
call mindest.bat admin users update-password --username !username! --password "!password!"

pause
