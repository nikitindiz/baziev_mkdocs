'use client';

import Link from 'next/link';
import { SectionMetadata } from '@/types/paragraph-context';

interface NavigationProps {
  previousSection: SectionMetadata | null;
  nextSection: SectionMetadata | null;
}

export function Navigation({ previousSection, nextSection }: NavigationProps) {
  return (
    <nav className="flex items-center justify-between gap-4 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
      <div className="flex-1">
        {previousSection ? (
          <Link
            href={`/read-in-context/${previousSection.firstParagraphId}`}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors group"
          >
            <span className="text-xl group-hover:-translate-x-1 transition-transform inline-block">←</span>
            <div className="text-left">
              <div className="text-xs opacity-80">Предыдущая секция</div>
              <div className="font-medium text-sm">
                {previousSection.number && `§${previousSection.number} `}
                {previousSection.title}
              </div>
            </div>
          </Link>
        ) : (
          <div className="text-gray-400 dark:text-gray-600 text-sm px-4 py-2">
            Начало книги
          </div>
        )}
      </div>

      <div className="flex-1 flex justify-end">
        {nextSection ? (
          <Link
            href={`/read-in-context/${nextSection.firstParagraphId}`}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors group"
          >
            <div className="text-right">
              <div className="text-xs opacity-80">Следующая секция</div>
              <div className="font-medium text-sm">
                {nextSection.number && `${nextSection.number} `}
                {nextSection.title}
              </div>
            </div>
            <span className="text-xl group-hover:translate-x-1 transition-transform inline-block">→</span>
          </Link>
        ) : (
          <div className="text-gray-400 dark:text-gray-600 text-sm px-4 py-2">
            Конец книги
          </div>
        )}
      </div>
    </nav>
  );
}
