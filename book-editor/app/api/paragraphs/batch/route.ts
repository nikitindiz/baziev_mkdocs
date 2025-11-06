import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';
import { Paragraph } from '@/types/paragraph';

export async function POST(request: NextRequest) {
  const session = getSession();
  
  try {
    const body = await request.json();
    const { ids } = body;

    if (!ids || !Array.isArray(ids) || ids.length === 0) {
      return NextResponse.json(
        { error: 'Parameter "ids" must be a non-empty array' },
        { status: 400 }
      );
    }

    // Ограничение на количество параграфов в одном запросе
    if (ids.length > 100) {
      return NextResponse.json(
        { error: 'Maximum 100 IDs per request' },
        { status: 400 }
      );
    }

    // Запрос параграфов по списку ID
    const query = `
      MATCH (p:Paragraph)
      WHERE p.id IN $ids
      OPTIONAL MATCH (p)-[:PREVIOUS]->(prev:Paragraph)
      OPTIONAL MATCH (p)-[:NEXT]->(next:Paragraph)
      RETURN p, prev, next
    `;

    const result = await session.run(query, { ids });

    const paragraphs: Paragraph[] = result.records.map(record => {
      const p = record.get('p').properties;
      const prev = record.get('prev');
      const next = record.get('next');

      return {
        id: p.id,
        text: p.content || p.text || '',
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

    // Сортируем в том же порядке, что и запрошенные ID
    const sortedParagraphs = ids
      .map(id => paragraphs.find(p => p.id === id))
      .filter((p): p is Paragraph => p !== undefined);

    return NextResponse.json({
      data: sortedParagraphs,
      total: sortedParagraphs.length
    });

  } catch (error) {
    console.error('Error fetching paragraphs batch:', error);
    return NextResponse.json(
      { error: 'Failed to fetch paragraphs' },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
