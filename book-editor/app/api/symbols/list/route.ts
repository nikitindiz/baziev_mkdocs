import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';

export interface SymbolListItem {
    id: string;
    latex: string;
    description?: string;
    units?: string;
    value?: string;
    chapterId?: string;
    chapterTitle?: string;
    sectionId?: string;
    sectionTitle?: string;
}

export async function GET(request: NextRequest) {
    const session = getSession();

    try {
        const { searchParams } = new URL(request.url);
        const searchText = searchParams.get('search') || '';
        const chapterId = searchParams.get('chapterId');
        const sectionId = searchParams.get('sectionId');
        const sortBy = searchParams.get('sortBy') || 'latex'; // 'latex' or 'created'

        // Построение запроса с фильтрами
        let whereConditions: string[] = [];
        const params: Record<string, any> = {};

        // Фильтр по тексту (поиск в latex, description, units, value)
        if (searchText) {
            whereConditions.push(`(
                toLower(s.latex) CONTAINS toLower($searchText) OR
                toLower(COALESCE(s.description, '')) CONTAINS toLower($searchText) OR
                toLower(COALESCE(s.units, '')) CONTAINS toLower($searchText) OR
                toLower(COALESCE(s.value, '')) CONTAINS toLower($searchText)
            )`);
            params.searchText = searchText;
        }

        // Фильтр по главе
        if (chapterId) {
            whereConditions.push('c.id = $chapterId');
            params.chapterId = chapterId;
        }

        // Фильтр по секции
        if (sectionId) {
            whereConditions.push('sec.id = $sectionId');
            params.sectionId = sectionId;
        }

        const whereClause =
            whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';

        // Определение сортировки
        const orderClause =
            sortBy === 'created'
                ? 'ORDER BY s.id DESC' // id содержит timestamp
                : 'ORDER BY s.latex ASC';

        const query = `
            MATCH (s:Symbol)
            OPTIONAL MATCH (s)<-[:HAS_SYMBOL]-(f:Formula)
            OPTIONAL MATCH (f)<-[:HAS_FORMULA]-(p:Paragraph)
            OPTIONAL MATCH (p)-[:BELONGS_TO_SECTION]->(sec:Section)
            OPTIONAL MATCH (sec)-[:BELONGS_TO_CHAPTER]->(c:Chapter)
            ${whereClause}
            WITH DISTINCT s, c, sec
            RETURN s.id as id,
                   s.latex as latex,
                   s.description as description,
                   s.units as units,
                   s.value as value,
                   c.id as chapterId,
                   c.title as chapterTitle,
                   sec.id as sectionId,
                   sec.title as sectionTitle
            ${orderClause}
        `;

        const result = await session.run(query, params);

        const symbols: SymbolListItem[] = result.records.map((record) => ({
            id: record.get('id'),
            latex: record.get('latex') || '',
            description: record.get('description') || undefined,
            units: record.get('units') || undefined,
            value: record.get('value') || undefined,
            chapterId: record.get('chapterId') || undefined,
            chapterTitle: record.get('chapterTitle') || undefined,
            sectionId: record.get('sectionId') || undefined,
            sectionTitle: record.get('sectionTitle') || undefined,
        }));

        return NextResponse.json({ symbols });
    } catch (error) {
        console.error('Error fetching symbols list:', error);
        return NextResponse.json({ error: 'Failed to fetch symbols list' }, { status: 500 });
    } finally {
        await session.close();
    }
}
