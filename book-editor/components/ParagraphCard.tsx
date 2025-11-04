'use client';

import { Paragraph } from '@/types/paragraph';
import Link from 'next/link';
import { useState } from 'react';

interface ParagraphCardProps {
  paragraph: Paragraph;
  index?: number;
  showNavigation?: boolean;
}

export function ParagraphCard({ 
  paragraph, 
  index, 
  showNavigation = true 
}: ParagraphCardProps) {
  const [copied, setCopied] = useState(false);

  const copyLink = () => {
    const url = `${window.location.origin}/reader?paragraph=${encodeURIComponent(paragraph.id)}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <article 
      id={paragraph.id}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700 transition-all hover:shadow-lg"
    >
      {/* Заголовок */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          {index !== undefined && (
            <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
              #{index + 1}
            </span>
          )}
          <code className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-gray-600 dark:text-gray-300">
            {paragraph.id}
          </code>
          <button
            onClick={copyLink}
            className="text-xs bg-blue-100 dark:bg-blue-900 hover:bg-blue-200 dark:hover:bg-blue-800 text-blue-800 dark:text-blue-200 px-2 py-1 rounded transition-colors"
            title="Копировать ссылку на параграф"
          >
            {copied ? '✓ Скопировано' : '🔗 Ссылка'}
          </button>
        </div>
        {paragraph.order !== undefined && (
          <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
            Order: {paragraph.order}
          </span>
        )}
      </div>

      {/* Текст параграфа */}
      <p className="text-gray-800 dark:text-gray-200 leading-relaxed mb-4 text-base">
        {paragraph.text}
      </p>

      {/* Навигация Previous/Next */}
      {showNavigation && (paragraph.previous || paragraph.next) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          {paragraph.previous && (
            <Link 
              href={`/reader/${paragraph.previous.id}`}
              className="group p-3 border-l-4 border-blue-500 bg-blue-50 dark:bg-blue-900/20 rounded hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors"
            >
              <div className="text-xs text-blue-600 dark:text-blue-400 mb-1 flex items-center gap-1">
                <span>←</span> Предыдущий параграф
              </div>
              <div className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2 group-hover:line-clamp-none">
                {paragraph.previous.text}
              </div>
            </Link>
          )}

          {paragraph.next && (
            <Link 
              href={`/reader/${paragraph.next.id}`}
              className="group p-3 border-l-4 border-green-500 bg-green-50 dark:bg-green-900/20 rounded hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors"
            >
              <div className="text-xs text-green-600 dark:text-green-400 mb-1 flex items-center gap-1">
                Следующий параграф <span>→</span>
              </div>
              <div className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2 group-hover:line-clamp-none">
                {paragraph.next.text}
              </div>
            </Link>
          )}
        </div>
      )}

      {/* Метаданные */}
      {(paragraph.section_id || paragraph.chapter_id) && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 flex flex-wrap gap-2 text-xs">
          {paragraph.chapter_id && (
            <span className="bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-3 py-1 rounded-full">
              Глава: {paragraph.chapter_id}
            </span>
          )}
          {paragraph.section_id && (
            <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 px-3 py-1 rounded-full">
              Секция: {paragraph.section_id}
            </span>
          )}
        </div>
      )}
    </article>
  );
}
