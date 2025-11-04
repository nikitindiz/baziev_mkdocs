'use client';

import { useParagraphs } from '@/hooks/useParagraphs';
import { ParagraphCard } from './ParagraphCard';
import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';

interface ParagraphsListProps {
  limit?: number;
  sectionId?: string;
  chapterId?: string;
}

export function ParagraphsList({ 
  limit = 20, 
  sectionId, 
  chapterId 
}: ParagraphsListProps) {
  const searchParams = useSearchParams();
  const targetParagraphId = searchParams.get('paragraph');
  const [isLoadingTarget, setIsLoadingTarget] = useState(false);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    error,
  } = useParagraphs(limit, sectionId, chapterId);

  const observerTarget = useRef<HTMLDivElement>(null);
  const paragraphs = data?.paragraphs || [];

  // Автоматическая загрузка до целевого параграфа
  useEffect(() => {
    if (targetParagraphId && !isLoading && paragraphs.length > 0) {
      const targetExists = paragraphs.some(p => p.id === targetParagraphId);
      
      if (!targetExists && hasNextPage && !isFetchingNextPage && !isLoadingTarget) {
        setIsLoadingTarget(true);
        fetchNextPage().then(() => {
          setIsLoadingTarget(false);
        });
      }
    }
  }, [targetParagraphId, paragraphs, hasNextPage, isFetchingNextPage, isLoading, fetchNextPage, isLoadingTarget]);

  // Intersection Observer для автоматической подгрузки
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Загрузка параграфов...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
        <p className="text-red-800 dark:text-red-200 font-semibold mb-2">
          Ошибка загрузки
        </p>
        <p className="text-red-600 dark:text-red-300 text-sm">
          {error?.message || 'Не удалось загрузить параграфы'}
        </p>
      </div>
    );
  }

  const total = data?.total;

  return (
    <div className="space-y-6">
      {/* Индикатор загрузки до целевого параграфа */}
      {isLoadingTarget && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 text-center">
          <p className="text-blue-800 dark:text-blue-200">
            Загрузка параграфов до целевого...
          </p>
        </div>
      )}

      {/* Статистика */}
      <div className="bg-linear-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <span className="text-sm text-gray-600 dark:text-gray-400">Загружено:</span>
              <span className="ml-2 text-lg font-bold text-blue-600 dark:text-blue-400">
                {paragraphs.length}
              </span>
            </div>
            {total !== undefined && (
              <div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Всего:</span>
                <span className="ml-2 text-lg font-bold text-indigo-600 dark:text-indigo-400">
                  {total}
                </span>
              </div>
            )}
          </div>
          {hasNextPage && (
            <span className="text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-3 py-1 rounded-full">
              Есть еще
            </span>
          )}
        </div>
      </div>

      {/* Список параграфов */}
      <div className="space-y-4">
        {paragraphs.map((paragraph, index) => (
          <ParagraphCard
            key={paragraph.id}
            paragraph={paragraph}
            index={index}
            showNavigation={false}
          />
        ))}
      </div>

      {/* Индикатор загрузки следующей страницы */}
      <div ref={observerTarget} className="py-8">
        {isFetchingNextPage && (
          <div className="flex items-center justify-center">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="ml-3 text-gray-600 dark:text-gray-400">
              Загрузка следующих параграфов...
            </p>
          </div>
        )}
        
        {!hasNextPage && paragraphs.length > 0 && (
          <div className="text-center text-gray-500 dark:text-gray-400">
            <p className="text-sm">Все параграфы загружены</p>
          </div>
        )}
      </div>

      {/* Кнопка ручной загрузки (запасной вариант) */}
      {hasNextPage && !isFetchingNextPage && (
        <div className="text-center pt-4">
          <button
            onClick={() => fetchNextPage()}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors shadow-md hover:shadow-lg"
          >
            Загрузить еще
          </button>
        </div>
      )}
    </div>
  );
}
