'use client';

import { useEffect } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ParagraphContextResponse } from '@/types/paragraph-context';
import { Paragraph } from '../../../components/Paragraph';
import { Navigation } from '../../../components/Navigation';
import { RightSidebar } from '../../../components/RightSidebar';
import { ParagraphEditor } from '../../../components/ParagraphEditor';
import { FormulaEditor } from '../../../components/FormulaEditor';

async function fetchParagraphContext(paragraphId: string): Promise<ParagraphContextResponse> {
  console.log('Fetching context for paragraph ID:', paragraphId);

  const response = await fetch(`/api/paragraphs/${paragraphId}/context`);

  if (!response.ok) {
    throw new Error(`Failed to fetch context: ${response.statusText}`);
  }

  return response.json();
}

export default function ReadInContextPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const paragraphId = decodeURI(params.id as string);
  const selectedFormulaId = searchParams.get('selected-formula');

  // Используем React Query для получения контекста параграфа
  const { data: context, isLoading: loading, error } = useQuery({
    queryKey: ['paragraph-context', paragraphId],
    queryFn: () => fetchParagraphContext(paragraphId),
    enabled: !!paragraphId,
  });

  // Scroll to the target paragraph after data is loaded
  useEffect(() => {
    if (!context) return;

    setTimeout(() => {
      const targetElement = document.getElementById(`paragraph-${paragraphId}`);
      console.log('Scrolling to paragraph element:', targetElement, `paragraph-${paragraphId}`);
      if (targetElement) {
        targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 100);
  }, [context, paragraphId]);

  // Handle formula clicks - only allow clicking formulas in the selected paragraph
  useEffect(() => {
    const handleFormulaClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const formulaElement = target.closest('.symbol-formula, .regular-formula');

      if (!formulaElement) return;

      // Check if the formula is within the selected paragraph
      const paragraphElement = formulaElement.closest(`#paragraph-${paragraphId}`);

      if (!paragraphElement) {
        // Formula is not in the selected paragraph, ignore click
        return;
      }

      const formulaId = formulaElement.getAttribute('data-formula-id');

      if (formulaId) {
        // Update URL with selected-formula query parameter
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.set('selected-formula', formulaId);
        router.push(newUrl.pathname + newUrl.search, { scroll: false });
      }
    };

    document.addEventListener('click', handleFormulaClick);

    return () => {
      document.removeEventListener('click', handleFormulaClick);
    };
  }, [paragraphId, router]);

  // Apply 'selected' class to the selected formula
  useEffect(() => {
    // Wait for context to load before applying selection
    if (!context) return;

    if (!selectedFormulaId) {
      // Remove all 'selected' classes
      document.querySelectorAll('.symbol-formula.selected, .regular-formula.selected').forEach(el => {
        el.classList.remove('selected');
      });
      return;
    }

    // Remove all 'selected' classes first
    document.querySelectorAll('.symbol-formula.selected, .regular-formula.selected').forEach(el => {
      el.classList.remove('selected');
    });

    // Add 'selected' class to the selected formula after a slight delay
    // to ensure DOM is fully rendered
    setTimeout(() => {
      const selectedFormula = document.querySelector(
        `[data-formula-id="${selectedFormulaId}"]`
      );

      if (selectedFormula) {
        selectedFormula.classList.add('selected');

        // Scroll to the selected formula
        setTimeout(() => {
          selectedFormula.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
      }
    }, 150);
  }, [selectedFormulaId, context]);

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
          <p className="text-gray-700 dark:text-gray-300">{error instanceof Error ? error.message : 'Unknown error'}</p>
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
              {/* {context.section.number && `${context.section.number} `} */}
              §{context.section.title}
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
        {selectedFormulaId ? (
          <FormulaEditor formulaId={selectedFormulaId} />
        ) : paragraphId ? (
          <ParagraphEditor paragraphId={paragraphId} />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500 dark:text-gray-400">
              <p>Параграф не выбран</p>
            </div>
          </div>
        )}
      </RightSidebar>
    </>
  );
}
