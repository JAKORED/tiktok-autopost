@echo off
echo ============================================
echo   FactVibes - Preparation Chrome
echo ============================================
echo.
echo   Etape 1: Une fenetre Chrome va s'ouvrir
echo   Etape 2: Connecte-toi sur developers.tiktok.com
echo   Etape 3: Dis a OpenCode "c'est fait"
echo.

if exist "%LocalAppData%\Google\Chrome\User Data" (
    set "PROFILE=%LocalAppData%\Google\Chrome\User Data"
) else (
    set "PROFILE=%USERPROFILE%\AppData\Local\Google\Chrome\User Data"
)

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%PROFILE%\FactVibesDebug" "https://developers.tiktok.com/"

if %errorlevel% neq 0 (
    echo.
    echo ERREUR: Chrome n'a pas pu se lancer.
    echo Essaie:  "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 https://developers.tiktok.com/
)

echo.
echo Chrome est lance. Connecte-toi dans la fenetre ouverte.
pause