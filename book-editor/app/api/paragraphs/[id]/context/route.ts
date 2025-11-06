import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';
import { ParagraphContextResponse } from '@/types/paragraph-context';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
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
      
      // Находим предыдущую и следующую главы
      OPTIONAL MATCH (c)-[:PREVIOUS]->(prevChapter:Chapter)
      OPTIONAL MATCH (c)-[:NEXT]->(nextChapter:Chapter)
      
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
          type: f.type
        }) as formulas,
        prevChapter.id as prevChapterId,
        prevChapter.title as prevChapterTitle,
        prevChapter.order as prevChapterOrder,
        nextChapter.id as nextChapterId,
        nextChapter.title as nextChapterTitle,
        nextChapter.order as nextChapterOrder
      ORDER BY sectionParagraph.order
    `;

    const result = await session.run(query, { paragraphId: id });

    if (result.records.length === 0) {
      return NextResponse.json(
        { error: 'Paragraph not found or not associated with any section' },
        { status: 404 }
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

    // Собираем все абзацы с их связями
    const paragraphsMap = new Map();
    
    result.records.forEach(record => {
      const pId = record.get('paragraphId');
      
      if (!paragraphsMap.has(pId)) {
        const tables = record.get('tables')
          .filter((t: any) => t.id !== null)
          .map((t: any) => ({
            id: t.id,
            content: t.content || '',
            html_attributes: t.html_attributes || undefined,
            type: t.type || undefined,
          }));

        const illustrations = record.get('illustrations')
          .filter((i: any) => i.id !== null)
          .map((i: any) => ({
            id: i.id,
            caption: i.caption || undefined,
            svg_content: i.svg_content || undefined,
            wrapper_html: i.wrapper_html || undefined,
            type: i.type || undefined,
          }));

        const formulas = record.get('formulas')
          .filter((f: any) => f.id !== null)
          .map((f: any) => ({
            id: f.id,
            latex: f.latex || '',
            wrapper_html: f.wrapper_html || undefined,
            type: f.type || undefined,
          }));

        paragraphsMap.set(pId, {
          id: pId,
          content: record.get('paragraphContent') || '',
          order: record.get('paragraphOrder')?.toNumber() || 0,
          tables,
          illustrations,
          formulas,
        });
      }
    });

    // Преобразуем Map в массив и сортируем по order
    const paragraphs = Array.from(paragraphsMap.values())
      .sort((a, b) => a.order - b.order);

    // Метаданные о предыдущей и следующей главах
    const prevChapterId = firstRecord.get('prevChapterId');
    const nextChapterId = firstRecord.get('nextChapterId');

    const response: ParagraphContextResponse = {
      chapter,
      section,
      paragraphs,
      metadata: {
        previousChapter: prevChapterId ? {
          id: prevChapterId,
          title: firstRecord.get('prevChapterTitle'),
          order: firstRecord.get('prevChapterOrder')?.toNumber() || 0,
        } : null,
        nextChapter: nextChapterId ? {
          id: nextChapterId,
          title: firstRecord.get('nextChapterTitle'),
          order: firstRecord.get('nextChapterOrder')?.toNumber() || 0,
        } : null,
      },
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Error fetching paragraph context:', error);
    return NextResponse.json(
      { 
        error: 'Failed to fetch paragraph context',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
