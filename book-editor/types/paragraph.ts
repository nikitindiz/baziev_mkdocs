export interface Paragraph {
  id: string;
  text: string;
  order?: number;
  section_id?: string;
  chapter_id?: string;
  previous?: {
    id: string;
    text: string;
  } | null;
  next?: {
    id: string;
    text: string;
  } | null;
}

export interface ParagraphsResponse {
  data: Paragraph[];
  pagination: {
    cursor: string | null;
    hasMore: boolean;
    total?: number;
  };
}
