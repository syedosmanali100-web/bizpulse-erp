@echo off
REM BizPulse ERP - Quick Deployment Script for Windows

echo.
echo ========================================
echo   BizPulse ERP Deployment Script
echo ========================================
echo.

REM Check if git is initialized
if not exist ".git" (
    echo Initializing Git repository...
    git init
)

REM Add all files
echo Adding files to Git...
git add .

REM Commit changes
set /p commit_msg="Enter commit message (or press Enter for default): "
if "%commit_msg%"=="" (
    set commit_msg=Update BizPulse ERP - %date% %time%
)
git commit -m "%commit_msg%"

REM Check if remote exists
git remote | findstr "origin" >nul
if errorlevel 1 (
    echo.
    echo No remote repository found.
    echo Please create a repository on GitHub first.
    echo.
    set /p repo_url="Enter your GitHub repository URL: "
    if not "%repo_url%"=="" (
        git remote add origin %repo_url%
        echo Remote added successfully!
    )
)

REM Push to GitHub
echo.
echo Pushing to GitHub...
git branch -M main
git push -u origin main

echo.
echo ========================================
echo   Code pushed to GitHub successfully!
echo ========================================
echo.
echo Next Steps:
echo 1. Go to https://dashboard.render.com/
echo 2. Click 'New +' - 'Web Service'
echo 3. Connect your GitHub repository
echo 4. Render will auto-detect render.yaml and deploy!
echo.
echo Your app will be live in 5-10 minutes!
echo.
pause
