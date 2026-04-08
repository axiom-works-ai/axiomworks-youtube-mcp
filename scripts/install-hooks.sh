#!/usr/bin/env bash
# Install gitleaks pre-commit hook for security scanning.
# Usage: ./scripts/install-hooks.sh
set -euo pipefail

GREEN='\033[92m'
RED='\033[91m'
YELLOW='\033[93m'
RESET='\033[0m'

echo "Installing security hooks..."

# Check gitleaks
if ! command -v gitleaks &>/dev/null; then
    echo -e "${YELLOW}gitleaks not found. Installing via brew...${RESET}"
    if command -v brew &>/dev/null; then
        brew install gitleaks
    else
        echo -e "${RED}brew not found. Install gitleaks manually: https://github.com/gitleaks/gitleaks${RESET}"
        exit 1
    fi
fi

echo -e "${GREEN}gitleaks $(gitleaks version) installed${RESET}"

# Install pre-commit hook
HOOK_PATH=".git/hooks/pre-commit"

if [ ! -d ".git" ]; then
    echo -e "${RED}Not a git repository. Run from the repo root.${RESET}"
    exit 1
fi

mkdir -p .git/hooks

cat > "$HOOK_PATH" << 'HOOK'
#!/usr/bin/env bash
# Pre-commit hook: gitleaks secret scanning
# Installed by scripts/install-hooks.sh

if ! command -v gitleaks &>/dev/null; then
    echo "WARNING: gitleaks not installed. Skipping pre-commit scan."
    echo "Install: brew install gitleaks"
    exit 0
fi

# Scan staged changes only
gitleaks protect --config .gitleaks.toml --staged --verbose

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Commit blocked by gitleaks — sensitive data detected."
    echo "Fix the issues above, or use 'git commit --no-verify' to bypass (not recommended)."
    exit 1
fi
HOOK

chmod +x "$HOOK_PATH"
echo -e "${GREEN}Pre-commit hook installed at ${HOOK_PATH}${RESET}"
echo "Every commit will now be scanned for secrets and internal data."
