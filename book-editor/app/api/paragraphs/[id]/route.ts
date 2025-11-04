import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';
import { Paragraph } from '@/types/paragraph';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = getSession();
  const { id } = await params;
  
  try {
    // Запрос конкретного параграфа с previous и next
    const query = `
      MATCH (p:Paragraph {id: $id})
      OPTIONAL MATCH (p)-[:PREVIOUS]->(prev:Paragraph)
      OPTIONAL MATCH (p)-[:NEXT]->(next:Paragraph)
      RETURN p, prev, next
    `;

    const result = await session.run(query, { id });

    if (result.records.length === 0) {
      return NextResponse.json(
        { error: 'Paragraph not found' },
        { status: 404 }
      );
    }

    const record = result.records[0];
    const p = record.get('p').properties;
    const prev = record.get('prev');
    const next = record.get('next');

    const paragraph: Paragraph = {
      id: p.id,
      text: p.text || '',
      order: p.order ? parseInt(p.order) : undefined,
      section_id: p.section_id || undefined,
      chapter_id: p.chapter_id || undefined,
      previous: prev ? {
        id: prev.properties.id,
        text: prev.properties.text || ''
      } : null,
      next: next ? {
        id: next.properties.id,
        text: next.properties.text || ''
      } : null
    };

    return NextResponse.json(paragraph);

  } catch (error) {
    console.error('Error fetching paragraph:', error);
    return NextResponse.json(
      { error: 'Failed to fetch paragraph' },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
