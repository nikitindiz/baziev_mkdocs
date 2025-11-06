'use client';

import { useVirtualizer } from '@tanstack/react-virtual';
import { useParagraphsMeta, useParagraphsBatch } from '@/hooks/useParagraphsMeta';
import { ParagraphCard } from './ParagraphCard';
import { useRef, useMemo, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';

interface VirtualParagraphsListProps {
  overscan?: number;
}

export function VirtualParagraphsList({ overscan = 5 }: VirtualParagraphsListProps) {
  const searchParams = useSearchParams();
  const targetParagraphId = searchParams.get('paragraph');
  const parentRef = useRef<HTMLDivElement>(null);
  const [scrolledToTarget, setScrolledToTarget] = useState(false);

  // Получаем метаданные всех параграфов
  const { data: metaData, isLoading: isLoadingMeta, isError: isMetaError } = useParagraphsMeta();

  const allParagraphIds = useMemo(() => {
    return metaData?.data.map(p => p.id) || [];
  }, [metaData]);

  // Виртуализатор
  const virtualizer = useVirtualizer({
    count: allParagraphIds.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 200, // примерная высота параграфа
    overscan,
  });

  const virtualItems = virtualizer.getVirtualItems();

  // Получаем ID видимых элементов
  const visibleIds = useMemo(() => {
    return virtualItems.map(item => allParagraphIds[item.index]);
  }, [virtualItems, allParagraphIds]);

  // Загружаем контент только видимых параграфов
  const { data: paragraphsData, isLoading: isLoadingContent } = useParagraphsBatch(
    visibleIds,
    visibleIds.length > 0
  );

  // Создаем map для быстрого доступа к контенту
  const paragraphsMap = useMemo(() => {
    const map = new Map();
    paragraphsData?.forEach(p => map.set(p.id, p));
    return map;
  }, [paragraphsData]);

  // Прокрутка к целевому параграфу
  useEffect(() => {
    if (targetParagraphId && allParagraphIds.length > 0 && !scrolledToTarget) {
      const targetIndex = allParagraphIds.indexOf(targetParagraphId);
      if (targetIndex !== -1) {
        // Небольшая задержка для инициализации виртуализатора
        setTimeout(() => {
          virtualizer.scrollToIndex(targetIndex, {
            align: 'center',
            behavior: 'smooth',
          });
          setScrolledToTarget(true);

          // Подсветка целевого элемента
          setTimeout(() => {
            const element = document.getElementById(targetParagraphId);
            if (element) {
              element.classList.add('highlight-paragraph');
              setTimeout(() => {
                element.classList.remove('highlight-paragraph');
              }, 3000);
            }
          }, 500);
        }, 100);
      }
    }
  }, [targetParagraphId, allParagraphIds, virtualizer, scrolledToTarget]);

  if (isLoadingMeta) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Загрузка структуры книги...
          </p>
        </div>
      </div>
    );
  }

  if (isMetaError) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
        <p className="text-red-800 dark:text-red-200 font-semibold mb-2">
          Ошибка загрузки
        </p>
        <p className="text-red-600 dark:text-red-300 text-sm">
          Не удалось загрузить структуру книги
        </p>
      </div>
    );
  }

  const total = metaData?.total || 0;

  return (
    <div className="space-y-6">
      {/* Статистика */}
      <div className="bg-linear-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <span className="text-sm text-gray-600 dark:text-gray-400">Всего параграфов:</span>
              <span className="ml-2 text-lg font-bold text-blue-600 dark:text-blue-400">
                {total}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-600 dark:text-gray-400">В памяти:</span>
              <span className="ml-2 text-lg font-bold text-green-600 dark:text-green-400">
                {paragraphsMap.size}
              </span>
            </div>
            <div>
              <span className="text-sm text-gray-600 dark:text-gray-400">Видимых:</span>
              <span className="ml-2 text-lg font-bold text-indigo-600 dark:text-indigo-400">
                {virtualItems.length}
              </span>
            </div>
          </div>
          <div className="text-xs bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-3 py-1 rounded-full">
            ⚡ Виртуализация
          </div>
        </div>
      </div>

      {/* Виртуальный список */}
      <div
        ref={parentRef}
        className="h-[calc(100vh-300px)] overflow-auto border border-gray-200 dark:border-gray-700 rounded-lg"
      >
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {virtualItems.map((virtualItem) => {
            const paragraphId = allParagraphIds[virtualItem.index];
            const paragraph = paragraphsMap.get(paragraphId);
            const meta = metaData?.data[virtualItem.index];

            return (
              <div
                key={virtualItem.key}
                data-index={virtualItem.index}
                ref={virtualizer.measureElement}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualItem.start}px)`,
                }}
                className="px-4 py-2"
              >
                {paragraph ? (
                  <ParagraphCard
                    paragraph={paragraph}
                    index={virtualItem.index}
                    showNavigation={false}
                  />
                ) : (
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                        #{virtualItem.index + 1}
                      </span>
                      <code className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-gray-600 dark:text-gray-300">
                        {paragraphId}
                      </code>
                    </div>
                    {isLoadingContent ? (
                      <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-solid border-gray-400 border-r-transparent"></div>
                        <span className="text-sm">Загрузка...</span>
                      </div>
                    ) : (
                      <div className="text-gray-400 dark:text-gray-500 text-sm">
                        Параграф не загружен
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Информация */}
      <div className="text-center text-sm text-gray-500 dark:text-gray-400">
        <p>
          Используется виртуализация для оптимальной производительности.
          Загружается только контент видимых параграфов.
        </p>
      </div>
    </div>
  );
}
