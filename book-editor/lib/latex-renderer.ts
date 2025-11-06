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
  }>
): string {
  // Create a map for fast lookup
  const formulaMap = new Map(formulas.map((f) => [f.id, f]));

  // Replace all {{formula:id}} with rendered KaTeX HTML
  return content.replace(/\{\{formula:([a-f0-9]+)\}\}/g, (match, formulaId) => {
    const formula = formulaMap.get(formulaId);
    if (formula) {
      const renderedLatex = renderLatex(formula.latex, false); // inline mode
      
      // Check if it's a high-confidence symbol
      const isHighConfidenceSymbol = formula.is_symbol === true && 
                                      formula.symbol_parse_confidence === 'high';
      
      if (isHighConfidenceSymbol && formula.symbol_definition) {
        // Wrap in a span with green border and tooltip
        return `<span class="symbol-formula" data-tooltip="${escapeHtml(formula.symbol_definition)}">${renderedLatex}</span>`;
      }
      
      return renderedLatex;
    }
    // If formula not found, leave as is or show warning
    return `<span class="text-orange-500" title="Formula not found">${match}</span>`;
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
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}
