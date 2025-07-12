@echo off
cd /d %~dp0
python script.py > log.txt 2>&1
