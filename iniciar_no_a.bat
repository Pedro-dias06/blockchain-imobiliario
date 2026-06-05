@echo off
echo Instalando dependencias...
pip install -r requirements.txt
echo.
echo Iniciando No A na porta 5000...
set PORT=5000
set DB_NAME=forum_a.db
python app.py
pause
