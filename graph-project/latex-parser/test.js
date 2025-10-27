#!/usr/bin/env node
/**
 * Тестирование парсера LaTeX формул
 */

const { extractSymbols } = require('./index.js');

const testCases = [
    {
        latex: 'a + b = c',
        expected: ['a', 'b', 'c']
    },
    {
        latex: 'x^2 + y^2 = z^2',
        expected: ['x', 'x^{2}', 'y', 'y^{2}', 'z', 'z^{2}']
    },
    {
        latex: 'a_i + b_j',
        expected: ['a', 'a_{i}', 'b', 'b_{j}', 'i', 'j']
    },
    {
        latex: 'n_\\hbar',
        expected: ['n', 'n_\\hbar']
    },
    {
        latex: "z_O'' = [(z_O - n(O) \\cdot \\Delta z)] = 0",
        expected: ['O', '\\Delta', 'n', 'z', 'z^\\prime\\prime', 'z_{O}']
    },
    {
        latex: '\\sin(x) + \\cos(y)',
        expected: ['x', 'y']
    },
    {
        latex: '\\alpha + \\beta',
        expected: ['\\alpha', '\\beta']
    },
    {
        latex: 'E = mc^2',
        expected: ['E', 'c', 'c^{2}', 'm']
    }
];

console.log('Тестирование парсера LaTeX формул\n');
console.log('='.repeat(80));

testCases.forEach((test, index) => {
    console.log(`\nТест ${index + 1}:`);
    console.log(`  LaTeX: ${test.latex}`);
    
    const symbols = extractSymbols(test.latex);
    console.log(`  Найдено: ${JSON.stringify(symbols)}`);
    console.log(`  Ожидалось: ${JSON.stringify(test.expected)}`);
    
    const match = JSON.stringify(symbols) === JSON.stringify(test.expected);
    console.log(`  Результат: ${match ? '✓ PASS' : '✗ FAIL'}`);
});

console.log('\n' + '='.repeat(80));
