import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { Paragraph, ParagraphsResponse } from '@/types/paragraph';

const API_BASE = '/api/paragraphs';

// Функция для получения списка параграфов
async function fetchParagraphs(
  limit: number,
  cursor?: string | null,
  sectionId?: string,
  chapterId?: string
): Promise<ParagraphsResponse> {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  
  if (cursor) params.append('cursor', cursor);
  if (sectionId) params.append('section_id', sectionId);
  if (chapterId) params.append('chapter_id', chapterId);

  const response = await fetch(`${API_BASE}?${params.toString()}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch paragraphs');
  }
  
  return response.json();
}

// Функция для получения конкретного параграфа
async function fetchParagraph(id: string): Promise<Paragraph> {
  const response = await fetch(`${API_BASE}/${id}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch paragraph');
  }
  
  return response.json();
}

// Хук для бесконечной прокрутки параграфов
export function useParagraphs(
  limit: number = 20,
  sectionId?: string,
  chapterId?: string
) {
  return useInfiniteQuery({
    queryKey: ['paragraphs', limit, sectionId, chapterId],
    queryFn: ({ pageParam }) => 
      fetchParagraphs(limit, pageParam, sectionId, chapterId),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => 
      lastPage.pagination.hasMore ? lastPage.pagination.cursor : undefined,
    select: (data) => ({
      pages: data.pages,
      pageParams: data.pageParams,
      paragraphs: data.pages.flatMap(page => page.data),
      total: data.pages[0]?.pagination.total,
    }),
  });
}

// Хук для получения конкретного параграфа
export function useParagraph(id: string) {
  return useQuery({
    queryKey: ['paragraph', id],
    queryFn: () => fetchParagraph(id),
    enabled: !!id,
  });
}
