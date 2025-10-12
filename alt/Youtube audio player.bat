@echo off
setlocal enabledelayedexpansion

:: ================= CHECK DEPENDENCIES =================
where yt-dlp.exe >nul 2>&1
if errorlevel 1 (
    echo [ERROR] yt-dlp.exe not found in PATH. Please install or add to PATH.
    pause
    exit /b 1
)
where ffplay.exe >nul 2>&1
if errorlevel 1 (
    echo [WARNING] ffplay.exe not found in PATH. You need it to play audio.
)

:: ================= CHECK FOR COOKIES =================
set "COOKIE_PARAM="
if exist "%~dp0cookies.txt" set "COOKIE_PARAM=--cookies \"%~dp0cookies.txt\""

:loop
:: ================= PROMPT USER =================
echo.
echo Enter YouTube URL, playlist, or search query (or type EXIT to quit):
set /p "inp=Input: "

if /i "%inp%"=="EXIT" goto :eof
if "%inp%"=="" goto loop

:: ================= DETECT URL OR SEARCH =================
echo %inp% | findstr /i "https://\|http://" >nul
if not errorlevel 1 (
    set "yt_arg=%inp%"
) else (
    set "yt_arg=ytsearch5:%inp%"
)

:: ================= STREAM AUDIO =================
echo [INFO] Running: yt-dlp -f bestaudio -o - %COOKIE_PARAM% "%yt_arg%" | ffplay -i - -nodisp -autoexit
yt-dlp -f bestaudio -o - %COOKIE_PARAM% "%yt_arg%" 2>&1 | ffplay -i - -nodisp -autoexit
if errorlevel 1 (
    echo [ERROR] Playback or download failed. Please check your query or link.
)
goto loop
