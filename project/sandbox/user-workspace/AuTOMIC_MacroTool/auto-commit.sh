#!/bin/bash

while true; do
    git add .
    if git diff --staged --quiet; then
        echo "No changes to commit"
    else
        git commit -m "Auto-commit: $(date)"
    fi
    sleep 300  # czeka 5 minut przed następnym sprawdzeniem
done
