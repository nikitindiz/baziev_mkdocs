import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';

export interface Symbol {
    id: string;
    latex: string;
    description?: string;
    units?: string;
}

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const session = getSession();
    const { id } = await params;

    try {
        const query = `
            MATCH (s:Symbol {id: $id})
            RETURN s
        `;

        const result = await session.run(query, { id });

        if (result.records.length === 0) {
            return NextResponse.json({ error: 'Symbol not found' }, { status: 404 });
        }

        const record = result.records[0];
        const s = record.get('s').properties;

        const symbol: Symbol = {
            id: s.id,
            latex: s.latex || '',
            description: s.description,
            units: s.units,
        };

        return NextResponse.json(symbol);
    } catch (error) {
        console.error('Error fetching symbol:', error);
        return NextResponse.json({ error: 'Failed to fetch symbol' }, { status: 500 });
    } finally {
        await session.close();
    }
}
