#!/bin/bash

# BizPulse ERP - Quick Deployment Script

echo "🚀 BizPulse ERP Deployment Script"
echo "=================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
fi

# Add all files
echo "📝 Adding files to Git..."
git add .

# Commit changes
echo "💾 Committing changes..."
read -p "Enter commit message (or press Enter for default): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Update BizPulse ERP - $(date '+%Y-%m-%d %H:%M:%S')"
fi
git commit -m "$commit_msg"

# Check if remote exists
if ! git remote | grep -q "origin"; then
    echo ""
    echo "🔗 No remote repository found."
    echo "Please create a repository on GitHub first, then run:"
    echo "git remote add origin https://github.com/YOUR_USERNAME/bizpulse-erp.git"
    echo ""
    read -p "Enter your GitHub repository URL: " repo_url
    if [ ! -z "$repo_url" ]; then
        git remote add origin "$repo_url"
        echo "✅ Remote added!"
    fi
fi

# Push to GitHub
echo ""
echo "📤 Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✅ Code pushed to GitHub successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Go to https://dashboard.render.com/"
echo "2. Click 'New +' → 'Web Service'"
echo "3. Connect your GitHub repository"
echo "4. Render will auto-detect render.yaml and deploy!"
echo ""
echo "🎉 Your app will be live in 5-10 minutes!"
