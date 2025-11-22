'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams, useParams } from 'next/navigation';
import { ParagraphEditor } from './ParagraphEditor';

interface RightSidebarProps {
  children?: React.ReactNode;
}

const MIN_WIDTH = 300;
const MAX_WIDTH = 800;
const DEFAULT_WIDTH = 800;

export function RightSidebar({ children }: RightSidebarProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const params = useParams();
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  const paragraphId = params.id ? decodeURI(params.id as string) : null;
  const isOpen = searchParams.get('show-editor') === 'true';

  console.log('Sidebar paragraphId:', paragraphId);

  const toggleSidebar = () => {
    const params = new URLSearchParams(searchParams.toString());
    if (isOpen) {
      params.delete('show-editor');
    } else {
      params.set('show-editor', 'true');
    }
    router.push(`?${params.toString()}`, { scroll: false });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const newWidth = window.innerWidth - e.clientX;
      if (newWidth >= MIN_WIDTH && newWidth <= MAX_WIDTH) {
        setWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  return (
    <>
      {/* Toggle Button (visible when sidebar is closed) */}
      {!isOpen && (
        <button
          onClick={toggleSidebar}
          className="fixed right-0 top-1/2 -translate-y-1/2 bg-blue-600 hover:bg-blue-700 text-white p-3 rounded-l-lg shadow-lg transition-all z-40"
          aria-label="Открыть сайдбар"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>
      )}

      {/* Sidebar */}
      <div
        ref={sidebarRef}
        className={`fixed right-0 top-0 h-full bg-white dark:bg-gray-800 shadow-2xl transition-transform duration-300 z-50 ${isOpen ? 'translate-x-0' : 'translate-x-full'
          }`}
        style={{ width: `${width}px` }}
      >
        {/* Resize Handle */}
        <div
          onMouseDown={handleMouseDown}
          className="absolute left-0 top-0 w-1 h-full cursor-col-resize hover:bg-blue-500 transition-colors"
          style={{
            background: isResizing ? '#3b82f6' : 'transparent',
          }}
        >
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-20 bg-gray-300 dark:bg-gray-600 rounded-r" />
        </div>

        {/* Sidebar Content */}
        <div className="flex flex-col h-full pl-2">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Редактор
            </h2>
            <button
              onClick={toggleSidebar}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              aria-label="Закрыть сайдбар"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6 text-gray-600 dark:text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto">
            {children}
          </div>
        </div>
      </div>

      {/* Overlay (visible when sidebar is open) */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 transition-opacity"
          onClick={toggleSidebar}
        />
      )}
    </>
  );
}
