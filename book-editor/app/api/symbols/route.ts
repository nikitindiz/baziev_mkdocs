import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';

export interface SymbolCreateRequest {
    latex: string;
    description?: string;
    units?: string;
    value?: string;
}

export async function POST(request: NextRequest) {
    const session = getSession();

    try {
        const body: SymbolCreateRequest = await request.json();

        // Проверяем обязательное поле
        if (!body.latex) {
            return NextResponse.json({ error: 'LaTeX is required' }, { status: 400 });
        }

        // Генерируем ID для нового символа
        const id = Date.now().toString();

        const query = `
            CREATE (s:Symbol {
                id: $id,
                latex: $latex,
                description: $description,
                units: $units,
                value: $value
            })
            RETURN s
        `;

        const result = await session.run(query, {
            id,
            latex: body.latex,
            description: body.description || null,
            units: body.units || null,
            value: body.value || null,
        });

        const record = result.records[0];
        const s = record.get('s').properties;

        const symbol = {
            id: s.id,
            latex: s.latex || '',
            description: s.description || undefined,
            units: s.units || undefined,
            value: s.value || undefined,
        };

        return NextResponse.json(symbol, { status: 201 });
    } catch (error) {
        console.error('Error creating symbol:', error);
        return NextResponse.json(
            {
                error: 'Failed to create symbol',
                details: error instanceof Error ? error.message : 'Unknown error',
            },
            { status: 500 },
        );
    } finally {
        await session.close();
    }
}
