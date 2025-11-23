export interface Literature {
    id: string;
    text: string;
    author?: string;
    title?: string;
    publication?: string;
    source?: string;
    number?: number;
}

export interface LiteratureResponse {
    data: Literature;
}
