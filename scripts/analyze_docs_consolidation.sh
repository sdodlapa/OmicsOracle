#!/bin/bash

# Analyze documentation for consolidation opportunities

cd /Users/sanjeevadodlapati/Downloads/Repos/OmicsOracle/docs

echo "════════════════════════════════════════════════════════════════"
echo "  Documentation Consolidation Analysis"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Count by directory
echo "📊 Documentation Distribution:"
echo ""
echo "Active Documentation:"
for dir in . guides testing architecture planning reports summaries; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
        echo "  $dir/: $count files"
    fi
done

echo ""
echo "Archives:"
find archive -type d -name "*2025*" 2>/dev/null | while read archive_dir; do
    count=$(find "$archive_dir" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "  $archive_dir: $count files"
done

echo ""
echo "━━━ Potential Duplicates & Consolidation Opportunities ━━━"
echo ""

# Check for similar filenames
echo "📋 Files with similar names (potential duplicates):"
find . -name "*.md" ! -path "*/archive/*" -type f -exec basename {} \; | sort | \
    sed 's/_/ /g; s/-/ /g' | awk '{print tolower($0)}' | sort | uniq -c | \
    awk '$1 > 1 {print "  ⚠️  Similar: " $0}'

echo ""
echo "📋 Guide Files:"
find guides -name "*.md" 2>/dev/null | head -20

echo ""
echo "📋 Testing Files:"
find testing -name "*.md" 2>/dev/null | head -10

echo ""
echo "📋 Architecture Files:"
find architecture -name "*.md" 2>/dev/null | head -10

echo ""
echo "━━━ Consolidation Assessment ━━━"
echo ""

TOTAL_ACTIVE=$(find . -name "*.md" ! -path "*/archive/*" -type f 2>/dev/null | wc -l | tr -d ' ')
TOTAL_ARCHIVED=$(find archive -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ')

echo "Total active docs: $TOTAL_ACTIVE"
echo "Total archived: $TOTAL_ARCHIVED"
echo ""

# Assess complexity
if [ $TOTAL_ACTIVE -lt 60 ]; then
    echo "✅ RECOMMENDATION: Good organization (< 60 files)"
    echo "   Option A NOT necessary - current structure is manageable"
elif [ $TOTAL_ACTIVE -lt 100 ]; then
    echo "⚠️  RECOMMENDATION: Consider light consolidation (60-100 files)"
    echo "   Option A OPTIONAL - could benefit from minor cleanup"
else
    echo "❌ RECOMMENDATION: Consolidation needed (> 100 files)"
    echo "   Option A RECOMMENDED - too many files for easy navigation"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
