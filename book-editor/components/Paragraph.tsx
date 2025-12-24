'use client';

import { ParagraphWithReferences } from '@/types/paragraph-context';
import { replaceFormulaPlaceholders, renderLatex, replaceLiteraturePlaceholders, replaceSymbolPlaceholders, replaceMarkdownLinks } from '@/lib/latex-renderer';
import Link from 'next/link';

interface ParagraphProps {
  paragraph: ParagraphWithReferences;
  isTarget?: boolean;
  renderFormulas?: boolean;
  showFormulasContext?: boolean;
  showParagraphId?: boolean;
  showSymbols?: boolean;
}

export function Paragraph({
  paragraph,
  isTarget = false,
  renderFormulas = true,
  showFormulasContext = false,
  showParagraphId = false,
  showSymbols = true,
}: ParagraphProps) {
  // Заменяем {{formula:id}} на LaTeX формулы (с подстановкой символов в формулы)
  let paragraphContent = paragraph.content;

  // Преобразуем переводы строк в <br> теги ДО рендеринга формул
  paragraphContent = paragraphContent.replace(/\n/g, '<br>');

  if (renderFormulas && paragraph.formulas.length > 0) {
    paragraphContent = replaceFormulaPlaceholders(
      paragraphContent,
      paragraph.formulas,
      paragraph.symbols // передаем символы для замены внутри формул
    );
  }

  // Заменяем {{symbol:id}} на LaTeX символы в тексте (после замены формул!)
  if (paragraph.symbols?.length > 0) {
    paragraphContent = replaceSymbolPlaceholders(paragraphContent, paragraph.symbols);
  }

  // Заменяем {{literature:id}} на ссылки
  if (paragraph.literature?.length > 0) {
    paragraphContent = replaceLiteraturePlaceholders(paragraphContent, paragraph.literature);
  }

  // Заменяем Markdown ссылки на HTML
  paragraphContent = replaceMarkdownLinks(paragraphContent);

  console.log('Final paragraph content:', paragraphContent);

  // Функция для обработки текста с формулами и символами
  const processText = (text: string): string => {
    let processed = text;

    // Заменяем {{formula:id}} на LaTeX формулы
    if (renderFormulas && paragraph.formulas.length > 0) {
      processed = replaceFormulaPlaceholders(
        processed,
        paragraph.formulas,
        paragraph.symbols
      );
    }

    // Заменяем {{symbol:id}} на LaTeX символы
    if (paragraph.symbols?.length > 0) {
      processed = replaceSymbolPlaceholders(processed, paragraph.symbols);
    }

    // Заменяем {{literature:id}} на ссылки
    if (paragraph.literature?.length > 0) {
      processed = replaceLiteraturePlaceholders(processed, paragraph.literature);
    }

    // Заменяем Markdown ссылки на HTML
    processed = replaceMarkdownLinks(processed);

    console.log('Processed text:', processed);

    return processed;
  };


  // Функция для конвертации JSON таблицы в HTML
  const convertTableJsonToHtml = (tableContent: string): string => {
    try {
      const tableData = JSON.parse(tableContent);

      if (!tableData.headers || !tableData.rows) {
        return tableContent; // Если это не JSON с таблицей, возвращаем как есть
      }

      let html = '<table class="min-w-full divide-y divide-gray-300 dark:divide-gray-600">';

      // Header - обрабатываем заголовки перед вставкой
      html += '<thead class="bg-gray-50 dark:bg-gray-800">';
      html += '<tr>';
      tableData.headers.forEach((header: string) => {
        const processedHeader = processText(header);
        html += `<th scope="col" class="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-gray-100">${processedHeader}</th>`;
      });
      html += '</tr>';
      html += '</thead>';

      // Body - обрабатываем ячейки перед вставкой
      html += '<tbody class="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900">';
      tableData.rows.forEach((row: string[]) => {
        html += '<tr>';
        row.forEach((cell: string, index: number) => {
          const processedCell = processText(cell);
          if (index === 0) {
            html += `<td class="whitespace-nowrap px-3 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">${processedCell}</td>`;
          } else {
            html += `<td class="whitespace-nowrap px-3 py-4 text-sm text-gray-700 dark:text-gray-300">${processedCell}</td>`;
          }
        });
        html += '</tr>';
      });
      html += '</tbody>';
      html += '</table>';

      return html;
    } catch (e) {
      // Если это не JSON или парсинг не удался, возвращаем как есть
      return tableContent;
    }
  };

  // Обрабатываем таблицы: конвертируем JSON в HTML с обработкой формул
  const processedTables = paragraph.tables.map(table => {
    // Конвертируем JSON в HTML таблицу (внутри уже обрабатываются формулы)
    const tableContent = convertTableJsonToHtml(table.content);

    return {
      ...table,
      processedContent: tableContent
    };
  });

  return (
    <div
      id={`paragraph-${paragraph.id}`}
      className={`
        mb-8 p-6 rounded-lg transition-all
        ${isTarget ? 'bg-yellow-100 dark:bg-yellow-900/30 ring-2 ring-yellow-500' : 'bg-gray-50 dark:bg-gray-800/50'}
        ${paragraph.verified ? 'ring-2 ring-green-500 dark:ring-green-400 dark:bg-green-900/30 text-white/20' : ''}
      `}
    >
      {/* Paragraph Content */}
      <div
        className="prose dark:prose-invert max-w-none mb-4"
        dangerouslySetInnerHTML={{ __html: paragraphContent }}
      />

      {/* Tables */}
      {processedTables.length > 0 && (
        <div className="mt-6 space-y-4">
          {processedTables.map((table) => (
            <div key={table.id} className="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
              <div
                className="overflow-x-auto prose dark:prose-invert max-w-none"
                dangerouslySetInnerHTML={{ __html: table.processedContent }}
              />
            </div>
          ))}
        </div>
      )}

      {/* Illustrations */}
      {paragraph.illustrations.length > 0 && (
        <div className="mt-6 space-y-4">
          {paragraph.illustrations.map((illustration) => (
            <figure key={illustration.id} className="text-center">
              {illustration.svg_content && (
                <div
                  className="inline-block"
                  dangerouslySetInnerHTML={{ __html: illustration.svg_content }}
                />
              )}
              {illustration.caption && (
                <figcaption className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                  {illustration.caption}
                </figcaption>
              )}
            </figure>
          ))}
        </div>
      )}

      {/* Formulas */}
      {showFormulasContext && paragraph.formulas.length > 0 && renderFormulas && (
        <div className="mt-6 space-y-4">
          {paragraph.formulas.map((formula) => (
            <div
              key={formula.id}
              className="text-center p-4 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700"
            >
              <div
                className="inline-block"
                dangerouslySetInnerHTML={{ __html: renderLatex(formula.latex, true) }}
              />
            </div>
          ))}
        </div>
      )}

      <Link href={`/read-in-context/${paragraph.id}`} className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
        Select
      </Link>

      {/* Paragraph ID (for debugging) */}
      {showParagraphId && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <span className="text-xs text-gray-400 dark:text-gray-600 font-mono">
            {paragraph.id}
          </span>
        </div>
      )}

      {showSymbols && paragraph.symbols && paragraph.symbols.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Используемые символы
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {paragraph.symbols.map((symbol) => (
              <div
                key={symbol.id}
                className="flex items-start gap-3 p-3 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <div className="shrink-0 w-12 h-10 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600">
                  <div dangerouslySetInnerHTML={{ __html: renderLatex(symbol.latex, false) }} />
                </div>
                <div className="flex-1 min-w-0">
                  {symbol.description && (
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {symbol.description}
                    </div>
                  )}
                  <div className="flex flex-wrap items-center gap-2 mt-1">
                    {symbol.value && (
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        {symbol.value}
                      </span>
                    )}
                    {symbol.units && (
                      <span className="text-xs text-gray-500 dark:text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">
                        {symbol.units}
                      </span>
                    )}
                  </div>
                  {!symbol.description && !symbol.value && !symbol.units && (
                    <div className="text-xs text-gray-400 dark:text-gray-500 font-mono">
                      {symbol.latex}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
