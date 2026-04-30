@echo off
title Subway Bot

echo Installing requirements...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt

echo Starting bot...
py -m subway_bot

if errorlevel 1 (
    echo Retry with python...
    python -m subway_bot
)

pause