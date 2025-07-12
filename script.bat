@echo off
cd /d %~dp0
git pull > log_git.txt 2>&1
python script.py > log.txt 2>&1
