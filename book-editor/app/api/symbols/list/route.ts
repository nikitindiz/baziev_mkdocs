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

        // Параметры для запроса
        const params: Record<string, any> = {};
        if (searchText) params.searchText = searchText;
        if (chapterId) params.chapterId = chapterId;
        if (sectionId) params.sectionId = sectionId;

        // Определение сортировки
        const orderClause =
            sortBy === 'created'
                ? 'ORDER BY s.id DESC' // id содержит timestamp
                : 'ORDER BY s.latex ASC';

        // Строим запрос в зависимости от фильтров
        let query = '';

        if (sectionId) {
            // Фильтр по секции - ищем символы, которые используются в формулах этой секции
            query = `
                MATCH (sec:Section {id: $sectionId})
                MATCH (sec)<-[:HAS_SECTION]-(c:Chapter)
                MATCH (sec)-[:HAS_PARAGRAPH]->(p:Paragraph)
                MATCH (p)-[:CONTAINS_FORMULA]->(f:Formula)
                WHERE f.latex CONTAINS '{{symbol:'
                WITH f, c, sec, [x IN split(f.latex, '{{symbol:') WHERE size(x) > 0 AND size(split(x, '}}')) > 0 | split(x, '}}')[0]] as symbolIds
                UNWIND symbolIds as symbolId
                MATCH (s:Symbol {id: symbolId})
                ${searchText ? 'WHERE (toLower(s.latex) CONTAINS toLower($searchText) OR toLower(COALESCE(s.description, "")) CONTAINS toLower($searchText) OR toLower(COALESCE(s.units, "")) CONTAINS toLower($searchText) OR toLower(COALESCE(s.value, "")) CONTAINS toLower($searchText))' : ''}
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
        } else if (chapterId) {
            // Фильтр по главе - ищем символы, которые используются в формулах этой главы
            query = `
                MATCH (c:Chapter {id: $chapterId})
                MATCH (c)-[:HAS_SECTION]->(sec:Section)
                MATCH (sec)-[:HAS_PARAGRAPH]->(p:Paragraph)
                MATCH (p)-[:CONTAINS_FORMULA]->(f:Formula)
                WHERE f.latex CONTAINS '{{symbol:'
                WITH f, c, sec, [x IN split(f.latex, '{{symbol:') WHERE size(x) > 0 AND size(split(x, '}}')) > 0 | split(x, '}}')[0]] as symbolIds
                UNWIND symbolIds as symbolId
                MATCH (s:Symbol {id: symbolId})
                ${searchText ? 'WHERE (toLower(s.latex) CONTAINS toLower($searchText) OR toLower(COALESCE(s.description, "")) CONTAINS toLower($searchText) OR toLower(COALESCE(s.units, "")) CONTAINS toLower($searchText) OR toLower(COALESCE(s.value, "")) CONTAINS toLower($searchText))' : ''}
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
        } else {
            // Без фильтров по главе/секции - показываем все символы
            query = `
                MATCH (s:Symbol)
                ${searchText ? 'WHERE (toLower(s.latex) CONTAINS toLower($searchText) OR toLower(COALESCE(s.description, "")) CONTAINS toLower($searchText) OR toLower(COALESCE(s.units, "")) CONTAINS toLower($searchText) OR toLower(COALESCE(s.value, "")) CONTAINS toLower($searchText))' : ''}
                OPTIONAL MATCH (f:Formula)
                WHERE f.latex CONTAINS ('{{symbol:' + s.id + '}}')
                OPTIONAL MATCH (f)<-[:CONTAINS_FORMULA]-(p:Paragraph)
                OPTIONAL MATCH (p)<-[:HAS_PARAGRAPH]-(sec:Section)
                OPTIONAL MATCH (sec)<-[:HAS_SECTION]-(c:Chapter)
                WITH DISTINCT s, 
                     head(collect(DISTINCT c)) as c, 
                     head(collect(DISTINCT sec)) as sec
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
        }

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
