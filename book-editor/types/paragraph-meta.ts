export interface ParagraphMeta {
  id: string;
  order?: number;
  section_id?: string;
  chapter_id?: string;
}

export interface ParagraphsMetaResponse {
  data: ParagraphMeta[];
  total: number;
}
