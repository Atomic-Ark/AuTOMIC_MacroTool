#!/bin/bash

echo "Auto-commit script started at $(date)"
cd /project/sandbox/user-workspace/AuTOMIC_MacroTool

while true; do
    echo "Checking for changes at $(date)..."
    
    # Najpierw pobierz zmiany z GitHuba
    echo "Pulling changes from GitHub..."
    git pull origin main --rebase
    
    # Sprawdź i commituj zmiany lokalne
    git add .
    if git diff --staged --quiet; then
        echo "No changes to commit"
    else
        echo "Changes detected, committing..."
        git commit -m "Auto-commit: $(date)"
        echo "Pushing to GitHub..."
        git push origin main
        if [ $? -eq 0 ]; then
            echo "Changes successfully pushed to GitHub"
        else
            echo "Error pushing changes to GitHub"
        fi
    fi
    
    echo "Waiting 5 minutes before next check..."
    sleep 300
done
