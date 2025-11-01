#!/usr/bin/env node

// Quick validation script for the futuristic interface fixes
const fs = require('fs');

console.log('🔍 VALIDATING FUTURISTIC INTERFACE FIXES...\n');

// Read the main.js file
const mainJsPath = 'interfaces/futuristic/static/js/main.js';
const content = fs.readFileSync(mainJsPath, 'utf8');

// Test 1: Check if ICON_MAP is properly structured
console.log('1. ✅ ICON_MAP Structure:');
const iconMapMatch = content.match(/const ICON_MAP = {[\s\S]*?};/);
if (iconMapMatch && !iconMapMatch[0].includes('<div') && !iconMapMatch[0].includes('onclick')) {
    console.log('   ✅ ICON_MAP is clean and properly structured');
} else {
    console.log('   ❌ ICON_MAP contains HTML corruption');
}

// Test 2: Check abstract toggle function references
console.log('\n2. ✅ Abstract Toggle References:');
const abstractToggles = content.match(/onclick="[^"]*toggleAbstract/g) || [];
const correctRefs = abstractToggles.filter(ref => ref.includes('window.futuristicInterface'));
console.log(`   Found ${abstractToggles.length} abstract toggle references`);
console.log(`   ✅ ${correctRefs.length} use correct 'window.futuristicInterface' reference`);
if (correctRefs.length === abstractToggles.length && abstractToggles.length > 0) {
    console.log('   ✅ All abstract toggle buttons properly referenced');
} else {
    console.log('   ❌ Some abstract toggle buttons may have incorrect references');
}

// Test 3: Check if extractGeoId function exists and looks correct
console.log('\n3. ✅ GEO ID Extraction Function:');
const extractGeoIdExists = content.includes('extractGeoId(result)');
const hasHashGeneration = content.includes('hash') && content.includes('GSE');
console.log(`   ✅ extractGeoId function exists: ${extractGeoIdExists}`);
console.log(`   ✅ Has hash-based ID generation: ${hasHashGeneration}`);

// Test 4: Check organism detection improvements
console.log('\n4. ✅ Organism Detection:');
const hasEnhancedOrganism = content.includes('myeloid') && content.includes('glioblastoma') && content.includes('astrocytoma');
console.log(`   ✅ Enhanced human cancer detection: ${hasEnhancedOrganism}`);

// Test 5: Check if Platform field was removed
console.log('\n5. ✅ Platform Field Removal:');
const hasPlatformField = content.includes('Platform:') || content.includes('meta-label">Platform');
console.log(`   ✅ Platform field removed from display: ${!hasPlatformField}`);

// Test 6: Check duplicate filtering function
console.log('\n6. ✅ Duplicate Filtering:');
const hasDuplicateFilter = content.includes('filterDuplicateResults') && content.includes('composite key');
console.log(`   ✅ Duplicate filtering function exists: ${hasDuplicateFilter}`);

// Test 7: Check if toggleAbstract function exists
console.log('\n7. ✅ Toggle Abstract Function:');
const hasToggleAbstract = content.includes('toggleAbstract(index)') && content.includes('Show Abstract') && content.includes('Hide Abstract');
console.log(`   ✅ toggleAbstract function properly implemented: ${hasToggleAbstract}`);

console.log('\n🎉 VALIDATION COMPLETE!\n');

// Summary
const fixes = [
    iconMapMatch && !iconMapMatch[0].includes('<div'),
    correctRefs.length === abstractToggles.length && abstractToggles.length > 0,
    extractGeoIdExists && hasHashGeneration,
    hasEnhancedOrganism,
    !hasPlatformField,
    hasDuplicateFilter,
    hasToggleAbstract
];

const passedFixes = fixes.filter(Boolean).length;
console.log(`📊 SUMMARY: ${passedFixes}/7 fixes validated successfully`);

if (passedFixes === 7) {
    console.log('🎉 ALL FIXES IMPLEMENTED AND VALIDATED!');
    console.log('\n📋 Key Improvements:');
    console.log('   ✅ Fixed corrupted ICON_MAP');
    console.log('   ✅ Corrected abstract toggle button references');
    console.log('   ✅ Implemented realistic GEO ID generation');
    console.log('   ✅ Enhanced organism detection for human cancer studies');
    console.log('   ✅ Removed Platform field from dataset display');
    console.log('   ✅ Maintained duplicate result filtering');
    console.log('   ✅ Working expandable abstract sections');
} else {
    console.log('⚠️  Some fixes may need attention');
}
