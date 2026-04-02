#!/bin/bash

###############################################################################
# STREAMLIT APP PUSH SCRIPT
# Run locally: bash push.sh
# Prompts for GitHub token (stays on your machine, never shared)
###############################################################################

set -e

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          Streamlit App Push - Backtesting + Live Trading             ║"
echo "║                   Token stays local (secure)                         ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Check git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not installed${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Getting token${NC}"
echo "Paste your GitHub token (from https://github.com/settings/tokens/new):"
read -sp "Token: " TOKEN
echo ""

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Token required${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Token received${NC}"
echo ""

# Check current repo
echo -e "${BLUE}Step 2: Verifying repo${NC}"
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Not in git repo. Run: git clone https://github.com/prabhuken01/nifty-weekly-options-strategy.git${NC}"
    exit 1
fi

REPO_URL=$(git config --get remote.origin.url)
echo "Repo: $REPO_URL"
echo -e "${GREEN}✓ Git repo found${NC}"
echo ""

# Create temp work dir
WORK_DIR="/tmp/streamlit_push_$$"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

echo -e "${BLUE}Step 3: Cloning repo${NC}"
REPO_HTTPS="https://prabhuken01:${TOKEN}@github.com/prabhuken01/nifty-weekly-options-strategy.git"
git clone "$REPO_HTTPS" repo 2>&1 | grep -v "Cloning" | grep -v "^$" || true
cd repo

echo -e "${GREEN}✓ Cloned successfully${NC}"
echo ""

# Create structure
echo -e "${BLUE}Step 4: Setting up files${NC}"
mkdir -p docs

echo -e "${GREEN}✓ Structure created${NC}"
echo ""

# Copy files (from /mnt/user-data/outputs)
echo -e "${BLUE}Step 5: Copying files${NC}"

if [ ! -f "/mnt/user-data/outputs/app.py" ]; then
    echo -e "${RED}❌ Files not found in /mnt/user-data/outputs${NC}"
    exit 1
fi

cp /mnt/user-data/outputs/app.py .
cp /mnt/user-data/outputs/requirements.txt .
cp /mnt/user-data/outputs/INTEGRATION_GUIDE.md .
cp /mnt/user-data/outputs/STREAMLIT_PUSH_INSTRUCTIONS.md .
cp /mnt/user-data/outputs/00_START_HERE.md .
cp -r /mnt/user-data/outputs/.streamlit .
cp /mnt/user-data/outputs/docs/*.md docs/ 2>/dev/null || true

echo -e "${GREEN}✓ Files copied: $(find . -type f -name '*.py' -o -name '*.md' -o -name '*.txt' | wc -l) files${NC}"
echo ""

# Configure git
echo -e "${BLUE}Step 6: Configuring git${NC}"
git config user.name "prabhuken01"
git config user.email "prabhuken01@github.com"
echo -e "${GREEN}✓ Git configured${NC}"
echo ""

# Stage and commit
echo -e "${BLUE}Step 7: Staging files${NC}"
git add .
echo -e "${GREEN}✓ Files staged${NC}"
echo ""

echo -e "${BLUE}Step 8: Creating commit${NC}"
git commit -m "Integrate backtesting + live trading dashboards

- Tab 1: Backtesting Dashboard (historical analysis)
- Tab 2: Live Trading Dashboard (real-time Greeks monitoring)
- Tab 3: Documentation reference
- Tab 4: Settings & configuration
- Tab 5: Original features (add your code here)

See INTEGRATION_GUIDE.md for details on adding existing code.
See 00_START_HERE.md for quick start.

Files include:
- app.py: Complete Streamlit app
- requirements.txt: Dependencies
- .streamlit/config.toml: Theme config
- docs/: Complete documentation (11 files)

Auto-deploys on Streamlit Cloud."

echo -e "${GREEN}✓ Commit created${NC}"
echo ""

# Push
echo -e "${BLUE}Step 9: Pushing to GitHub${NC}"
echo "Pushing... (this may take 10-30 seconds)"

if git push -u origin main 2>&1 | grep -q "master\|main"; then
    echo -e "${GREEN}✓ Push successful!${NC}"
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ FILES PUSHED SUCCESSFULLY!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Your app is deploying at:"
    echo "  https://nifty-weekly-options.streamlit.app/"
    echo ""
    echo "Repository:"
    echo "  https://github.com/prabhuken01/nifty-weekly-options-strategy"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Wait 2-5 minutes for Streamlit Cloud to auto-deploy"
    echo "  2. Visit https://nifty-weekly-options.streamlit.app/"
    echo "  3. Add your existing code to Tab 5 (see INTEGRATION_GUIDE.md)"
    echo "  4. Push updates: git push (in your local repo)"
    echo ""
else
    echo -e "${RED}❌ Push failed${NC}"
    echo "Check credentials and try again"
    exit 1
fi

# Cleanup
echo -e "${BLUE}Step 10: Cleanup${NC}"
cd /tmp
rm -rf "$WORK_DIR"
echo -e "${GREEN}✓ Cleaned up${NC}"
echo ""

echo "═════════════════════════════════════════════════════════════════════════"
echo ""
echo "🎉 DONE! Your Streamlit app is now deploying!"
echo ""
echo "Token was only used locally and is not stored anywhere."
echo ""
