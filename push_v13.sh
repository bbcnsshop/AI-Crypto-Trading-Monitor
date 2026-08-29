#!/bin/bash
cd /Users/Parinya/VSCode/BinanceMonitor
git add -A
git commit -m "v1.3: Refactor main.py into modules + AI Smart Trigger + Display Modes"
git push origin main
echo "DONE!"
#!/bin/bash
cd /Users/Parinya/VSCode/BinanceMonitor

echo "=== Staging files ==="
git add -A

echo ""
echo "=== Git Status ==="
git status

echo ""
echo "=== Committing ==="
git commit -m "Add AI Smart Trigger + Cooldown System (v1.3) + CHANGELOG.md"

echo ""
echo "=== Pushing to GitHub ==="
git push origin main

echo ""
echo "=== DONE! ==="
