@echo off
title Winner's Circle Demo Bot
python -m pip install -r requirements.txt
if errorlevel 1 ( echo Python/pip error. Try: py -m pip install -r requirements.txt & pause & exit /b 1 )
if not exist .env ( copy .env.example .env >nul & echo Created .env. Open it and insert your BotFather token. & pause & exit /b 0 )
python bot.py
pause
