export interface FormulaMetadata {
    db_key?: string;
    src?: string;
    equation_number?: string | null;
}

export interface Formula {
    id: string;
    latex: string;
    type: 'inline' | 'display';
    wrapper_html?: string;
    source?: string;
    metadata?: string | FormulaMetadata;

    // Symbol properties
    is_symbol?: boolean;
    symbol_type?: string;
    symbol_value?: string;
    symbol_definition?: string;
    symbol_units?: string;
    symbol_parsed?: boolean;
    symbol_parse_confidence?: 'high' | 'medium' | 'low';
    not_sure_if_this_is_symbol?: boolean;
}

export interface FormulaUpdateRequest {
    latex?: string;
    type?: 'inline' | 'display';
    is_symbol?: boolean;
    symbol_definition?: string;
    symbol_value?: string;
    symbol_units?: string;
    symbol_type?: string;
    symbol_parse_confidence?: 'high' | 'medium' | 'low';
    not_sure_if_this_is_symbol?: boolean;
}
