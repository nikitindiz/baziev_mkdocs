'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ParagraphContextResponse } from '@/types/paragraph-context';
import { Paragraph } from '../components/Paragraph';
import { Navigation } from '../components/Navigation';
import { RightSidebar } from '../components/RightSidebar';

export default function ReadInContextPage() {
  const params = useParams();
  const paragraphId = decodeURI(params.id as string);
  
  const [context, setContext] = useState<ParagraphContextResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchContext() {
      try {
        setLoading(true);
        setError(null);

        console.log('Fetching context for paragraph ID:', paragraphId);
        
        const response = await fetch(`/api/paragraphs/${paragraphId}/context`);
        
        if (!response.ok) {
          throw new Error(`Failed to fetch context: ${response.statusText}`);
        }
        
        const data = await response.json();
        setContext(data);
        
        // Scroll to the target paragraph after data is loaded
        setTimeout(() => {
          const targetElement = document.getElementById(`paragraph-${paragraphId}`);

          console.log('Scrolling to paragraph element:', targetElement, `paragraph-${paragraphId}`);
          if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        }, 100);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
      } finally {
        setLoading(false);
      }
    }

    if (paragraphId) {
      fetchContext();
    }
  }, [paragraphId]);

  if (loading) {
    return (
      <div className="min-h-screen overflow-hidden flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Загрузка...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen overflow-hidden flex items-center justify-center">
        <div className="text-center max-w-md p-8 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <h2 className="text-xl font-bold text-red-600 dark:text-red-400 mb-2">Ошибка</h2>
          <p className="text-gray-700 dark:text-gray-300">{error}</p>
        </div>
      </div>
    );
  }

  if (!context) {
    return (
      <div className="min-h-screen overflow-hidden flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400">Контекст не найден</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="min-h-screen overflow-hidden bg-gray-50 dark:bg-gray-900">
        <div className="max-w-4xl mx-auto py-8 px-4">
          {/* Top Navigation */}
          <div className="mb-8">
            <Navigation
              previousSection={context.metadata.previousSection}
              nextSection={context.metadata.nextSection}
            />
          </div>

          {/* Chapter Title */}
          <header className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {context.chapter.title}
            </h1>
            <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300">
              {context.section.number && `§${context.section.number} `}
              {context.section.title}
            </h2>
          </header>

          {/* Paragraphs */}
          <main className="space-y-6">
            {context.paragraphs.map((paragraph) => (
              <Paragraph
                key={paragraph.id}
                paragraph={paragraph}
                isTarget={paragraph.id === paragraphId}
              />
            ))}
          </main>

          {/* Bottom Navigation */}
          <div className="mt-8">
            <Navigation
              previousSection={context.metadata.previousSection}
              nextSection={context.metadata.nextSection}
            />
          </div>
        </div>
      </div>

      {/* Right Sidebar */}
      <RightSidebar>
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            Здесь будут располагаться формы для редактирования
          </p>
        </div>
      </RightSidebar>
    </>
  );
}
