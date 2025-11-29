import katex from 'katex';

/**
 * Renders LaTeX formula to HTML using KaTeX
 * @param latex - LaTeX string to render
 * @param displayMode - If true, renders in display mode (block), otherwise inline
 * @returns HTML string with rendered formula
 */
export function renderLatex(latex: string, displayMode: boolean = false): string {
    try {
        return katex.renderToString(latex, {
            displayMode,
            throwOnError: false,
            strict: false,
        });
    } catch (error) {
        console.error('Error rendering LaTeX:', error);
        return `<span class="text-red-500">Error: ${latex}</span>`;
    }
}

/**
 * Replaces {{formula:id}} placeholders with rendered inline LaTeX formulas
 * @param content - HTML content with formula placeholders
 * @param formulas - Array of formula objects with id and latex
 * @param symbols - Optional array of symbol objects for replacing symbols in formulas
 * @returns HTML content with rendered formulas
 */
export function replaceFormulaPlaceholders(
    content: string,
    formulas: Array<{
        id: string;
        latex: string;
        is_symbol?: boolean;
        symbol_parse_confidence?: string;
        symbol_definition?: string;
        type?: string;
        metadata?: {
            equation_number?: string;
            [key: string]: any;
        };
    }>,
    symbols?: Array<{
        id: string;
        latex: string;
        description?: string;
        units?: string;
    }>,
): string {
    // Create a map for fast lookup
    const formulaMap = new Map(formulas.map((f) => [f.id, f]));

    // Replace all {{formula:id}} or {{formula:id:(number)}} with rendered KaTeX HTML
    // Regex matches: {{formula:hexid}} or {{formula:hexid:(12.11)}}
    return content.replace(/\{\{formula:([a-f0-9]+)(?::\([^)]+\))?\}\}/g, (match, formulaId) => {
        const formula = formulaMap.get(formulaId);
        if (formula) {
            // Replace symbols in formula latex if symbols array is provided
            let formulaLatex = formula.latex;
            if (symbols && symbols.length > 0) {
                formulaLatex = replaceSymbolsInLatex(formulaLatex, symbols);
            }

            const isDisplayMode = formula.type === 'display';
            const renderedLatex = renderLatex(formulaLatex, isDisplayMode);

            // Check if it's a display formula with equation number
            if (isDisplayMode && formula.metadata?.equation_number) {
                // Display formula with equation number
                return `<div class="display-formula-container regular-formula" data-formula-id="${formula.id}" style="display: flex; align-items: center; justify-content: center; gap: 1rem; margin: 1rem 0; cursor: pointer;"><div class="formula-content" style="flex: 1; text-align: center;">${renderedLatex}</div><span class="equation-number" style="color: #6b7280; font-size: 0.875rem; white-space: nowrap; pointer-events: none;">${escapeHtml(formula.metadata.equation_number)}</span></div>`;
            }

            // Display formula without equation number
            if (isDisplayMode) {
                return `<div class="display-formula-container regular-formula" data-formula-id="${formula.id}" style="text-align: center; margin: 1rem 0; cursor: pointer;">${renderedLatex}</div>`;
            }

            // Check if it's a high-confidence symbol
            const isHighConfidenceSymbol =
                formula.is_symbol === true && formula.symbol_parse_confidence === 'high';

            if (isHighConfidenceSymbol && formula.symbol_definition) {
                // Wrap in a span with green border and tooltip for high-confidence symbols
                return `<span class="symbol-formula" data-formula-id="${formula.id}" data-tooltip="${escapeHtml(formula.symbol_definition)}">${renderedLatex}</span>`;
            } else {
                // Wrap in a span with gray border for regular formulas
                return `<span class="regular-formula" data-formula-id="${formula.id}">${renderedLatex}</span>`;
            }
        }
        // If formula not found, leave as is or show warning
        return `<span class="text-orange-500" title="Formula not found">${match}</span>`;
    });
}

/**
 * Helper function to replace symbol placeholders in LaTeX strings
 * @param latex - LaTeX string with symbol placeholders
 * @param symbols - Array of symbol objects
 * @returns LaTeX string with replaced symbols
 */
export function replaceSymbolsInLatex(
    latex: string,
    symbols: Array<{
        id: string;
        latex: string;
    }>,
): string {
    const symbolMap = new Map(symbols.map((s) => [s.id, s]));

    return latex.replace(/\{\{symbol:([0-9]+)\}\}/g, (match, symbolId) => {
        const symbol = symbolMap.get(symbolId);
        return symbol ? symbol.latex : match;
    });
}

/**
 * Escapes HTML special characters
 */
function escapeHtml(text: string): string {
    const map: Record<string, string> = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
}

/**
 * Replaces {{symbol:id}} placeholders with rendered inline LaTeX symbols
 * @param content - HTML content with symbol placeholders
 * @param symbols - Array of symbol objects with id and latex
 * @returns HTML content with rendered symbols
 */
export function replaceSymbolPlaceholders(
    content: string,
    symbols: Array<{
        id: string;
        latex: string;
        description?: string;
        units?: string;
    }>,
): string {
    // Create a map for fast lookup
    const symbolMap = new Map(symbols.map((s) => [s.id, s]));

    // Replace all {{symbol:id}} with rendered KaTeX HTML
    return content.replace(/\{\{symbol:([0-9]+)\}\}/g, (match, symbolId) => {
        const symbol = symbolMap.get(symbolId);
        if (symbol) {
            const renderedLatex = renderLatex(symbol.latex, false); // inline mode

            // Build tooltip with all fields except latex
            const tooltipParts: string[] = [];
            if (symbol.description) {
                tooltipParts.push(symbol.description);
            }
            if (symbol.units) {
                tooltipParts.push(symbol.units);
            }
            const tooltip = tooltipParts.join(', ');

            // Use symbol-formula class for pink border (same as high-confidence symbol formulas)
            if (tooltip) {
                return `<span class="symbol-formula pink" data-symbol-id="${symbol.id}" data-tooltip="${escapeHtml(tooltip)}">${renderedLatex}</span>`;
            } else {
                return `<span class="symbol-formula pink" data-symbol-id="${symbol.id}">${renderedLatex}</span>`;
            }
        }
        // If symbol not found, leave as is or show warning
        return `<span class="text-orange-500" title="Symbol not found">${match}</span>`;
    });
}

/**
 * Replaces {{literature:id}} placeholders with links to literature pages
 * @param content - HTML content with literature placeholders
 * @param literature - Array of literature objects with id and number
 * @returns HTML content with literature links
 */
export function replaceLiteraturePlaceholders(
    content: string,
    literature: Array<{
        id: string;
        number?: number;
        text?: string;
    }>,
): string {
    // Create a map for fast lookup
    const literatureMap = new Map(literature.map((lit) => [lit.id, lit]));

    // Replace all {{literature:id}} with links
    return content.replace(/\{\{literature:([a-f0-9]+)\}\}/g, (match, literatureId) => {
        const lit = literatureMap.get(literatureId);

        if (lit) {
            const displayText = lit.number !== undefined ? `[${lit.number}]` : `[?]`;
            const tooltip = lit.text || 'Литература';

            return `<a href="/literature/${lit.id}" target="_blank" rel="noopener noreferrer" class="literature-link" title="${escapeHtml(tooltip)}">${displayText}</a>`;
        }

        // If literature not found, leave as is or show warning
        return `<span class="text-orange-500" title="Literature not found">${match}</span>`;
    });
}

/**
 * Replaces Markdown-style links with HTML links
 * Supports [text](url){:target="_blank"} syntax
 * @param content - Content with Markdown links
 * @returns Content with HTML links
 */
export function replaceMarkdownLinks(content: string): string {
    // Replace [text](url){:target="_blank"} with <a href="url" target="_blank">text</a>
    content = content.replace(
        /\[([^\]]+)\]\(([^)]+)\)\{:target="_blank"\}/g,
        (match, text, url) => {
            return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="markdown-link">${text}</a>`;
        },
    );

    // Replace regular [text](url) with <a href="url">text</a>
    content = content.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
        return `<a href="${escapeHtml(url)}" class="markdown-link">${text}</a>`;
    });

    return content;
}
