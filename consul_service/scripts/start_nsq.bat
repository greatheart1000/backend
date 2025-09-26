@echo off
echo Starting NSQ components...

echo Starting nsqlookupd...
start "nsqlookupd" nsqlookupd

timeout /t 2 /nobreak >nul

echo Starting nsqd...
start "nsqd" nsqd --lookupd-tcp-address=127.0.0.1:4161

echo NSQ started successfully!
echo NSQ Admin UI: http://localhost:4171
echo Press any key to stop NSQ
pause

taskkill /f /im nsqlookupd.exe
taskkill /f /im nsqd.exe 