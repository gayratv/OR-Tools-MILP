@echo off
setlocal

:: --- Настройки ---
set SSH_KEY=C:\Users\<ВАШ_ПОЛЬЗОВАТЕЛЬ>\.ssh\vps_key
set VPS_USER=user
set VPS_HOST=203.0.113.25
set LOCAL_PORT=3307
set REMOTE_PORT=3306

:: --- Запуск SSH-туннеля ---
echo Открываю туннель: localhost:%LOCAL_PORT% -> %VPS_HOST%:%REMOTE_PORT%
ssh -i %SSH_KEY% -L %LOCAL_PORT%:127.0.0.1:%REMOTE_PORT% %VPS_USER%@%VPS_HOST%

pause
