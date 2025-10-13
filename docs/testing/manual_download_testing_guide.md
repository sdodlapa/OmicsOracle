# Manual Download Testing Guide

## Test 1: Dataset with PMIDs (should show Download button)
Search: "alzheimer"
Expected: GSE308813 shows "📥 Download 3 Papers" button
Expected: AI Analysis button is disabled (gray)

## Test 2: Click Download Button
Action: Click "📥 Download 3 Papers"
Expected: Button changes to "⏳ Downloading..."
Expected: Wait 10-20 seconds
Expected: Success alert: "✓ Successfully downloaded X papers!"
Expected: Button changes to "🤖 AI Analysis" with "✓ X PDFs" badge
Expected: AI Analysis button is now enabled (purple)

## Test 3: Click AI Analysis
Action: Click "🤖 AI Analysis"
Expected: Analysis section expands
Expected: Shows full-text sections (Methods, Results, Discussion)

## Test 4: Dataset without PMIDs (should be disabled)
Search: "breast cancer" (recent datasets)
Expected: Datasets with no PMIDs show disabled AI button
Expected: No Download button (nothing to download)
Expected: Badge says "No Publications"
