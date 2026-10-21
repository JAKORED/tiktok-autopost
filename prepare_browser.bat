@echo off
REM ============================================================
REM  Prepare Browser - Chrome pour FactVibes (port CDP 9222)
REM  21/10/2026 : le VRAI profil = config\chrome_tiktok_profile
REM  (il contient les sessions TikTok QR + YouTube). L'instance
REM  "FactVibesDebug" n'a AUCUN cookie : ne plus l'utiliser.
REM  Si le port 9222 repond deja (Chrome du poster ou deja ouvert),
REM  on ne relance RIEN.
REM ============================================================
set PORT=9222
set PROFILE=%~dp0config\chrome_tiktok_profile

REM Port deja actif ? rien a faire.
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:%PORT%/json/version' -TimeoutSec 4 | Out-Null; exit 1 } catch { exit 0 }"
if errorlevel 1 (
  echo [prepare_browser] port %PORT% deja actif - aucune action.
  goto fin
)

set CHROME=
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
if "%CHROME%"=="" (
  echo [prepare_browser] ERREUR : Chrome introuvable.
  exit /b 1
)

if not exist "%PROFILE%" mkdir "%PROFILE%"
start "" "%CHROME%" --remote-debugging-port=%PORT% --user-data-dir="%PROFILE%" "https://www.tiktok.com/tiktokstudio/content"
echo [prepare_browser] Chrome lance (profil chrome_tiktok_profile, port %PORT%).

:fin
REM Verif finale
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:%PORT%/json/version' -TimeoutSec 8 | Out-Null; Write-Host '[prepare_browser] OK : le port 9222 repond.' } catch { Write-Host '[prepare_browser] ALERTE : port 9222 inactif.' }"
