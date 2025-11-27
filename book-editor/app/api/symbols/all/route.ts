import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';

export interface SymbolData {
    id: string;
    latex: string;
    description?: string;
    units?: string;
    value?: string;
}

export async function GET(request: NextRequest) {
    const session = getSession();

    try {
        // Получаем все символы из базы
        const query = `
            MATCH (s:Symbol)
            RETURN 
                s.id as id,
                s.latex as latex,
                s.description as description,
                s.units as units,
                s.value as value
            ORDER BY s.latex
        `;

        const result = await session.run(query);

        const symbols: SymbolData[] = result.records.map((record) => ({
            id: record.get('id'),
            latex: record.get('latex') || '',
            description: record.get('description') || undefined,
            units: record.get('units') || undefined,
            value: record.get('value') || undefined,
        }));

        return NextResponse.json({ symbols });
    } catch (error) {
        console.error('Error fetching all symbols:', error);
        return NextResponse.json(
            {
                error: 'Failed to fetch symbols',
                details: error instanceof Error ? error.message : 'Unknown error',
            },
            { status: 500 },
        );
    } finally {
        await session.close();
    }
}
