@echo off
setlocal enabledelayedexpansion

rem --- change to target directory (uses pushd so it works with network drives) ---
pushd "C:\Users\devan\Desktop\yt-dlp cmd player" 2>nul
if errorlevel 1 (
  echo ERROR: could not change to "C:\Users\devan\Desktop\yt-dlp cmd player"
  echo Make sure the path exists and try again.
  pause
  exit /b 1
)

rem --- choose Audio or Video ---
:TOPCHOICE
echo.
echo Choose mode:
echo  1) Audio only
echo  2) Video
set /p top_choice="Enter 1 or 2: "
if "%top_choice%"=="1" goto AUDIO_MODE
if "%top_choice%"=="2" goto VIDEO_MODE
echo Invalid choice. Try again.
goto TOPCHOICE

:AUDIO_MODE
echo Selected: Audio only
goto PLAYMODE_PROMPT

:VIDEO_MODE
echo Selected: Video
set "VIDEO_FLAG=--video"
goto PLAYMODE_PROMPT

:PLAYMODE_PROMPT
echo.
echo Choose play mode:
echo  1) interactive play
echo  2) offline
echo  3) playlist (shuffle all)
set /p play_choice="Enter 1, 2, or 3: "

if "%play_choice%"=="1" (
  set "CMD=python yt_audio_player.py"
) else if "%play_choice%"=="2" (
  set "CMD=python yt_audio_player.py --offline"
) else if "%play_choice%"=="3" (
  set "CMD=python yt_audio_player.py --list --shuffle-all"
) else (
  echo Invalid choice. Try again.
  goto PLAYMODE_PROMPT
)

rem append video flag if needed (VIDEO_FLAG only set in video mode)
if defined VIDEO_FLAG (
  set "CMD=%CMD% %VIDEO_FLAG%"
)

echo.
echo Running command:
echo   %CMD%
echo.
%CMD%
set RC=%ERRORLEVEL%

rem return to original dir
popd
exit /b %RC%
