'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface FormulaEditorProps {
    formulaId: string;
}

export function FormulaEditor({ formulaId }: FormulaEditorProps) {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // TODO: Fetch formula data from API
        setLoading(false);
    }, [formulaId]);

    const handleCancel = () => {
        // Remove selected-formula query parameter
        const url = new URL(window.location.href);
        url.searchParams.delete('selected-formula');
        router.push(url.pathname + url.search);
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mb-2"></div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Загрузка формулы...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4">
                <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                    <h3 className="text-sm font-semibold text-red-600 dark:text-red-400 mb-2">Ошибка</h3>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="border-b border-gray-200 dark:border-gray-700 p-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Редактор формулы
                </h2>
                <p className="text-xs text-gray-500 dark:text-gray-400 font-mono mt-1">
                    {formulaId}
                </p>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {/* Formula Preview */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Предварительный просмотр
                    </label>
                    <div className="bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg p-4 text-center">
                        <div className="text-gray-400 dark:text-gray-500 text-sm">
                            Формула будет отображаться здесь
                        </div>
                    </div>
                </div>

                {/* LaTeX Input */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        LaTeX
                    </label>
                    <textarea
                        className="w-full h-24 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-mono text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Введите LaTeX код..."
                        disabled
                    />
                </div>

                {/* Formula Type */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Тип формулы
                    </label>
                    <div className="flex gap-4">
                        <label className="flex items-center">
                            <input
                                type="radio"
                                name="formulaType"
                                value="inline"
                                className="mr-2"
                                disabled
                            />
                            <span className="text-sm text-gray-700 dark:text-gray-300">Встроенная</span>
                        </label>
                        <label className="flex items-center">
                            <input
                                type="radio"
                                name="formulaType"
                                value="display"
                                className="mr-2"
                                disabled
                            />
                            <span className="text-sm text-gray-700 dark:text-gray-300">Отдельная</span>
                        </label>
                    </div>
                </div>

                {/* Symbol Information */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Информация о символе
                    </label>
                    <div className="space-y-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3">
                        <div className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                id="isSymbol"
                                className="rounded"
                                disabled
                            />
                            <label htmlFor="isSymbol" className="text-sm text-gray-700 dark:text-gray-300">
                                Это символ
                            </label>
                        </div>

                        <div className="space-y-1">
                            <label className="block text-xs text-gray-600 dark:text-gray-400">
                                Определение символа
                            </label>
                            <input
                                type="text"
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100"
                                placeholder="Например: скорость света"
                                disabled
                            />
                        </div>

                        <div className="space-y-1">
                            <label className="block text-xs text-gray-600 dark:text-gray-400">
                                Уверенность распознавания
                            </label>
                            <select
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100"
                                disabled
                            >
                                <option value="">Не определено</option>
                                <option value="high">Высокая</option>
                                <option value="medium">Средняя</option>
                                <option value="low">Низкая</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Related Information */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Связанные элементы
                    </label>
                    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3">
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                            Связи с другими формулами, символами и сущностями будут отображаться здесь
                        </p>
                    </div>
                </div>
            </div>

            {/* Footer Actions */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-4 flex gap-2">
                <button
                    className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled
                >
                    Сохранить
                </button>
                <button
                    className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg font-medium text-sm transition-colors"
                    onClick={handleCancel}
                >
                    Отмена
                </button>
            </div>
        </div>
    );
}
