#!/bin/bash
# Automated cleanup script for OmicsOracle
# Created: October 16, 2025

set -e

echo "🧹 Starting OmicsOracle cleanup..."

# Remove Python cache files
echo "📦 Cleaning Python cache..."
find . -type d -name "__pycache__" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -not -path "./venv/*" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -not -path "./venv/*" -delete 2>/dev/null || true

# Remove OS files
echo "🍎 Cleaning OS artifacts..."
find . -type f -name ".DS_Store" -delete 2>/dev/null || true

# Clean temp directories
echo "🗑️  Cleaning temp directory..."
if [ -d "temp" ]; then
    rm -rf temp/*
    mkdir -p temp
    touch temp/.gitkeep
fi

# Clean pytest cache
echo "🧪 Cleaning pytest cache..."
if [ -d ".pytest_cache" ]; then
    rm -rf .pytest_cache/*
fi

# Clean coverage HTML (but keep .coverage data file)
echo "📊 Cleaning HTML coverage reports..."
if [ -d "htmlcov" ]; then
    rm -rf htmlcov/*
fi

# Show what was cleaned
echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📈 Statistics:"
echo "   - Python cache removed"
echo "   - OS artifacts removed"
echo "   - Temporary files removed"
echo "   - Test cache cleaned"
echo "   - Coverage HTML removed"
echo ""
echo "💡 Tip: Run 'make test' to regenerate coverage reports"
