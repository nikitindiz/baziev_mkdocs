export interface SymbolListItem {
    id: string;
    latex: string;
    description?: string;
    units?: string;
    value?: string;
    chapterId?: string;
    chapterTitle?: string;
    sectionId?: string;
    sectionTitle?: string;
    usageCount?: number;
}

export interface SymbolsListResponse {
    symbols: SymbolListItem[];
}

export interface SymbolsListFilters {
    search?: string;
    chapterId?: string;
    sectionId?: string;
    sortBy?: 'latex' | 'created';
}
