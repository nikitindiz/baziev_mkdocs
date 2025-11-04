import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';
import { Paragraph, ParagraphsResponse } from '@/types/paragraph';

export async function GET(request: NextRequest) {
  const session = getSession();
  
  try {
    const searchParams = request.nextUrl.searchParams;
    const limit = parseInt(searchParams.get('limit') || '10', 10);
    const cursor = searchParams.get('cursor') || null;
    const sectionId = searchParams.get('section_id') || null;
    const chapterId = searchParams.get('chapter_id') || null;

    // Валидация limit
    if (limit < 1 || limit > 100) {
      return NextResponse.json(
        { error: 'Limit must be between 1 and 100' },
        { status: 400 }
      );
    }

    // Построение фильтров
    let whereClause = '';
    const params: Record<string, any> = {};

    if (cursor) {
      whereClause += whereClause ? ' AND ' : 'WHERE ';
      whereClause += 'p.id > $cursor';
      params.cursor = cursor;
    }

    if (sectionId) {
      whereClause += whereClause ? ' AND ' : 'WHERE ';
      whereClause += 'p.section_id = $sectionId';
      params.sectionId = sectionId;
    }

    if (chapterId) {
      whereClause += whereClause ? ' AND ' : 'WHERE ';
      whereClause += 'p.chapter_id = $chapterId';
      params.chapterId = chapterId;
    }

    // Запрос параграфов с previous и next
    // ВАЖНО: LIMIT должен быть встроен в запрос, т.к. Neo4j требует INTEGER литерал
    const query = `
      MATCH (p:Paragraph)
      ${whereClause}
      OPTIONAL MATCH (p)-[:PREVIOUS]->(prev:Paragraph)
      OPTIONAL MATCH (p)-[:NEXT]->(next:Paragraph)
      RETURN p, prev, next
      ORDER BY p.id
      LIMIT ${limit + 1}
    `;

    const result = await session.run(query, params);

    const paragraphs: Paragraph[] = result.records.slice(0, limit).map(record => {
      const p = record.get('p').properties;
      const prev = record.get('prev');
      const next = record.get('next');

      return {
        id: p.id,
        text: p.content || p.text || '', // content - основное поле, text - запасное
        order: p.order ? parseInt(p.order) : undefined,
        section_id: p.section_id || undefined,
        chapter_id: p.chapter_id || undefined,
        previous: prev ? {
          id: prev.properties.id,
          text: prev.properties.content || prev.properties.text || ''
        } : null,
        next: next ? {
          id: next.properties.id,
          text: next.properties.content || next.properties.text || ''
        } : null
      };
    });

    // Определение следующего курсора
    const hasMore = result.records.length > limit;
    const nextCursor = hasMore ? paragraphs[paragraphs.length - 1].id : null;

    // Подсчет общего количества (опционально, только для первого запроса)
    let total: number | undefined;
    if (!cursor) {
      const countQuery = `
        MATCH (p:Paragraph)
        ${whereClause.replace('p.id > $cursor', '')}
        RETURN count(p) as total
      `;
      const countParams = { ...params };
      delete countParams.cursor;
      delete countParams.limit;
      
      const countResult = await session.run(countQuery, countParams);
      total = countResult.records[0]?.get('total').toNumber();
    }

    const response: ParagraphsResponse = {
      data: paragraphs,
      pagination: {
        cursor: nextCursor,
        hasMore,
        total
      }
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Error fetching paragraphs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch paragraphs' },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
