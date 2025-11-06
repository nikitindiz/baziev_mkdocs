import { NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';
import { ParagraphsMetaResponse, ParagraphMeta } from '@/types/paragraph-meta';

export async function GET() {
  const session = getSession();
  
  try {
    // Запрос всех параграфов с минимальными данными (без content/text)
    const query = `
      MATCH (p:Paragraph)
      RETURN p.id as id, p.order as order, p.section_id as section_id, p.chapter_id as chapter_id
      ORDER BY p.id
    `;

    const result = await session.run(query);

    const paragraphs: ParagraphMeta[] = result.records.map(record => ({
      id: record.get('id'),
      order: record.get('order') ? parseInt(record.get('order')) : undefined,
      section_id: record.get('section_id') || undefined,
      chapter_id: record.get('chapter_id') || undefined,
    }));

    const response: ParagraphsMetaResponse = {
      data: paragraphs,
      total: paragraphs.length
    };

    return NextResponse.json(response);

  } catch (error) {
    console.error('Error fetching paragraphs meta:', error);
    return NextResponse.json(
      { error: 'Failed to fetch paragraphs metadata' },
      { status: 500 }
    );
  } finally {
    await session.close();
  }
}
