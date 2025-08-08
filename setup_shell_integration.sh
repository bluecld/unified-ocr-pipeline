#!/bin/sh

# VS Code Shell Integration Helper for /bin/sh
# This script helps improve command detection in VS Code terminals

echo "🔧 VS Code Shell Integration Setup"
echo "=================================="

# Check current environment
echo "Current shell: $SHELL"
echo "Terminal: $TERM"
echo "VS Code detected: ${VSCODE_INJECTION:-No}"

# Create a more feature-rich shell profile
PROFILE_FILE="$HOME/.profile"

echo ""
echo "📝 Setting up enhanced shell profile..."

# Create or update .profile with VS Code integration helpers
cat > "$PROFILE_FILE" << 'EOF'
# Enhanced shell profile for VS Code integration

# Set better prompt for command detection
if [ -n "$VSCODE_INJECTION" ]; then
    # VS Code terminal detected
    export PS1='\u@\h:\w# '
    
    # Enable command line editing
    set -o emacs 2>/dev/null || true
    
    # History settings
    export HISTSIZE=1000
    export HISTFILESIZE=2000
    
    # Better terminal settings
    export TERM=${TERM:-xterm-256color}
    
    # Path helpers
    export PATH="$PATH:/usr/local/bin:/usr/bin:/bin"
    
    # VS Code integration markers
    echo "VS Code shell integration active"
fi

# Aliases for better command detection
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'

# Function to show current directory in a VS Code-friendly way
pwd_prompt() {
    echo "📁 Current directory: $(pwd)"
}

# Git helpers if available
if command -v git >/dev/null 2>&1; then
    alias gs='git status'
    alias ga='git add'
    alias gc='git commit'
    alias gp='git push'
fi

# Docker helpers if available
if command -v docker >/dev/null 2>&1; then
    alias dps='docker ps'
    alias di='docker images'
    alias dc='docker-compose'
fi

EOF

# Source the profile
if [ -f "$PROFILE_FILE" ]; then
    . "$PROFILE_FILE"
    echo "✅ Profile loaded: $PROFILE_FILE"
else
    echo "❌ Failed to create profile"
fi

echo ""
echo "🎯 VS Code Shell Integration Tips:"
echo "1. Restart your VS Code terminal"
echo "2. Use 'Command Palette' > 'Terminal: Select Default Profile'"
echo "3. Consider switching to bash/zsh for better integration"
echo "4. Enable 'terminal.integrated.shellIntegration.enabled' in settings"

echo ""
echo "📋 Current integration status:"
if [ -n "$VSCODE_INJECTION" ]; then
    echo "   ✅ VS Code terminal detected"
else
    echo "   📝 Not in VS Code terminal (run from VS Code for full integration)"
fi

echo ""
echo "🔄 To apply changes, run: source ~/.profile"
