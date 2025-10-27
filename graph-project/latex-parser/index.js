#!/usr/bin/env node
/**
 * LaTeX Symbol Parser using KaTeX
 * 
 * Парсит LaTeX формулы и извлекает символы (переменные).
 * Использует: node index.js "latex_formula"
 * Или читает из stdin: echo "a + b" | node index.js
 */

const katex = require('katex');

/**
 * Извлекает текст из узла AST
 */
function extractText(node) {
    if (!node) return '';
    
    if (node.text) return node.text;
    
    if (Array.isArray(node)) {
        return node.map(extractText).join('');
    }
    
    if (node.body) {
        if (Array.isArray(node.body)) {
            return node.body.map(extractText).join('');
        }
        return extractText(node.body);
    }
    
    return '';
}

/**
 * Проверяет, является ли узел LaTeX командой
 */
function isLatexCommand(text) {
    return text && text.startsWith('\\');
}

/**
 * Проверяет, является ли символ оператором или знаком пунктуации
 */
function isOperatorOrPunctuation(text) {
    const operators = [
        '+', '-', '=', '<', '>', '≤', '≥', '≠', '≈', '∼',
        '×', '÷', '±', '∓', '∗', '·', '∘', '•',
        '(', ')', '[', ']', '{', '}', '|',
        ',', ';', ':', '!', '?',
        '\\cdot', '\\times', '\\div', '\\pm', '\\mp',
        '\\leq', '\\geq', '\\neq', '\\approx', '\\sim',
        '\\infty', '\\partial', '\\nabla'
    ];
    return operators.includes(text);
}

/**
 * Список греческих букв LaTeX
 */
const greekLetters = [
    '\\alpha', '\\beta', '\\gamma', '\\delta', '\\epsilon', '\\varepsilon',
    '\\zeta', '\\eta', '\\theta', '\\vartheta', '\\iota', '\\kappa',
    '\\lambda', '\\mu', '\\nu', '\\xi', '\\pi', '\\varpi', '\\rho',
    '\\varrho', '\\sigma', '\\varsigma', '\\tau', '\\upsilon', '\\phi',
    '\\varphi', '\\chi', '\\psi', '\\omega',
    '\\Gamma', '\\Delta', '\\Theta', '\\Lambda', '\\Xi', '\\Pi',
    '\\Sigma', '\\Upsilon', '\\Phi', '\\Psi', '\\Omega'
];

/**
 * Извлекает символы из LaTeX формулы
 */
function extractSymbols(latex) {
    const symbols = new Set();
    
    try {
        // Парсим через KaTeX
        const parsed = katex.__parse(latex, {
            throwOnError: false,
            strict: false
        });
        
        /**
         * Обходит AST дерево и извлекает символы
         */
        function traverse(node, context = {}) {
            if (!node) return;
            
            switch (node.type) {
                case 'textord':
                case 'mathord':
                    // Обычные символы (переменные a, b, x, y, etc.)
                    if (node.text) {
                        // Латинские буквы - это переменные
                        if (/^[a-zA-Z]$/.test(node.text)) {
                            if (!context.inOperator) {
                                symbols.add(node.text);
                            }
                        }
                        // Греческие буквы как команды
                        else if (greekLetters.includes(node.text)) {
                            if (!context.inOperator) {
                                symbols.add(node.text);
                            }
                        }
                    }
                    break;
                
                case 'atom':
                    // Специальные символы - НЕ добавляем операторы
                    if (node.text && !isOperatorOrPunctuation(node.text)) {
                        symbols.add(node.text);
                    }
                    break;
                
                case 'op':
                    // Операторы (sin, cos, log, lim, etc.) - НЕ символы
                    if (node.body) {
                        traverse(node.body, { ...context, inOperator: true });
                    }
                    break;
                
                case 'ordgroup':
                case 'styling':
                    // Группы - обрабатываем содержимое
                    if (node.body) {
                        if (Array.isArray(node.body)) {
                            node.body.forEach(n => traverse(n, context));
                        } else {
                            traverse(node.body, context);
                        }
                    }
                    break;
                
                case 'supsub':
                    // Индексы и степени: a_i, x^2, y_0
                    const baseText = node.base ? extractText(node.base) : '';
                    
                    // Обрабатываем базу
                    if (node.base) {
                        traverse(node.base, context);
                    }
                    
                    // Добавляем составные символы с индексами
                    if (baseText && /^[a-zA-Z]$/.test(baseText)) {
                        if (node.sub) {
                            const subText = extractText(node.sub);
                            if (subText) {
                                // Проверяем, это LaTeX команда или обычный текст
                                if (isLatexCommand(subText)) {
                                    symbols.add(baseText + '_' + subText);
                                } else {
                                    symbols.add(baseText + '_{' + subText + '}');
                                }
                            }
                            // Обрабатываем элементы индекса
                            traverse(node.sub, context);
                        }
                        if (node.sup) {
                            const supText = extractText(node.sup);
                            if (supText) {
                                if (isLatexCommand(supText)) {
                                    symbols.add(baseText + '^' + supText);
                                } else {
                                    symbols.add(baseText + '^{' + supText + '}');
                                }
                            }
                            // Обрабатываем элементы степени
                            traverse(node.sup, context);
                        }
                    }
                    break;
                
                case 'accent':
                    // Акценты: штрихи ('), тильды (~), шляпки (^), etc.
                    if (node.base) {
                        const baseText = extractText(node.base);
                        if (baseText && /^[a-zA-Z]$/.test(baseText)) {
                            // Определяем тип акцента
                            if (node.label === 'vec') {
                                symbols.add('\\vec{' + baseText + '}');
                            } else if (node.label === 'bar') {
                                symbols.add('\\bar{' + baseText + '}');
                            } else if (node.label === 'hat') {
                                symbols.add('\\hat{' + baseText + '}');
                            } else if (node.label === 'tilde') {
                                symbols.add('\\tilde{' + baseText + '}');
                            } else {
                                // Для прочих акцентов просто добавляем штрих
                                symbols.add(baseText + "'");
                            }
                        }
                        traverse(node.base, context);
                    }
                    break;
                
                case 'sqrt':
                    // Корни - обрабатываем содержимое
                    if (node.body) {
                        if (Array.isArray(node.body)) {
                            node.body.forEach(n => traverse(n, context));
                        } else {
                            traverse(node.body, context);
                        }
                    }
                    break;
                
                case 'genfrac':
                    // Дроби - обрабатываем числитель и знаменатель
                    if (node.numer) traverse(node.numer, context);
                    if (node.denom) traverse(node.denom, context);
                    break;
                
                case 'leftright':
                case 'middle':
                    // Скобки - обрабатываем содержимое
                    if (node.body) {
                        if (Array.isArray(node.body)) {
                            node.body.forEach(n => traverse(n, context));
                        } else {
                            traverse(node.body, context);
                        }
                    }
                    break;
                
                case 'color':
                case 'sizing':
                case 'font':
                    // Стилистика - обрабатываем содержимое
                    if (node.body) {
                        if (Array.isArray(node.body)) {
                            node.body.forEach(n => traverse(n, context));
                        } else {
                            traverse(node.body, context);
                        }
                    }
                    break;
                
                case 'text':
                    // Текстовые блоки - ПРОПУСКАЕМ
                    break;
                
                default:
                    // Для неизвестных типов пытаемся обработать body
                    if (node.body) {
                        if (Array.isArray(node.body)) {
                            node.body.forEach(n => traverse(n, context));
                        } else {
                            traverse(node.body, context);
                        }
                    }
            }
        }
        
        // Обрабатываем дерево
        if (Array.isArray(parsed)) {
            parsed.forEach(node => traverse(node));
        } else {
            traverse(parsed);
        }
        
        return Array.from(symbols).sort();
        
    } catch (error) {
        console.error(JSON.stringify({
            success: false,
            error: error.message,
            latex: latex
        }));
        return [];
    }
}

// Main
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.length > 0) {
        // Формула передана как аргумент
        const latex = args[0];
        const symbols = extractSymbols(latex);
        console.log(JSON.stringify({
            success: true,
            latex: latex,
            symbols: symbols
        }));
    } else {
        // Читаем из stdin
        let latex = '';
        process.stdin.on('data', chunk => latex += chunk);
        process.stdin.on('end', () => {
            latex = latex.trim();
            if (latex) {
                const symbols = extractSymbols(latex);
                console.log(JSON.stringify({
                    success: true,
                    latex: latex,
                    symbols: symbols
                }));
            }
        });
    }
}

module.exports = { extractSymbols };
