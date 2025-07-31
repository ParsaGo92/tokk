// Detection Test Suite for Invisible Stealth Framework
(() => {
    console.log('🔍 Starting Detection Tests...\n');
    
    // Test 1: Pattern Analysis
    const testPatternAnalysis = () => {
        console.log('📊 Test 1: Pattern Analysis');
        
        const patterns = [
            /_0x[a-f0-9]{4}/g,
            /new Uint8Array/g,
            /TextEncoder|TextDecoder/g,
            /WebAssembly/g,
            /WeakMap/g,
            /performance\.now/g,
            /navigator\.userAgent/g
        ];
        
        const code = document.querySelector('script[src*="invisible.js"]')?.textContent || '';
        
        patterns.forEach((pattern, index) => {
            const matches = code.match(pattern);
            if (matches) {
                console.log(`❌ Pattern ${index + 1} detected: ${matches.length} matches`);
            } else {
                console.log(`✅ Pattern ${index + 1} not detected`);
            }
        });
        
        console.log('');
    };
    
    // Test 2: Function Name Analysis
    const testFunctionNames = () => {
        console.log('🔤 Test 2: Function Name Analysis');
        
        const suspiciousNames = [
            '_main', '_check', '_store', '_mem', '_crypt', '_rand',
            '_func', '_task', '_obfs', '_event', '_state', '_dyn', '_wasm'
        ];
        
        const foundNames = suspiciousNames.filter(name => window[name] !== undefined);
        
        if (foundNames.length > 0) {
            console.log(`❌ Suspicious function names found: ${foundNames.join(', ')}`);
        } else {
            console.log('✅ No suspicious function names detected');
        }
        
        console.log('');
    };
    
    // Test 3: API Usage Analysis
    const testAPIUsage = () => {
        console.log('🔧 Test 3: API Usage Analysis');
        
        const suspiciousAPIs = [
            'WebAssembly',
            'WeakMap',
            'TextEncoder',
            'TextDecoder',
            'performance.now',
            'navigator.userAgent',
            'navigator.plugins',
            'navigator.languages',
            'window.outerHeight',
            'window.outerWidth',
            'screen.width',
            'screen.height',
            'navigator.hardwareConcurrency'
        ];
        
        const detectedAPIs = [];
        
        suspiciousAPIs.forEach(api => {
            try {
                if (eval(api) !== undefined) {
                    detectedAPIs.push(api);
                }
            } catch (e) {
                // API not available
            }
        });
        
        if (detectedAPIs.length > 0) {
            console.log(`❌ Suspicious APIs detected: ${detectedAPIs.join(', ')}`);
        } else {
            console.log('✅ No suspicious APIs detected');
        }
        
        console.log('');
    };
    
    // Test 4: Encryption Pattern Detection
    const testEncryptionPatterns = () => {
        console.log('🔐 Test 4: Encryption Pattern Detection');
        
        const encryptionPatterns = [
            /\^/g,
            /XOR/g,
            /encrypt|decrypt/g,
            /TextEncoder|TextDecoder/g,
            /Uint8Array/g
        ];
        
        const code = document.querySelector('script[src*="invisible.js"]')?.textContent || '';
        
        encryptionPatterns.forEach((pattern, index) => {
            const matches = code.match(pattern);
            if (matches) {
                console.log(`❌ Encryption pattern ${index + 1} detected: ${matches.length} matches`);
            } else {
                console.log(`✅ Encryption pattern ${index + 1} not detected`);
            }
        });
        
        console.log('');
    };
    
    // Test 5: Anti-Debugging Detection
    const testAntiDebugging = () => {
        console.log('🐛 Test 5: Anti-Debugging Detection');
        
        const antiDebugPatterns = [
            /debugger/g,
            /inspector/g,
            /devtools/g,
            /Error\(\)/g,
            /\.stack/g
        ];
        
        const code = document.querySelector('script[src*="invisible.js"]')?.textContent || '';
        
        antiDebugPatterns.forEach((pattern, index) => {
            const matches = code.match(pattern);
            if (matches) {
                console.log(`❌ Anti-debugging pattern ${index + 1} detected: ${matches.length} matches`);
            } else {
                console.log(`✅ Anti-debugging pattern ${index + 1} not detected`);
            }
        });
        
        console.log('');
    };
    
    // Test 6: Sandbox Detection
    const testSandboxDetection = () => {
        console.log('📦 Test 6: Sandbox Detection');
        
        const sandboxPatterns = [
            /phantom/g,
            /headless/g,
            /selenium/g,
            /webdriver/g,
            /chrome-lighthouse/g
        ];
        
        const code = document.querySelector('script[src*="invisible.js"]')?.textContent || '';
        
        sandboxPatterns.forEach((pattern, index) => {
            const matches = code.match(pattern);
            if (matches) {
                console.log(`❌ Sandbox detection pattern ${index + 1} detected: ${matches.length} matches`);
            } else {
                console.log(`✅ Sandbox detection pattern ${index + 1} not detected`);
            }
        });
        
        console.log('');
    };
    
    // Test 7: Timing Analysis
    const testTimingAnalysis = () => {
        console.log('⏱️ Test 7: Timing Analysis');
        
        const timingPatterns = [
            /setTimeout/g,
            /performance\.now/g,
            /Date\.now/g
        ];
        
        const code = document.querySelector('script[src*="invisible.js"]')?.textContent || '';
        
        timingPatterns.forEach((pattern, index) => {
            const matches = code.match(pattern);
            if (matches) {
                console.log(`❌ Timing pattern ${index + 1} detected: ${matches.length} matches`);
            } else {
                console.log(`✅ Timing pattern ${index + 1} not detected`);
            }
        });
        
        console.log('');
    };
    
    // Test 8: Memory Analysis
    const testMemoryAnalysis = () => {
        console.log('💾 Test 8: Memory Analysis');
        
        const memoryPatterns = [
            /WeakMap/g,
            /Map/g,
            /Set/g,
            /new Map/g,
            /new Set/g
        ];
        
        const code = document.querySelector('script[src*="invisible.js"]')?.textContent || '';
        
        memoryPatterns.forEach((pattern, index) => {
            const matches = code.match(pattern);
            if (matches) {
                console.log(`❌ Memory pattern ${index + 1} detected: ${matches.length} matches`);
            } else {
                console.log(`✅ Memory pattern ${index + 1} not detected`);
            }
        });
        
        console.log('');
    };
    
    // Test 9: Dynamic Code Generation
    const testDynamicCode = () => {
        console.log('⚡ Test 9: Dynamic Code Generation');
        
        const dynamicPatterns = [
            /new Function/g,
            /eval/g,
            /setTimeout/g,
            /WebAssembly\.instantiate/g
        ];
        
        const code = document.querySelector('script[src*="invisible.js"]')?.textContent || '';
        
        dynamicPatterns.forEach((pattern, index) => {
            const matches = code.match(pattern);
            if (matches) {
                console.log(`❌ Dynamic code pattern ${index + 1} detected: ${matches.length} matches`);
            } else {
                console.log(`✅ Dynamic code pattern ${index + 1} not detected`);
            }
        });
        
        console.log('');
    };
    
    // Test 10: Overall Assessment
    const testOverallAssessment = () => {
        console.log('📈 Test 10: Overall Assessment');
        
        let score = 100;
        const issues = [];
        
        // Check for common detection patterns
        const code = document.querySelector('script[src*="invisible.js"]')?.textContent || '';
        
        if (code.match(/_0x[a-f0-9]{4}/g)) {
            score -= 20;
            issues.push('Pattern naming detected');
        }
        
        if (code.match(/new Uint8Array/g)) {
            score -= 15;
            issues.push('Uint8Array usage detected');
        }
        
        if (code.match(/WebAssembly/g)) {
            score -= 10;
            issues.push('WebAssembly usage detected');
        }
        
        if (code.match(/WeakMap/g)) {
            score -= 10;
            issues.push('WeakMap usage detected');
        }
        
        if (code.match(/performance\.now/g)) {
            score -= 10;
            issues.push('Performance timing detected');
        }
        
        if (code.match(/navigator\.userAgent/g)) {
            score -= 10;
            issues.push('User agent detection detected');
        }
        
        if (code.match(/debugger|inspector|devtools/g)) {
            score -= 15;
            issues.push('Anti-debugging patterns detected');
        }
        
        if (code.match(/phantom|headless|selenium|webdriver/g)) {
            score -= 10;
            issues.push('Sandbox detection patterns detected');
        }
        
        console.log(`📊 Detection Score: ${score}/100`);
        
        if (score >= 80) {
            console.log('✅ EXCELLENT: Very difficult to detect');
        } else if (score >= 60) {
            console.log('⚠️ GOOD: Moderately difficult to detect');
        } else if (score >= 40) {
            console.log('❌ FAIR: Somewhat detectable');
        } else {
            console.log('🚨 POOR: Easily detectable');
        }
        
        if (issues.length > 0) {
            console.log('\n🔍 Detected Issues:');
            issues.forEach(issue => console.log(`  - ${issue}`));
        }
        
        console.log('');
    };
    
    // Run all tests
    const runAllTests = () => {
        testPatternAnalysis();
        testFunctionNames();
        testAPIUsage();
        testEncryptionPatterns();
        testAntiDebugging();
        testSandboxDetection();
        testTimingAnalysis();
        testMemoryAnalysis();
        testDynamicCode();
        testOverallAssessment();
        
        console.log('🎯 Detection Test Complete!');
    };
    
    // Run tests after a short delay
    setTimeout(runAllTests, 1000);
    
})();