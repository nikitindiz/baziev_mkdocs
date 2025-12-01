import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';

export interface SymbolData {
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
        // Находим формулу, её параграф и секцию, затем получаем все Symbol сущности из этой секции
        const query = `
            MATCH (f:Formula {id: $formulaId})
            MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f)
            MATCH (s:Section)-[:HAS_PARAGRAPH]->(p)
            
            // Получаем все параграфы этой секции плюс саму формулу
            MATCH (s)-[:HAS_PARAGRAPH]->(sectionParagraph:Paragraph)
            
            // Извлекаем ID символов из содержимого параграфов и формул
            WITH sectionParagraph, f,
                 [x IN split(sectionParagraph.content, '{{symbol:') WHERE size(x) > 0 AND size(split(x, '}}')) > 0 | 
                  split(x, '}}')[0]
                 ] + 
                 [x IN split(f.latex, '{{symbol:') WHERE size(x) > 0 AND size(split(x, '}}')) > 0 | 
                  split(x, '}}')[0]
                 ] as symbolIds
            
            // Получаем Symbol сущности по найденным ID
            UNWIND CASE WHEN size([sid IN symbolIds WHERE sid IS NOT NULL]) > 0 
                        THEN [sid IN symbolIds WHERE sid IS NOT NULL] 
                        ELSE [null] END as symbolId
            MATCH (sym:Symbol {id: symbolId})
            
            RETURN DISTINCT
                sym.id as id,
                sym.latex as latex,
                sym.description as description,
                sym.units as units,
                sym.value as value
            
            ORDER BY sym.latex
        `;

        const result = await session.run(query, { formulaId: id });

        const symbols: SymbolData[] = result.records.map((record) => ({
            id: record.get('id'),
            latex: record.get('latex') || '',
            description: record.get('description') || undefined,
            units: record.get('units') || undefined,
            value: record.get('value') || undefined,
        }));

        return NextResponse.json({ symbols });
    } catch (error) {
        console.error('Error fetching formula symbols:', error);
        return NextResponse.json(
            {
                error: 'Failed to fetch formula symbols',
                details: error instanceof Error ? error.message : 'Unknown error',
            },
            { status: 500 },
        );
    } finally {
        await session.close();
    }
}
