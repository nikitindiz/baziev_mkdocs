import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';
import { LiteratureResponse } from '@/types/literature';

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
    const session = getSession();

    try {
        const { id } = params;

        if (!id) {
            return NextResponse.json({ error: 'Literature ID is required' }, { status: 400 });
        }

        // Запрос литературы по ID
        const query = `
      MATCH (l:Literature {id: $id})
      RETURN l
    `;

        const result = await session.run(query, { id });

        if (result.records.length === 0) {
            return NextResponse.json({ error: 'Literature not found' }, { status: 404 });
        }

        const literature = result.records[0].get('l').properties;

        const response: LiteratureResponse = {
            data: {
                id: literature.id,
                text: literature.text || '',
                author: literature.author || undefined,
                title: literature.title || undefined,
                publication: literature.publication || undefined,
                source: literature.source || undefined,
                number: literature.number ? parseInt(literature.number) : undefined,
            },
        };

        return NextResponse.json(response);
    } catch (error) {
        console.error('Error fetching literature:', error);
        return NextResponse.json({ error: 'Failed to fetch literature' }, { status: 500 });
    } finally {
        await session.close();
    }
}
