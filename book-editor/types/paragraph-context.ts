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
}

export interface ParagraphWithReferences {
  id: string;
  content: string;
  order: number;
  tables: TableReference[];
  illustrations: IllustrationReference[];
  formulas: FormulaReference[];
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
