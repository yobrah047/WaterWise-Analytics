@echo off
cd /d C:\Users\admin\waterwise

echo Adding changes...
git add .

echo Committing...
git commit -m "Auto update from local machine"

echo Pushing to GitHub...
git push

pause

