#!/bin/sh

echo "🔧 VS Code Shell Integration Troubleshooting"
echo "============================================"

echo ""
echo "📋 Quick Visual Check:"
echo "After restarting, look at the LEFT SIDE of your terminal lines."
echo "You should see:"
echo "  ✅ Green checkmarks for successful commands"
echo "  ❌ Red X marks for failed commands"
echo "  ⏱️  Duration indicators (like '2.1s')"

echo ""
echo "🔍 If you DON'T see decorations, try these steps:"

echo ""
echo "Step 1: Check VS Code Settings"
echo "   → Press Ctrl+Shift+P"
echo "   → Type: 'Preferences: Open Settings (JSON)'"
echo "   → Add these lines:"
echo '   {'
echo '     "terminal.integrated.shellIntegration.enabled": true,'
echo '     "terminal.integrated.shellIntegration.decorationsEnabled": "both",'
echo '     "terminal.integrated.shellIntegration.showWelcome": false'
echo '   }'

echo ""
echo "Step 2: Check VS Code Version"
echo "   → Help > About"
echo "   → Shell integration requires VS Code 1.70+"

echo ""
echo "Step 3: Force Enable Integration"
echo "   → Command Palette (Ctrl+Shift+P)"
echo "   → Type: 'Terminal: Focus Terminal'"
echo "   → Then: 'Terminal: Toggle Shell Integration'"

echo ""
echo "Step 4: Alternative - Use Command Palette"
echo "   → Ctrl+Shift+P"
echo "   → Type: 'Terminal: Configure Terminal Shell Integration'"

echo ""
echo "Step 5: Manual Test"
echo "Let's test if you can see ANY visual indicators:"

# Test commands with clear success/failure
echo ""
echo "Running test commands - watch for decorations:"
echo "Test A: Success command"
true && echo "Command succeeded"

echo "Test B: Failure command"  
false || echo "Command failed (expected)"

echo "Test C: Timed command"
sleep 1 && echo "Timer completed"

echo ""
echo "🎯 What you should see:"
echo "   • Left margin should have green ✓ or red ✗"
echo "   • Some commands might show timing like '1.2s'"
echo "   • Failed commands should have red decoration"

echo ""
echo "❓ Questions to help debug:"
echo "1. Do you see ANY decorations in the left margin?"
echo "2. What VS Code version are you using?"
echo "3. Are you using VS Code or VS Code Insiders?"
echo "4. Did you enable the settings in VS Code (not on the server)?"

echo ""
echo "💡 Remember: Enable settings in your LOCAL VS Code,"
echo "   not on the remote server!"
