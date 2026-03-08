#!/bin/bash

# ==========================================
# Quick Git Push Script (No Confirmation)
# ==========================================
# Usage: 
#   ./git_push_quick.sh "commit message"
# ==========================================

# Get commit message from parameter
if [ -z "$1" ]; then
    echo "Error: Commit message is required"
    echo "Usage: ./git_push_quick.sh \"your commit message\""
    exit 1
fi

COMMIT_MSG="$1"
TARGET_REMOTE="https://github.com/neostar-ja/vmstat.git"
# ensure origin points to correct repo
if git remote | grep -q '^origin$'; then
    CUR_URL=$(git remote get-url origin)
    if [ "$CUR_URL" != "$TARGET_REMOTE" ]; then
        echo "Updating origin URL to ${TARGET_REMOTE}"
        git remote set-url origin "$TARGET_REMOTE"
    fi
else
    echo "Adding origin remote ${TARGET_REMOTE}"
    git remote add origin "$TARGET_REMOTE"
fi

CURRENT_BRANCH=$(git branch --show-current)

echo "🚀 Quick Push to ${CURRENT_BRANCH}..."

# Add, commit, and push in one go
git add . && \
git commit -m "${COMMIT_MSG}" && \
git push origin ${CURRENT_BRANCH}

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed!"
else
    echo "❌ Failed to push"
    exit 1
fi
