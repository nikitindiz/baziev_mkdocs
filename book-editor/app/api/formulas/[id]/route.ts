import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/neo4j';
import { Formula, FormulaUpdateRequest } from '@/types/formula';

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const session = getSession();
    const { id } = await params;

    try {
        const query = `
            MATCH (f:Formula {id: $id})
            RETURN f
        `;

        const result = await session.run(query, { id });

        if (result.records.length === 0) {
            return NextResponse.json({ error: 'Formula not found' }, { status: 404 });
        }

        const record = result.records[0];
        const f = record.get('f').properties;

        // Парсим metadata если это строка
        let metadata = f.metadata;
        if (typeof metadata === 'string') {
            try {
                metadata = JSON.parse(metadata);
            } catch (e) {
                // Оставляем как строку если не удалось распарсить
            }
        }

        // Парсим source если это строка
        let source = f.source;
        if (typeof source === 'string') {
            try {
                source = JSON.parse(source);
            } catch (e) {
                // Оставляем как строку если не удалось распарсить
            }
        }

        const formula: Formula = {
            id: f.id,
            latex: f.latex || '',
            type: f.type || 'inline',
            wrapper_html: f.wrapper_html,
            source: source,
            metadata: metadata,
            is_symbol: f.is_symbol || false,
            symbol_type: f.symbol_type,
            symbol_value: f.symbol_value,
            symbol_definition: f.symbol_definition,
            symbol_units: f.symbol_units,
            symbol_parsed: f.symbol_parsed || false,
            symbol_parse_confidence: f.symbol_parse_confidence,
            not_sure_if_this_is_symbol: f.not_sure_if_this_is_symbol || false,
        };

        return NextResponse.json(formula);
    } catch (error) {
        console.error('Error fetching formula:', error);
        return NextResponse.json({ error: 'Failed to fetch formula' }, { status: 500 });
    } finally {
        await session.close();
    }
}

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const session = getSession();
    const { id } = await params;

    try {
        const body: FormulaUpdateRequest = await request.json();

        // Проверяем, что хотя бы одно поле для обновления передано
        const hasUpdates = Object.keys(body).length > 0;
        if (!hasUpdates) {
            return NextResponse.json({ error: 'No fields to update provided' }, { status: 400 });
        }

        // Формируем динамический запрос для обновления только переданных полей
        const setClauses: string[] = [];
        const queryParams: Record<string, any> = { id };

        if (body.latex !== undefined) {
            setClauses.push('f.latex = $latex');
            queryParams.latex = body.latex;
        }

        if (body.type !== undefined) {
            setClauses.push('f.type = $type');
            queryParams.type = body.type;
        }

        if (body.is_symbol !== undefined) {
            setClauses.push('f.is_symbol = $is_symbol');
            queryParams.is_symbol = body.is_symbol;
        }

        if (body.symbol_definition !== undefined) {
            setClauses.push('f.symbol_definition = $symbol_definition');
            queryParams.symbol_definition = body.symbol_definition;
        }

        if (body.symbol_value !== undefined) {
            setClauses.push('f.symbol_value = $symbol_value');
            queryParams.symbol_value = body.symbol_value;
        }

        if (body.symbol_units !== undefined) {
            setClauses.push('f.symbol_units = $symbol_units');
            queryParams.symbol_units = body.symbol_units;
        }

        if (body.symbol_type !== undefined) {
            setClauses.push('f.symbol_type = $symbol_type');
            queryParams.symbol_type = body.symbol_type;
        }

        if (body.symbol_parse_confidence !== undefined) {
            setClauses.push('f.symbol_parse_confidence = $symbol_parse_confidence');
            queryParams.symbol_parse_confidence = body.symbol_parse_confidence;
        }

        if (body.not_sure_if_this_is_symbol !== undefined) {
            setClauses.push('f.not_sure_if_this_is_symbol = $not_sure_if_this_is_symbol');
            queryParams.not_sure_if_this_is_symbol = body.not_sure_if_this_is_symbol;
        }

        // Если изменяется is_symbol на false, сбрасываем связанные поля
        if (body.is_symbol === false) {
            setClauses.push('f.symbol_definition = null');
            setClauses.push('f.symbol_value = null');
            setClauses.push('f.symbol_units = null');
            setClauses.push('f.symbol_type = null');
            setClauses.push('f.symbol_parse_confidence = null');
            setClauses.push('f.symbol_parsed = false');
        }

        const query = `
            MATCH (f:Formula {id: $id})
            SET ${setClauses.join(', ')}
            RETURN f
        `;

        const result = await session.run(query, queryParams);

        if (result.records.length === 0) {
            return NextResponse.json({ error: 'Formula not found' }, { status: 404 });
        }

        const record = result.records[0];
        const f = record.get('f').properties;

        // Парсим metadata если это строка
        let metadata = f.metadata;
        if (typeof metadata === 'string') {
            try {
                metadata = JSON.parse(metadata);
            } catch (e) {
                // Оставляем как строку если не удалось распарсить
            }
        }

        // Парсим source если это строка
        let source = f.source;
        if (typeof source === 'string') {
            try {
                source = JSON.parse(source);
            } catch (e) {
                // Оставляем как строку если не удалось распарсить
            }
        }

        const updatedFormula: Formula = {
            id: f.id,
            latex: f.latex || '',
            type: f.type || 'inline',
            wrapper_html: f.wrapper_html,
            source: source,
            metadata: metadata,
            is_symbol: f.is_symbol || false,
            symbol_type: f.symbol_type,
            symbol_value: f.symbol_value,
            symbol_definition: f.symbol_definition,
            symbol_units: f.symbol_units,
            symbol_parsed: f.symbol_parsed || false,
            symbol_parse_confidence: f.symbol_parse_confidence,
            not_sure_if_this_is_symbol: f.not_sure_if_this_is_symbol || false,
        };

        return NextResponse.json(updatedFormula);
    } catch (error) {
        console.error('Error updating formula:', error);
        return NextResponse.json({ error: 'Failed to update formula' }, { status: 500 });
    } finally {
        await session.close();
    }
}
