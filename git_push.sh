#!/bin/bash

# ==========================================
# Git Push Script for Sangfor SCP Project
# ==========================================
# Usage: 
#   ./git_push.sh "commit message"
#   ./git_push.sh  (will use default message)
# ==========================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get commit message from parameter or use default
COMMIT_MSG="${1:-Update: $(date +'%Y-%m-%d %H:%M:%S')}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Git Push Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git is not installed${NC}"
    exit 1
fi

# Check if current directory is a git repository
if [ ! -d .git ]; then
    echo -e "${RED}Error: Not a git repository${NC}"
    echo -e "${YELLOW}Please run 'git init' first${NC}"
    exit 1
fi

# Show current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${GREEN}Current branch:${NC} ${YELLOW}${CURRENT_BRANCH}${NC}"
echo ""

# Show git status
echo -e "${BLUE}Checking git status...${NC}"
git status
echo ""

# Ask for confirmation
echo -e "${YELLOW}Files will be added, committed, and pushed with message:${NC}"
echo -e "${GREEN}\"${COMMIT_MSG}\"${NC}"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Cancelled by user${NC}"
    exit 1
fi

# Add all files
echo -e "${BLUE}Adding files...${NC}"
git add .

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to add files${NC}"
    exit 1
fi

echo -e "${GREEN}Files added successfully${NC}"
echo ""

# Commit
echo -e "${BLUE}Committing changes...${NC}"
git commit -m "${COMMIT_MSG}"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to commit${NC}"
    echo -e "${YELLOW}(This may be because there are no changes to commit)${NC}"
    exit 1
fi

echo -e "${GREEN}Committed successfully${NC}"
echo ""

# Push to remote
echo -e "${BLUE}Pushing to remote repository...${NC}"
git push origin ${CURRENT_BRANCH}

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to push to remote${NC}"
    echo -e "${YELLOW}Tip: You may need to set up the remote repository or check your credentials${NC}"
    echo -e "${YELLOW}Run: git remote -v to check remote repositories${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Successfully pushed to git!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Branch:${NC} ${CURRENT_BRANCH}"
echo -e "${GREEN}Commit:${NC} ${COMMIT_MSG}"
echo ""
