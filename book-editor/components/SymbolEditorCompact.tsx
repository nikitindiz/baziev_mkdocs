'use client';

import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import dynamic from 'next/dynamic';

const InlineMath = dynamic(() => import('react-katex').then((mod) => mod.InlineMath), {
    ssr: false,
});

interface Symbol {
    id: string;
    latex: string;
    description?: string;
    units?: string;
    value?: string;
}

interface SymbolEditorCompactProps {
    symbolId: string;
    onClose: () => void;
}

export function SymbolEditorCompact({ symbolId, onClose }: SymbolEditorCompactProps) {
    const queryClient = useQueryClient();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [symbol, setSymbol] = useState<Symbol | null>(null);

    // Form state
    const [latex, setLatex] = useState('');
    const [description, setDescription] = useState('');
    const [units, setUnits] = useState('');
    const [value, setValue] = useState('');

    useEffect(() => {
        async function fetchSymbol() {
            try {
                const response = await fetch(`/api/symbols/${symbolId}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch symbol');
                }
                const data: Symbol = await response.json();
                setSymbol(data);

                // Инициализируем форму данными
                setLatex(data.latex);
                setDescription(data.description || '');
                setUnits(data.units || '');
                setValue(data.value || '');

                setLoading(false);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
                setLoading(false);
            }
        }

        fetchSymbol();
    }, [symbolId]);

    const handleSave = async () => {
        if (!symbol) return;

        setSaving(true);
        setError(null);

        try {
            const response = await fetch(`/api/symbols/${symbolId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    latex,
                    description: description || undefined,
                    units: units || undefined,
                    value: value || undefined,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to save symbol');
            }

            const updatedSymbol: Symbol = await response.json();
            setSymbol(updatedSymbol);

            // Invalidate queries to refetch data
            queryClient.invalidateQueries({ queryKey: ['symbols-list'] });
            queryClient.invalidateQueries({ queryKey: ['paragraph-context'] });

            // Close editor after successful save
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex justify-center items-center h-20">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-red-50 dark:bg-red-900/20">
                <p className="text-red-600 dark:text-red-400 text-sm mb-2">{error}</p>
                <button
                    onClick={onClose}
                    className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                >
                    Закрыть
                </button>
            </div>
        );
    }

    if (!symbol) {
        return null;
    }

    return (
        <div className="border-b border-gray-200 dark:border-gray-700 bg-blue-50 dark:bg-blue-900/20">
            {/* Header */}
            <div className="p-3 flex justify-between items-center border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                    <span>Редактирование:</span>
                    <span className="px-2 py-0.5 bg-white dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600">
                        <InlineMath math={symbol.latex} />
                    </span>
                </h3>
                <button
                    onClick={onClose}
                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    aria-label="Закрыть"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                        />
                    </svg>
                </button>
            </div>

            {/* Form */}
            <div className="p-3 space-y-3">
                {/* LaTeX */}
                <div>
                    <label htmlFor="latex-edit" className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        LaTeX <span className="text-red-500">*</span>
                    </label>
                    <textarea
                        id="latex-edit"
                        value={latex}
                        onChange={(e) => setLatex(e.target.value)}
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded
                                 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400
                                 font-mono"
                        rows={2}
                        placeholder="E = mc^2"
                        required
                    />
                </div>

                {/* Description */}
                <div>
                    <label htmlFor="description-edit" className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Описание
                    </label>
                    <textarea
                        id="description-edit"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded
                                 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                        rows={2}
                        placeholder="Энергия"
                    />
                </div>

                {/* Units */}
                <div>
                    <label htmlFor="units-edit" className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Единицы измерения
                    </label>
                    <input
                        type="text"
                        id="units-edit"
                        value={units}
                        onChange={(e) => setUnits(e.target.value)}
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded
                                 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                        placeholder="Дж (джоули)"
                    />
                </div>

                {/* Value */}
                <div>
                    <label htmlFor="value-edit" className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Значение
                    </label>
                    <input
                        type="text"
                        id="value-edit"
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded
                                 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                        placeholder="9.11 × 10^-31 кг"
                    />
                </div>

                {/* Symbol ID */}
                <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        ID символа
                    </label>
                    <div className="flex items-center gap-2">
                        <input
                            type="text"
                            value={symbol.id}
                            readOnly
                            className="flex-1 px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded
                                     bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-400
                                     font-mono cursor-text select-all"
                        />
                        <button
                            onClick={() => navigator.clipboard.writeText(symbol.id)}
                            className="p-1.5 bg-gray-200 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
                            title="Копировать ID"
                            type="button"
                        >
                            <svg className="w-4 h-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                    <button
                        onClick={handleSave}
                        disabled={saving || !latex}
                        className="flex-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded
                                 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        {saving ? 'Сохранение...' : 'Сохранить'}
                    </button>
                    <button
                        onClick={onClose}
                        disabled={saving}
                        className="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded
                                 hover:bg-gray-300 dark:hover:bg-gray-600
                                 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Отмена
                    </button>
                </div>
            </div>
        </div>
    );
}
