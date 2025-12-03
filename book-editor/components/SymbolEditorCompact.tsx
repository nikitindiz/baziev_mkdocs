'use client';

import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import dynamic from 'next/dynamic';
import { ConfirmModal } from './ConfirmModal';

const InlineMath = dynamic(() => import('react-katex').then((mod) => mod.InlineMath), {
    ssr: false,
});

interface Symbol {
    id: string;
    latex: string;
    description?: string;
    units?: string;
    value?: string;
    usageCount?: number;
}

interface SymbolEditorCompactProps {
    symbolId: string;
    onClose: () => void;
}

export function SymbolEditorCompact({ symbolId, onClose }: SymbolEditorCompactProps) {
    const queryClient = useQueryClient();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [symbol, setSymbol] = useState<Symbol | null>(null);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [usageCount, setUsageCount] = useState<number>(0);

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

                // Получаем статистику использования
                try {
                    const statsResponse = await fetch(`/api/symbols/${symbolId}/usage`);
                    if (statsResponse.ok) {
                        const stats = await statsResponse.json();
                        setUsageCount(stats.totalUsages || 0);
                    }
                } catch (err) {
                    console.error('Failed to fetch usage stats:', err);
                }

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

    const handleDeleteClick = () => {
        setShowDeleteModal(true);
    };

    const handleDeleteConfirm = async () => {
        if (!symbol) return;

        setShowDeleteModal(false);
        setDeleting(true);
        setError(null);

        try {
            const response = await fetch(`/api/symbols/${symbolId}`, {
                method: 'DELETE',
            });

            const data = await response.json();

            if (!response.ok) {
                if (response.status === 409) {
                    // Symbol is in use
                    const { formulasCount, paragraphsCount, totalUsages } = data.details;
                    throw new Error(
                        `Символ используется в ${totalUsages} местах:\n` +
                        `- Формулы: ${formulasCount}\n` +
                        `- Параграфы: ${paragraphsCount}\n\n` +
                        `Удалите все ссылки на символ перед его удалением.`
                    );
                }
                throw new Error(data.error || 'Failed to delete symbol');
            }

            // Invalidate queries to refetch data
            queryClient.invalidateQueries({ queryKey: ['symbols-list'] });
            queryClient.invalidateQueries({ queryKey: ['paragraph-context'] });

            // Close editor after successful delete
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setDeleting(false);
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
                        disabled={saving || deleting || !latex}
                        className="flex-1 px-3 py-1.5 text-sm bg-blue-600 text-white rounded
                                 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                        {saving ? 'Сохранение...' : 'Сохранить'}
                    </button>
                    <button
                        onClick={onClose}
                        disabled={saving || deleting}
                        className="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded
                                 hover:bg-gray-300 dark:hover:bg-gray-600
                                 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Отмена
                    </button>
                    <button
                        onClick={handleDeleteClick}
                        disabled={saving || deleting || usageCount > 0}
                        className="px-3 py-1.5 text-sm bg-red-600 text-white rounded
                                 hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed
                                 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                        title={usageCount > 0 ? `Символ используется в ${usageCount} местах` : 'Удалить символ'}
                    >
                        {deleting ? (
                            <span className="flex items-center gap-1">
                                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Удаление...
                            </span>
                        ) : (
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        )}
                    </button>
                </div>
            </div>

            {/* Confirm Delete Modal */}
            <ConfirmModal
                isOpen={showDeleteModal}
                title="Удаление символа"
                message={`Вы уверены, что хотите удалить символ "${symbol.latex}"?\n\nЭто действие нельзя отменить.`}
                confirmLabel="Удалить"
                cancelLabel="Отмена"
                onConfirm={handleDeleteConfirm}
                onCancel={() => setShowDeleteModal(false)}
                variant="danger"
            />
        </div>
    );
}
