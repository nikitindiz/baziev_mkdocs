'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import dynamic from 'next/dynamic';
import { ConfirmModal } from './ConfirmModal';

const BlockMath = dynamic(() => import('react-katex').then((mod) => mod.BlockMath), { ssr: false });

interface Symbol {
    id: string;
    latex: string;
    description?: string;
    units?: string;
    value?: string;
    usageCount?: number;
}

interface SymbolEditorProps {
    symbolId: string;
}

export function SymbolEditor({ symbolId }: SymbolEditorProps) {
    const router = useRouter();
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

            // Show success feedback
            alert('Символ успешно сохранён');
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

            // Close symbol editor by removing query parameter
            const url = new URL(window.location.href);
            url.searchParams.delete('selected-symbol');
            router.replace(url.pathname + url.search);

            alert('Символ успешно удалён');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setDeleting(false);
        }
    };

    const handleClose = () => {
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.delete('selected-symbol');
        router.push(newUrl.pathname + newUrl.search, { scroll: false });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-2"></div>
                    <p className="text-gray-600 dark:text-gray-400 text-sm">Загрузка...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full p-4">
                <div className="text-center max-w-md">
                    <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
                    <button
                        onClick={handleClose}
                        className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
                    >
                        Закрыть
                    </button>
                </div>
            </div>
        );
    }

    if (!symbol) {
        return null;
    }

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Редактор символа
                </h2>
                <button
                    onClick={handleClose}
                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    aria-label="Закрыть"
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                        />
                    </svg>
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Preview */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Предварительный просмотр
                    </label>
                    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 text-center">
                        {latex ? (
                            <BlockMath math={latex} />
                        ) : (
                            <span className="text-gray-400 dark:text-gray-600">LaTeX не задан</span>
                        )}
                    </div>
                </div>

                {/* LaTeX */}
                <div>
                    <label
                        htmlFor="latex"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                    >
                        LaTeX <span className="text-red-500">*</span>
                    </label>
                    <textarea
                        id="latex"
                        value={latex}
                        onChange={(e) => setLatex(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                                 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400
                                 font-mono text-sm"
                        rows={3}
                        placeholder="E = mc^2"
                        required
                    />
                </div>

                {/* Description */}
                <div>
                    <label
                        htmlFor="description"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                    >
                        Описание
                    </label>
                    <textarea
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                                 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                        rows={3}
                        placeholder="Энергия"
                    />
                </div>

                {/* Units */}
                <div>
                    <label
                        htmlFor="units"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                    >
                        Единицы измерения
                    </label>
                    <input
                        type="text"
                        id="units"
                        value={units}
                        onChange={(e) => setUnits(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                                 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                        placeholder="Дж (джоули)"
                    />
                </div>

                {/* Value */}
                <div>
                    <label
                        htmlFor="value"
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                    >
                        Значение
                    </label>
                    <input
                        type="text"
                        id="value"
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                                 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                                 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                        placeholder="9.11 × 10^-31 кг"
                    />
                </div>

                {/* Symbol ID */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        ID символа
                    </label>
                    <input
                        type="text"
                        value={symbol.id}
                        disabled
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md
                                 bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-400
                                 font-mono text-sm"
                    />
                </div>
            </div>

            {/* Footer with actions */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex gap-2">
                <button
                    onClick={handleSave}
                    disabled={saving || deleting || !latex}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700
                             disabled:bg-gray-400 disabled:cursor-not-allowed
                             focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                    {saving ? 'Сохранение...' : 'Сохранить'}
                </button>
                <button
                    onClick={handleClose}
                    disabled={saving || deleting}
                    className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-md
                             hover:bg-gray-300 dark:hover:bg-gray-600
                             disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Отмена
                </button>
                <button
                    onClick={handleDeleteClick}
                    disabled={saving || deleting || usageCount > 0}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700
                             disabled:bg-gray-400 disabled:cursor-not-allowed
                             focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
                             flex items-center gap-2"
                    title={usageCount > 0 ? `Символ используется в ${usageCount} местах` : 'Удалить символ'}
                >
                    {deleting ? (
                        <>
                            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Удаление...
                        </>
                    ) : (
                        <>
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Удалить
                        </>
                    )}
                </button>
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
