'use client';

import { ParagraphsList } from '@/components/ParagraphsList';
import Link from 'next/link';
import { useState } from 'react';

export default function ReaderPage() {
  const [limit, setLimit] = useState(20);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Шапка */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <Link href="/" className="text-2xl font-bold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                📖 Физика Базиева
              </Link>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Интерактивное чтение книги
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div>
                <label htmlFor="limit" className="text-sm text-gray-600 dark:text-gray-400 mr-2">
                  Параграфов на страницу:
                </label>
                <select
                  id="limit"
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={30}>30</option>
                  <option value={50}>50</option>
                </select>
              </div>

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
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Все параграфы книги
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Прокручивайте страницу вниз для автоматической загрузки следующих параграфов
          </p>
        </div>

        <ParagraphsList limit={limit} />
      </main>

      {/* Футер */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-20">
        <div className="max-w-6xl mx-auto px-4 py-6 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>Powered by Neo4j • TanStack Query • Next.js 16</p>
        </div>
      </footer>
    </div>
  );
}
