#!/bin/bash
# Creates deployment package for Google Drive

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CREATING GOOGLE DRIVE DEPLOYMENT PACKAGE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Create main package directory
mkdir -p AIEmpire-Core-2.0-Package/

# Copy essential files
echo "📋 Copying core files..."
cp empire_engine.py AIEmpire-Core-2.0-Package/
cp AUTOPILOT.py AIEmpire-Core-2.0-Package/
cp ATOMIC_REVENUE_MACHINE.py AIEmpire-Core-2.0-Package/
cp WORKFLOW_EXECUTOR.py AIEmpire-Core-2.0-Package/

# Copy directories
echo "📁 Copying major systems..."
cp -r antigravity AIEmpire-Core-2.0-Package/
cp -r workflow_system AIEmpire-Core-2.0-Package/
cp -r brain_system AIEmpire-Core-2.0-Package/
cp -r crm AIEmpire-Core-2.0-Package/
cp -r scripts AIEmpire-Core-2.0-Package/
cp -r products AIEmpire-Core-2.0-Package/
cp -r docs AIEmpire-Core-2.0-Package/
cp -r gold-nuggets AIEmpire-Core-2.0-Package/

# Copy EXPORT docs
echo "📖 Copying documentation..."
cp -r EXPORT/* AIEmpire-Core-2.0-Package/

# Create compressed archives
echo "🗜️  Creating archives..."
zip -r AIEmpire-Core-2.0.zip AIEmpire-Core-2.0-Package/ -q
tar -czf AIEmpire-Core-2.0.tar.gz AIEmpire-Core-2.0-Package/ 

# Create checksums
echo "🔐 Creating checksums..."
md5 AIEmpire-Core-2.0.zip > AIEmpire-Core-2.0.md5
md5 AIEmpire-Core-2.0.tar.gz > AIEmpire-Core-2.0.tar.gz.md5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ PACKAGE READY FOR GOOGLE DRIVE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ls -lh AIEmpire-Core-2.0.* 

echo ""
echo "NEXT STEPS:"
echo "1. Create folder on Google Drive: 'AIEmpire-Core-2.0'"
echo "2. Upload: AIEmpire-Core-2.0.zip (or .tar.gz)"
echo "3. Share link with team"
echo "4. On new machine: unzip + python3 AUTOPILOT.py"
echo ""

# Cleanup
rm -rf AIEmpire-Core-2.0-Package/

echo "✓ Package created successfully!"
