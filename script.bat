@echo off
cd /d %~dp0
for /f "usebackq delims=" %%s in ("secret.txt") do (
    python test.py "%%s" > log.txt 2>&1
)
