#!/bin/bash

# Script to remove sensitive files from git history
# WARNING: This will rewrite git history - make sure to backup first!

echo "🚨 WARNING: This script will rewrite git history!"
echo "Make sure you have:"
echo "1. Revoked all API keys found in .env files"
echo "2. Backed up your repository"
echo "3. Coordinated with team members if this is a shared repo"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "🧹 Removing sensitive files from git history..."

# Remove .env file and log files from history
echo "Using git filter-branch..."
git filter-branch --force --index-filter \
    'git rm --cached --ignore-unmatch .env
     git rm --cached --ignore-unmatch logs/*.log
     git rm --cached --ignore-unmatch logs/*.json' \
    --prune-empty --tag-name-filter cat -- --all

# Clean up refs
echo "🧹 Cleaning up refs..."
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "🔄 Next steps:"
echo "1. Force push to remote: git push origin --force --all"
echo "2. Force push tags: git push origin --force --tags"
echo "3. Ask collaborators to clone fresh copy"
echo "4. Create new API keys and add them to new .env file"
echo ""
echo "⚠️  Note: .env and log files are now properly ignored by .gitignore" 