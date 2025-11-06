import { useQuery } from '@tanstack/react-query';
import { ParagraphsMetaResponse, ParagraphMeta } from '@/types/paragraph-meta';
import { Paragraph } from '@/types/paragraph';

// Получить метаданные всех параграфов (только ID и базовая информация)
async function fetchParagraphsMeta(): Promise<ParagraphsMetaResponse> {
  const response = await fetch('/api/paragraphs/meta');
  
  if (!response.ok) {
    throw new Error('Failed to fetch paragraphs metadata');
  }
  
  return response.json();
}

// Получить контент параграфов по списку ID
async function fetchParagraphsBatch(ids: string[]): Promise<Paragraph[]> {
  const response = await fetch('/api/paragraphs/batch', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ids }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch paragraphs batch');
  }
  
  const data = await response.json();
  return data.data;
}

// Хук для получения всех ID параграфов
export function useParagraphsMeta() {
  return useQuery({
    queryKey: ['paragraphs-meta'],
    queryFn: fetchParagraphsMeta,
    staleTime: 5 * 60 * 1000, // 5 минут (метаданные редко меняются)
  });
}

// Хук для получения контента параграфов по ID
export function useParagraphsBatch(ids: string[], enabled: boolean = true) {
  return useQuery({
    queryKey: ['paragraphs-batch', ids],
    queryFn: () => fetchParagraphsBatch(ids),
    enabled: enabled && ids.length > 0,
    staleTime: 60 * 1000, // 1 минута
  });
}

// Хелпер для разбиения большого списка ID на батчи
export function chunkArray<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}
