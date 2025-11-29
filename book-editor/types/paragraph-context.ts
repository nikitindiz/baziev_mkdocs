export interface TableReference {
    id: string;
    content: string;
    html_attributes?: string;
    type?: string;
}

export interface IllustrationReference {
    id: string;
    caption?: string;
    svg_content?: string;
    wrapper_html?: string;
    type?: string;
}

export interface FormulaReference {
    id: string;
    latex: string;
    wrapper_html?: string;
    type?: string;
    is_symbol?: boolean;
    symbol_parse_confidence?: string;
    symbol_definition?: string;
    metadata?: {
        equation_number?: string;
        [key: string]: any;
    };
}

export interface LiteratureReference {
    id: string;
    number?: number;
    text?: string;
}

export interface SymbolReference {
    id: string;
    latex: string;
    description?: string;
    units?: string;
    value?: string;
}

export interface ParagraphWithReferences {
    id: string;
    content: string;
    order: number;
    verified?: boolean;
    tables: TableReference[];
    illustrations: IllustrationReference[];
    formulas: FormulaReference[];
    literature: LiteratureReference[];
    symbols: SymbolReference[];
}

export interface ChapterMetadata {
    id: string;
    title: string;
    order: number;
}

export interface SectionMetadata {
    id: string;
    title: string;
    number?: string;
    order: number;
    firstParagraphId: string;
}

export interface ParagraphContextResponse {
    chapter: {
        id: string;
        title: string;
        order: number;
    };
    section: {
        id: string;
        title: string;
        number?: string;
        order: number;
    };
    paragraphs: ParagraphWithReferences[];
    metadata: {
        previousChapter: ChapterMetadata | null;
        nextChapter: ChapterMetadata | null;
        previousSection: SectionMetadata | null;
        nextSection: SectionMetadata | null;
    };
}
