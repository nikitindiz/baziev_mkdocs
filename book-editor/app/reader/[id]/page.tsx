'use client';

import { useParagraph } from '@/hooks/useParagraphs';
import { ParagraphCard } from '@/components/ParagraphCard';
import Link from 'next/link';
import { use } from 'react';

export default function ParagraphPage({ 
  params 
}: { 
  params: Promise<{ id: string }> 
}) {
  const { id } = use(params);
  const { data: paragraph, isLoading, isError, error } = useParagraph(id);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Шапка */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link 
              href="/reader" 
              className="text-2xl font-bold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            >
              📖 Физика Базиева
            </Link>

            <div className="flex gap-3">
              <Link
                href="/reader"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                ← Все параграфы
              </Link>
              <Link
                href="/"
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                На главную
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Контент */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Загрузка параграфа...</p>
            </div>
          </div>
        )}

        {isError && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
            <p className="text-red-800 dark:text-red-200 font-semibold mb-2">
              Ошибка загрузки
            </p>
            <p className="text-red-600 dark:text-red-300 text-sm mb-4">
              {error?.message || 'Не удалось загрузить параграф'}
            </p>
            <Link
              href="/reader"
              className="inline-block px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              Вернуться к списку
            </Link>
          </div>
        )}

        {paragraph && (
          <>
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Параграф
              </h1>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                ID: {paragraph.id}
              </p>
            </div>

            <ParagraphCard paragraph={paragraph} showNavigation={true} />

            {/* Быстрая навигация */}
            <div className="mt-8 flex justify-between items-center">
              {paragraph.previous ? (
                <Link
                  href={`/reader/${paragraph.previous.id}`}
                  className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <span>←</span> Предыдущий
                </Link>
              ) : (
                <div className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 rounded-lg cursor-not-allowed">
                  ← Предыдущий
                </div>
              )}

              {paragraph.next ? (
                <Link
                  href={`/reader/${paragraph.next.id}`}
                  className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                >
                  Следующий <span>→</span>
                </Link>
              ) : (
                <div className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 rounded-lg cursor-not-allowed">
                  Следующий →
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
