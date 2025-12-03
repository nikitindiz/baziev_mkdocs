import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
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

        return NextResponse.json({
            formulasCount,
            paragraphsCount,
            totalUsages: formulasCount + paragraphsCount,
        });
    } catch (error) {
        console.error('Error fetching symbol usage:', error);
        return NextResponse.json({ error: 'Failed to fetch symbol usage' }, { status: 500 });
    } finally {
        await session.close();
    }
}
