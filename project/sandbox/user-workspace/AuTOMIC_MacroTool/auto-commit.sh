#!/bin/bash

echo "Auto-commit script started at $(date)"
cd /project/sandbox/user-workspace/AuTOMIC_MacroTool

while true; do
    echo "Checking for changes at $(date)..."
    
    # Zapisz aktualne zmiany
    git add .
    if ! git diff --staged --quiet; then
        echo "Changes detected, committing..."
        git commit -m "Auto-commit: $(date)"
    fi
    
    # Pobierz i połącz zmiany z GitHuba
    echo "Synchronizing with GitHub..."
    if git pull origin main --rebase; then
        # Jeśli są lokalne commity, wypchnij je
        if git log origin/main..HEAD | grep -q .; then
            echo "Pushing changes to GitHub..."
            if git push origin main; then
                echo "Changes successfully pushed to GitHub"
            else
                echo "Error pushing changes to GitHub"
            fi
        else
            echo "No local changes to push"
        fi
    else
        echo "Error pulling from GitHub"
    fi
    
    echo "Waiting 5 minutes before next check..."
    sleep 300
done
