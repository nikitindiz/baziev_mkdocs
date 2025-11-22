import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';
import { Paragraph } from '@/types/paragraph';

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
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
            return NextResponse.json({ error: 'Paragraph not found' }, { status: 404 });
        }

        const record = result.records[0];
        const p = record.get('p').properties;
        const prev = record.get('prev');
        const next = record.get('next');

        const paragraph: Paragraph = {
            id: p.id,
            text: p.content || p.text || '', // content - основное поле, text - запасное
            order: p.order ? parseInt(p.order) : undefined,
            section_id: p.section_id || undefined,
            chapter_id: p.chapter_id || undefined,
            verified: p.verified || false,
            previous: prev
                ? {
                      id: prev.properties.id,
                      text: prev.properties.content || prev.properties.text || '',
                  }
                : null,
            next: next
                ? {
                      id: next.properties.id,
                      text: next.properties.content || next.properties.text || '',
                  }
                : null,
        };

        return NextResponse.json(paragraph);
    } catch (error) {
        console.error('Error fetching paragraph:', error);
        return NextResponse.json({ error: 'Failed to fetch paragraph' }, { status: 500 });
    } finally {
        await session.close();
    }
}

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const session = getSession();
    const { id } = await params;

    try {
        const body = await request.json();
        const { content, display_name, order, verified } = body;

        // Проверяем, что хотя бы одно поле для обновления передано
        if (
            content === undefined &&
            display_name === undefined &&
            order === undefined &&
            verified === undefined
        ) {
            return NextResponse.json({ error: 'No fields to update provided' }, { status: 400 });
        }

        // Формируем динамический запрос для обновления только переданных полей
        const setClauses: string[] = [];
        const queryParams: Record<string, any> = { id };

        if (content !== undefined) {
            setClauses.push('p.content = $content');
            queryParams.content = content;

            // Пересчитываем количество слов
            const wordCount = content
                .trim()
                .split(/\s+/)
                .filter((word: string) => word.length > 0).length;
            setClauses.push('p.word_count = $word_count');
            queryParams.word_count = wordCount;
        }

        if (display_name !== undefined) {
            setClauses.push('p.display_name = $display_name');
            queryParams.display_name = display_name;
        }

        if (order !== undefined) {
            setClauses.push('p.order = $order');
            queryParams.order = order;
        }

        if (verified !== undefined) {
            setClauses.push('p.verified = $verified');
            queryParams.verified = verified;
        }

        const query = `
      MATCH (p:Paragraph {id: $id})
      SET ${setClauses.join(', ')}
      RETURN p
    `;

        const result = await session.run(query, queryParams);

        if (result.records.length === 0) {
            return NextResponse.json({ error: 'Paragraph not found' }, { status: 404 });
        }

        const record = result.records[0];
        const p = record.get('p').properties;

        const updatedParagraph: Paragraph = {
            id: p.id,
            text: p.content || p.text || '',
            order: p.order ? parseInt(p.order) : undefined,
            section_id: p.section_id || undefined,
            chapter_id: p.chapter_id || undefined,
            verified: p.verified || false,
            previous: null,
            next: null,
        };

        return NextResponse.json(updatedParagraph);
    } catch (error) {
        console.error('Error updating paragraph:', error);
        return NextResponse.json({ error: 'Failed to update paragraph' }, { status: 500 });
    } finally {
        await session.close();
    }
}
