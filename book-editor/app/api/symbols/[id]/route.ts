import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';

export interface Symbol {
    id: string;
    latex: string;
    description?: string;
    units?: string;
    value?: string;
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
            value: s.value,
        };

        return NextResponse.json(symbol);
    } catch (error) {
        console.error('Error fetching symbol:', error);
        return NextResponse.json({ error: 'Failed to fetch symbol' }, { status: 500 });
    } finally {
        await session.close();
    }
}

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const session = getSession();
    const { id } = await params;

    try {
        const body = await request.json();

        // Проверяем обязательное поле
        if (!body.latex) {
            return NextResponse.json({ error: 'LaTeX is required' }, { status: 400 });
        }

        const query = `
            MATCH (s:Symbol {id: $id})
            SET s.latex = $latex,
                s.description = $description,
                s.units = $units,
                s.value = $value
            RETURN s
        `;

        const result = await session.run(query, {
            id,
            latex: body.latex,
            description: body.description || null,
            units: body.units || null,
            value: body.value || null,
        });

        if (result.records.length === 0) {
            return NextResponse.json({ error: 'Symbol not found' }, { status: 404 });
        }

        const record = result.records[0];
        const s = record.get('s').properties;

        const symbol: Symbol = {
            id: s.id,
            latex: s.latex || '',
            description: s.description || undefined,
            units: s.units || undefined,
            value: s.value || undefined,
        };

        return NextResponse.json(symbol);
    } catch (error) {
        console.error('Error updating symbol:', error);
        return NextResponse.json({ error: 'Failed to update symbol' }, { status: 500 });
    } finally {
        await session.close();
    }
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> },
) {
    const session = getSession();
    const { id } = await params;

    try {
        // Проверяем использование символа в формулах
        const checkFormulasQuery = `
            MATCH (f:Formula)
            WHERE f.latex CONTAINS ('{{symbol:' + $id + '}}')
            RETURN count(f) as formulasCount
        `;

        const formulasResult = await session.run(checkFormulasQuery, { id });
        const formulasCount = formulasResult.records[0].get('formulasCount').toNumber();

        // Проверяем использование символа в параграфах
        const checkParagraphsQuery = `
            MATCH (p:Paragraph)
            WHERE p.content CONTAINS ('{{symbol:' + $id + '}}')
            RETURN count(p) as paragraphsCount
        `;

        const paragraphsResult = await session.run(checkParagraphsQuery, { id });
        const paragraphsCount = paragraphsResult.records[0].get('paragraphsCount').toNumber();

        // Если символ используется, запрещаем удаление
        if (formulasCount > 0 || paragraphsCount > 0) {
            return NextResponse.json(
                {
                    error: 'Symbol is in use',
                    details: {
                        formulasCount,
                        paragraphsCount,
                        totalUsages: formulasCount + paragraphsCount,
                    },
                },
                { status: 409 },
            );
        }

        // Удаляем символ
        const deleteQuery = `
            MATCH (s:Symbol {id: $id})
            DELETE s
            RETURN count(s) as deletedCount
        `;

        const deleteResult = await session.run(deleteQuery, { id });
        const deletedCount = deleteResult.records[0].get('deletedCount').toNumber();

        if (deletedCount === 0) {
            return NextResponse.json({ error: 'Symbol not found' }, { status: 404 });
        }

        return NextResponse.json({ success: true, message: 'Symbol deleted successfully' });
    } catch (error) {
        console.error('Error deleting symbol:', error);
        return NextResponse.json({ error: 'Failed to delete symbol' }, { status: 500 });
    } finally {
        await session.close();
    }
}
