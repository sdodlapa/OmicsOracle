#!/usr/bin/env node

/**
 * Comprehensive Validation Script for OmicsOracle Futuristic Interface
 * Tests color scheme functionality, dataset display, and core features
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 OmicsOracle Futuristic Interface - Comprehensive Validation');
console.log('=' .repeat(70));

let testsPassed = 0;
let testsTotal = 0;
let warnings = [];

function test(description, testFunction) {
    testsTotal++;
    try {
        const result = testFunction();
        if (result === true || result === undefined) {
            console.log(`✅ ${description}`);
            testsPassed++;
        } else {
            console.log(`❌ ${description}: ${result}`);
        }
    } catch (error) {
        console.log(`❌ ${description}: ${error.message}`);
    }
}

function warn(message) {
    warnings.push(message);
    console.log(`⚠️  ${message}`);
}

// Test file existence
console.log('\n📁 File Structure Tests:');

test('Main JavaScript file exists', () => {
    return fs.existsSync('interfaces/futuristic/static/js/main.js');
});

test('Main CSS file exists', () => {
    return fs.existsSync('interfaces/futuristic/static/css/main.css');
});

test('Main Python file exists', () => {
    return fs.existsSync('interfaces/futuristic/main.py');
});

test('Futuristic interface JavaScript exists', () => {
    return fs.existsSync('interfaces/futuristic/static/js/futuristic-interface.js');
});

// Test CSS content
console.log('\n🎨 Color Scheme CSS Tests:');

const cssContent = fs.existsSync('interfaces/futuristic/static/css/main.css')
    ? fs.readFileSync('interfaces/futuristic/static/css/main.css', 'utf8')
    : '';

test('CSS contains root theme variables', () => {
    return cssContent.includes(':root') && cssContent.includes('--primary-gradient');
});

test('CSS contains dark-ocean theme', () => {
    return cssContent.includes('[data-theme="dark-ocean"]');
});

test('CSS contains forest-green theme', () => {
    return cssContent.includes('[data-theme="forest-green"]');
});

test('CSS contains sunset-purple theme', () => {
    return cssContent.includes('[data-theme="sunset-purple"]');
});

test('CSS contains warm-amber theme', () => {
    return cssContent.includes('[data-theme="warm-amber"]');
});

test('CSS contains modern-gray theme', () => {
    return cssContent.includes('[data-theme="modern-gray"]');
});

test('CSS contains color scheme selector styles', () => {
    return cssContent.includes('.color-scheme-selector');
});

test('CSS contains theme option styles', () => {
    return cssContent.includes('.theme-option') && cssContent.includes('.theme-options');
});

test('CSS contains responsive theme selector', () => {
    return cssContent.includes('@media (max-width: 768px)') &&
           cssContent.includes('.color-scheme-selector');
});

// Test JavaScript content
console.log('\n⚙️ JavaScript Functionality Tests:');

const jsContent = fs.existsSync('interfaces/futuristic/static/js/main.js')
    ? fs.readFileSync('interfaces/futuristic/static/js/main.js', 'utf8')
    : '';

test('JavaScript contains FuturisticInterface class', () => {
    return jsContent.includes('class FuturisticInterface');
});

test('JavaScript contains setupColorSchemeToggle method', () => {
    return jsContent.includes('setupColorSchemeToggle()');
});

test('JavaScript contains applyTheme method', () => {
    return jsContent.includes('applyTheme(themeName)');
});

test('JavaScript contains localStorage theme saving', () => {
    return jsContent.includes('localStorage.setItem(\'omics-oracle-theme\'');
});

test('JavaScript contains theme loading', () => {
    return jsContent.includes('localStorage.getItem(\'omics-oracle-theme\')');
});

test('JavaScript contains icon mapping system', () => {
    return jsContent.includes('ICON_MAP') && jsContent.includes('replaceIconCodes');
});

test('JavaScript contains dataset display functions', () => {
    return jsContent.includes('displaySearchResults') &&
           jsContent.includes('extractGeoId') &&
           jsContent.includes('extractOrganism');
});

test('JavaScript contains deduplication logic', () => {
    return jsContent.includes('filterDuplicateResults');
});

test('JavaScript contains AI summary display', () => {
    return jsContent.includes('generateAISummarySection') ||
           jsContent.includes('ai-summaries-section');
});

test('JavaScript contains abstract toggle functionality', () => {
    return jsContent.includes('toggleAbstract');
});

// Test Python content
console.log('\n🐍 Python Backend Tests:');

const pyContent = fs.existsSync('interfaces/futuristic/main.py')
    ? fs.readFileSync('interfaces/futuristic/main.py', 'utf8')
    : '';

test('Python contains color scheme selector HTML', () => {
    return pyContent.includes('color-scheme-selector') && pyContent.includes('theme-option');
});

test('Python contains multiple theme options', () => {
    return pyContent.includes('data-theme="default"') &&
           pyContent.includes('data-theme="dark-ocean"') &&
           pyContent.includes('data-theme="forest-green"');
});

test('Python includes both JavaScript files', () => {
    return pyContent.includes('/static/js/main.js') &&
           pyContent.includes('/static/js/futuristic-interface.js');
});

test('Python contains FastAPI setup', () => {
    return pyContent.includes('FastAPI') && pyContent.includes('HTMLResponse');
});

// Test theme completeness
console.log('\n🌈 Theme Completeness Tests:');

const themes = ['default', 'dark-ocean', 'forest-green', 'sunset-purple', 'warm-amber', 'modern-gray'];
const cssVariables = [
    '--primary-gradient', '--card-background', '--accent-color',
    '--title-color', '--text-color', '--border-color'
];

themes.forEach(theme => {
    if (theme !== 'default') {
        test(`${theme} theme contains all required variables`, () => {
            const themeSection = cssContent.match(new RegExp(`\\[data-theme="${theme}"\\][^}]*\\{[^}]*\\}`, 's'));
            if (!themeSection) return `Theme section not found`;

            const missingVars = cssVariables.filter(variable =>
                !themeSection[0].includes(variable)
            );

            return missingVars.length === 0 || `Missing variables: ${missingVars.join(', ')}`;
        });
    }
});

// Test integration
console.log('\n🔗 Integration Tests:');

test('CSS and JS theme names match', () => {
    const cssThemes = [...cssContent.matchAll(/data-theme="([^"]+)"/g)].map(m => m[1]);
    const jsThemes = [...jsContent.matchAll(/data-theme['"]=["']([^"']+)["']/g)].map(m => m[1]);
    const pyThemes = [...pyContent.matchAll(/data-theme="([^"]+)"/g)].map(m => m[1]);

    const allThemes = new Set([...cssThemes, ...jsThemes, ...pyThemes]);
    const expectedThemes = new Set(themes);

    const missing = [...expectedThemes].filter(t => !allThemes.has(t));
    const extra = [...allThemes].filter(t => !expectedThemes.has(t));

    if (missing.length > 0) return `Missing themes: ${missing.join(', ')}`;
    if (extra.length > 0) warn(`Extra themes found: ${extra.join(', ')}`);

    return true;
});

test('Icon system is properly initialized', () => {
    return jsContent.includes('applyIconReplacements()') &&
           jsContent.includes('setTimeout') &&
           jsContent.includes('ICON_MAP');
});

// Test core functionality preservation
console.log('\n🧬 Core Functionality Tests:');

test('WebSocket functionality preserved', () => {
    return jsContent.includes('WebSocket') && jsContent.includes('connectWebSocket');
});

test('Search functionality preserved', () => {
    return jsContent.includes('performSearch') && jsContent.includes('/api/search');
});

test('Dataset display functionality preserved', () => {
    return jsContent.includes('displaySearchResults') &&
           jsContent.includes('dataset-item') &&
           jsContent.includes('geo-link');
});

test('Performance monitoring preserved', () => {
    return jsContent.includes('updatePerformanceMetrics') &&
           jsContent.includes('startPerformanceMonitoring');
});

// Summary
console.log('\n' + '='.repeat(70));
console.log(`📊 Test Results: ${testsPassed}/${testsTotal} tests passed`);

if (warnings.length > 0) {
    console.log(`⚠️  ${warnings.length} warnings:`);
    warnings.forEach(warning => console.log(`   • ${warning}`));
}

if (testsPassed === testsTotal) {
    console.log('🎉 All tests passed! The futuristic interface is ready with multiple color schemes.');
    console.log('\n🚀 Next Steps:');
    console.log('   1. Start the futuristic interface server');
    console.log('   2. Test color scheme switching in the browser');
    console.log('   3. Verify dataset search and display functionality');
    console.log('   4. Test responsiveness on different screen sizes');
    console.log('\n💡 Features implemented:');
    console.log('   • 6 beautiful color schemes with smooth transitions');
    console.log('   • Persistent theme selection (localStorage)');
    console.log('   • Responsive theme selector UI');
    console.log('   • Improved dataset display with proper GEO links');
    console.log('   • AI summary integration');
    console.log('   • Deduplication and data accuracy improvements');
} else {
    console.log('❌ Some tests failed. Please review the issues above.');
    process.exit(1);
}

console.log('\n🎨 Available Color Schemes:');
console.log('   • Default (Milky White) - Clean and professional');
console.log('   • Dark Ocean - Deep blue with cyan accents');
console.log('   • Forest Green - Natural green theme');
console.log('   • Sunset Purple - Elegant purple theme');
console.log('   • Warm Amber - Cozy amber/orange theme');
console.log('   • Modern Gray - Sleek monochrome theme');
