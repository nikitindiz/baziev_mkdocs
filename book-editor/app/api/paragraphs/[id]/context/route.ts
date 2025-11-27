import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';
import { ParagraphContextResponse } from '@/types/paragraph-context';

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const session = getSession();
    const { id } = await params;

    try {
        // Основной запрос для получения всей информации
        const query = `
      // Находим абзац и его секцию
      MATCH (p:Paragraph {id: $paragraphId})
      MATCH (s:Section)-[:HAS_PARAGRAPH]->(p)
      MATCH (c:Chapter)-[:HAS_SECTION]->(s)
      
      // Находим все абзацы секции с их связями
      MATCH (s)-[:HAS_PARAGRAPH]->(sectionParagraph:Paragraph)
      OPTIONAL MATCH (sectionParagraph)-[:CONTAINS_TABLE]->(t:Table)
      OPTIONAL MATCH (sectionParagraph)-[:CONTAINS_ILLUSTRATION]->(i:Illustration)
      OPTIONAL MATCH (sectionParagraph)-[:CONTAINS_FORMULA]->(f:Formula)
      OPTIONAL MATCH (sectionParagraph)-[:CITES]->(l:Literature)
      
      // Извлекаем ID символов из параграфов и формул
      WITH c, s, sectionParagraph, t, i, f, l,
           [x IN split(sectionParagraph.content, '{{symbol:') WHERE size(x) > 0 | 
            CASE WHEN x =~ '^[0-9]+.*' THEN split(split(x, '}}')[0], ':')[0] ELSE null END
           ] + 
           CASE WHEN f.latex IS NOT NULL THEN
             [x IN split(f.latex, '{{symbol:') WHERE size(x) > 0 | 
              CASE WHEN x =~ '^[0-9]+.*' THEN split(split(x, '}}')[0], ':')[0] ELSE null END
             ]
           ELSE []
           END as symbolIds
      
      // Получаем символы по найденным ID
      UNWIND CASE WHEN size([sid IN symbolIds WHERE sid IS NOT NULL]) > 0 
                  THEN [sid IN symbolIds WHERE sid IS NOT NULL] 
                  ELSE [null] END as symbolId
      OPTIONAL MATCH (sym:Symbol {id: symbolId})
      
      // Находим предыдущую и следующую главы
      OPTIONAL MATCH (c)-[:PREVIOUS]->(prevChapter:Chapter)
      OPTIONAL MATCH (c)-[:NEXT]->(nextChapter:Chapter)
      
      // Находим предыдущую и следующую секции
      OPTIONAL MATCH (s)-[:PREVIOUS]->(prevSection:Section)
      OPTIONAL MATCH (s)-[:NEXT]->(nextSection:Section)
      
      // Возвращаем все данные
      RETURN 
        c.id as chapterId,
        c.title as chapterTitle,
        c.order as chapterOrder,
        s.id as sectionId,
        s.title as sectionTitle,
        s.number as sectionNumber,
        s.order as sectionOrder,
        sectionParagraph.id as paragraphId,
        sectionParagraph.content as paragraphContent,
        sectionParagraph.order as paragraphOrder,
        sectionParagraph.verified as paragraphVerified,
        collect(DISTINCT {
          id: t.id,
          content: t.content,
          html_attributes: t.html_attributes,
          type: t.type
        }) as tables,
        collect(DISTINCT {
          id: i.id,
          caption: i.caption,
          svg_content: i.svg_content,
          wrapper_html: i.wrapper_html,
          type: i.type
        }) as illustrations,
        collect(DISTINCT {
          id: f.id,
          latex: f.latex,
          wrapper_html: f.wrapper_html,
          type: f.type,
          is_symbol: f.is_symbol,
          symbol_parse_confidence: f.symbol_parse_confidence,
          symbol_definition: f.symbol_definition
        }) as formulas,
        collect(DISTINCT {
          id: l.id,
          number: l.number,
          text: l.text
        }) as literature,
        collect(DISTINCT {
          id: sym.id,
          latex: sym.latex,
          description: sym.description,
          units: sym.units
        }) as symbols,
        prevChapter.id as prevChapterId,
        prevChapter.title as prevChapterTitle,
        prevChapter.order as prevChapterOrder,
        nextChapter.id as nextChapterId,
        nextChapter.title as nextChapterTitle,
        nextChapter.order as nextChapterOrder,
        prevSection.id as prevSectionId,
        prevSection.title as prevSectionTitle,
        prevSection.number as prevSectionNumber,
        prevSection.order as prevSectionOrder,
        nextSection.id as nextSectionId,
        nextSection.title as nextSectionTitle,
        nextSection.number as nextSectionNumber,
        nextSection.order as nextSectionOrder
      ORDER BY sectionParagraph.order
    `;

        const result = await session.run(query, { paragraphId: id });

        if (result.records.length === 0) {
            return NextResponse.json(
                { error: 'Paragraph not found or not associated with any section' },
                { status: 404 },
            );
        }

        // Извлекаем данные из первой записи (глава и секция одинаковы для всех)
        const firstRecord = result.records[0];

        const chapter = {
            id: firstRecord.get('chapterId'),
            title: firstRecord.get('chapterTitle'),
            order: firstRecord.get('chapterOrder')?.toNumber() || 0,
        };

        const section = {
            id: firstRecord.get('sectionId'),
            title: firstRecord.get('sectionTitle'),
            number: firstRecord.get('sectionNumber') || undefined,
            order: firstRecord.get('sectionOrder')?.toNumber() || 0,
        };

        // Получаем ID предыдущей и следующей секций
        const prevSectionId = firstRecord.get('prevSectionId');
        const nextSectionId = firstRecord.get('nextSectionId');

        // Делаем отдельные запросы для получения первых абзацев prev/next секций
        let prevSectionFirstParagraphId = null;
        let nextSectionFirstParagraphId = null;

        if (prevSectionId) {
            const prevQuery = `
        MATCH (s:Section {id: $sectionId})-[:HAS_PARAGRAPH]->(p:Paragraph)
        RETURN p.id as paragraphId, p.order as paragraphOrder
        ORDER BY p.order ASC
        LIMIT 1
      `;
            const prevResult = await session.run(prevQuery, { sectionId: prevSectionId });
            if (prevResult.records.length > 0) {
                prevSectionFirstParagraphId = prevResult.records[0].get('paragraphId');
            }
        }

        if (nextSectionId) {
            const nextQuery = `
        MATCH (s:Section {id: $sectionId})-[:HAS_PARAGRAPH]->(p:Paragraph)
        RETURN p.id as paragraphId, p.order as paragraphOrder
        ORDER BY p.order ASC
        LIMIT 1
      `;
            const nextResult = await session.run(nextQuery, { sectionId: nextSectionId });
            if (nextResult.records.length > 0) {
                nextSectionFirstParagraphId = nextResult.records[0].get('paragraphId');
            }
        }

        // Собираем все абзацы с их связями
        const paragraphsMap = new Map();

        result.records.forEach((record) => {
            const pId = record.get('paragraphId');

            if (!paragraphsMap.has(pId)) {
                const tables = record
                    .get('tables')
                    .filter((t: any) => t.id !== null)
                    .map((t: any) => ({
                        id: t.id,
                        content: t.content || '',
                        html_attributes: t.html_attributes || undefined,
                        type: t.type || undefined,
                    }));

                const illustrations = record
                    .get('illustrations')
                    .filter((i: any) => i.id !== null)
                    .map((i: any) => ({
                        id: i.id,
                        caption: i.caption || undefined,
                        svg_content: i.svg_content || undefined,
                        wrapper_html: i.wrapper_html || undefined,
                        type: i.type || undefined,
                    }));

                const formulas = record
                    .get('formulas')
                    .filter((f: any) => f.id !== null)
                    .map((f: any) => ({
                        id: f.id,
                        latex: f.latex.replace(/^\$+(.*?)\$+(.*?)/g, '$1 $2') || '',
                        wrapper_html: f.wrapper_html || undefined,
                        type: f.type || undefined,
                        is_symbol: f.is_symbol || undefined,
                        symbol_parse_confidence: f.symbol_parse_confidence || undefined,
                        symbol_definition: f.symbol_definition || undefined,
                    }));

                const literature = record
                    .get('literature')
                    .filter((lit: any) => lit.id !== null)
                    .map((lit: any) => ({
                        id: lit.id,
                        number: lit.number ? lit.number.toNumber() : undefined,
                        text: lit.text || undefined,
                    }));

                const symbols = record
                    .get('symbols')
                    .filter((sym: any) => sym.id !== null)
                    .map((sym: any) => ({
                        id: sym.id,
                        latex: sym.latex || '',
                        description: sym.description || undefined,
                        units: sym.units || undefined,
                    }));

                paragraphsMap.set(pId, {
                    id: pId,
                    content: record.get('paragraphContent') || '',
                    order: record.get('paragraphOrder')?.toNumber() || 0,
                    verified: record.get('paragraphVerified') || false,
                    tables,
                    illustrations,
                    formulas,
                    literature,
                    symbols,
                });
            }
        });

        // Преобразуем Map в массив и сортируем по order
        const paragraphs = Array.from(paragraphsMap.values()).sort((a, b) => a.order - b.order);

        // Метаданные о предыдущей и следующей главах
        const prevChapterId = firstRecord.get('prevChapterId');
        const nextChapterId = firstRecord.get('nextChapterId');

        const response: ParagraphContextResponse = {
            chapter,
            section,
            paragraphs,
            metadata: {
                previousChapter: prevChapterId
                    ? {
                          id: prevChapterId,
                          title: firstRecord.get('prevChapterTitle'),
                          order: firstRecord.get('prevChapterOrder')?.toNumber() || 0,
                      }
                    : null,
                nextChapter: nextChapterId
                    ? {
                          id: nextChapterId,
                          title: firstRecord.get('nextChapterTitle'),
                          order: firstRecord.get('nextChapterOrder')?.toNumber() || 0,
                      }
                    : null,
                previousSection: prevSectionId
                    ? {
                          id: prevSectionId,
                          title: firstRecord.get('prevSectionTitle'),
                          number: firstRecord.get('prevSectionNumber') || undefined,
                          order: firstRecord.get('prevSectionOrder')?.toNumber() || 0,
                          firstParagraphId: prevSectionFirstParagraphId,
                      }
                    : null,
                nextSection: nextSectionId
                    ? {
                          id: nextSectionId,
                          title: firstRecord.get('nextSectionTitle'),
                          number: firstRecord.get('nextSectionNumber') || undefined,
                          order: firstRecord.get('nextSectionOrder')?.toNumber() || 0,
                          firstParagraphId: nextSectionFirstParagraphId,
                      }
                    : null,
            },
        };

        return NextResponse.json(response);
    } catch (error) {
        console.error('Error fetching paragraph context:', error);
        return NextResponse.json(
            {
                error: 'Failed to fetch paragraph context',
                details: error instanceof Error ? error.message : 'Unknown error',
            },
            { status: 500 },
        );
    } finally {
        await session.close();
    }
}
