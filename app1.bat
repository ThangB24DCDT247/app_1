@echo off
chcp 65001 >nul
title PTIT MQTT Monitor

set UV=C:\Users\THANG\.local\bin\uv.exe
set APP=%~dp0app.py

echo Dang khoi dong PTIT MQTT Monitor...
"%UV%" run --with paho-mqtt --with Pillow "%APP%"
