#!/bin/sh

echo "🧪 VS Code Shell Integration Status Check"
echo "========================================="

# Check current status
echo "📊 Current Status:"
echo "  • Terminal Program: ${TERM_PROGRAM:-Unknown}"
echo "  • VS Code Injection: ${VSCODE_INJECTION:-❌ Not active}"
echo "  • Shell: $SHELL"
echo "  • Term Type: $TERM"

# Test enhanced features
echo ""
echo "🔧 Enhanced Features Test:"
echo "  • pwd_prompt function: $(type pwd_prompt >/dev/null 2>&1 && echo '✅ Available' || echo '❌ Not loaded')"
echo "  • ll alias: $(alias ll >/dev/null 2>&1 && echo '✅ Available' || echo '❌ Not set')"

# Set up features if not available
if ! alias ll >/dev/null 2>&1; then
    alias ll='ls -la'
    alias la='ls -A'
    alias l='ls -CF'
    echo "  ✅ Aliases configured"
fi

# Test a command that should show integration
echo ""
echo "🎯 Testing Command Integration:"
echo "Running: ls -la | head -3"
ls -la | head -3

echo ""
echo "💡 What to Look For in VS Code:"
echo "1. 🟢 Green checkmarks next to successful commands"
echo "2. 🔴 Red X marks next to failed commands"  
echo "3. ⏱️  Command duration indicators"
echo "4. 🔗 Clickable command history"

echo ""
echo "🔧 To Enable Full Integration:"
echo "1. In VS Code: Ctrl+, (Settings)"
echo "2. Search: 'shell integration'"
echo "3. Enable: ✅ Terminal > Integrated > Shell Integration: Enabled"
echo "4. Enable: ✅ Terminal > Integrated > Shell Integration: Decorations"
echo "5. Restart this terminal (Ctrl+Shift+\`)"

echo ""
if [ "$TERM_PROGRAM" = "vscode" ]; then
    echo "✅ You're in VS Code terminal - just need to enable settings!"
else
    echo "📝 Not detected as VS Code terminal"
fi
