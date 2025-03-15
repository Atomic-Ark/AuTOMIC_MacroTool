#!/bin/bash

echo "Auto-commit script started at $(date)"
cd /project/sandbox/user-workspace/AuTOMIC_MacroTool

while true; do
    echo "Checking for changes at $(date)..."
    
    # Sprawdź i commituj zmiany
    git add .
    if git diff --staged --quiet; then
        echo "No changes to commit"
    else
        echo "Changes detected, committing..."
        git commit -m "Auto-commit: $(date)"
        echo "Pushing to GitHub..."
        git push origin main --force
        echo "Changes pushed to GitHub"
    fi
    
    echo "Waiting 5 minutes before next check..."
    sleep 300
done
