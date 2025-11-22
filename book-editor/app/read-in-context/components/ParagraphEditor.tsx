'use client';

import { useState, useEffect } from 'react';
import { useParagraph } from '@/hooks/useParagraphs';
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface ParagraphEditorProps {
    paragraphId: string;
}

async function updateParagraph(id: string, data: { content?: string; display_name?: string; order?: number; verified?: boolean }) {
    const response = await fetch(`/api/paragraphs/${id}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error('Failed to update paragraph');
    }

    return response.json();
}

export const ParagraphEditor = ({ paragraphId }: ParagraphEditorProps) => {
    const { data: paragraph, isLoading, error } = useParagraph(paragraphId);
    const [content, setContent] = useState('');
    const [displayName, setDisplayName] = useState('');
    const [order, setOrder] = useState<number | undefined>();
    const [verified, setVerified] = useState(false);
    const [isDirty, setIsDirty] = useState(false);

    const queryClient = useQueryClient();

    const updateMutation = useMutation({
        mutationFn: (data: { content?: string; display_name?: string; order?: number; verified?: boolean }) =>
            updateParagraph(paragraphId, data),
        onSuccess: () => {
            // Инвалидируем кеш для обновления данных
            queryClient.invalidateQueries({ queryKey: ['paragraph', paragraphId] });
            queryClient.invalidateQueries({ queryKey: ['paragraphs'] });
            setIsDirty(false);
        },
    });

    // Синхронизируем локальное состояние с данными из API
    useEffect(() => {
        if (paragraph) {
            setContent(paragraph.text || '');
            setDisplayName(paragraph.order ? `Параграф ${paragraph.order}` : '');
            setOrder(paragraph.order);
            setVerified(paragraph.verified || false);
            setIsDirty(false);
        }
    }, [paragraph]);

    // Отслеживаем изменения
    useEffect(() => {
        if (paragraph) {
            const hasContentChanged = content !== (paragraph.text || '');
            const hasOrderChanged = order !== paragraph.order;
            const hasVerifiedChanged = verified !== (paragraph.verified || false);
            setIsDirty(hasContentChanged || hasOrderChanged || hasVerifiedChanged);
        }
    }, [content, order, verified, paragraph]);

    const handleSave = () => {
        if (!isDirty || updateMutation.isPending) return;

        const updates: { content?: string; display_name?: string; order?: number; verified?: boolean } = {};

        if (content !== paragraph?.text) {
            updates.content = content;
        }

        if (order !== paragraph?.order) {
            updates.order = order;
            updates.display_name = order ? `Параграф ${order}` : displayName;
        }

        if (verified !== (paragraph?.verified || false)) {
            updates.verified = verified;
        }

        updateMutation.mutate(updates);
    };

    const handleReset = () => {
        if (paragraph) {
            setContent(paragraph.text || '');
            setOrder(paragraph.order);
            setVerified(paragraph.verified || false);
            setIsDirty(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-gray-500 dark:text-gray-400">Загрузка параграфа...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-red-500">Ошибка загрузки параграфа</div>
            </div>
        );
    }

    if (!paragraph) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="text-gray-500 dark:text-gray-400">Параграф не найден</div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-white dark:bg-gray-900">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-4">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        Редактирование параграфа
                    </h2>
                    {isDirty && (
                        <span className="text-xs px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 rounded">
                            Несохранённые изменения
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleReset}
                        disabled={!isDirty || updateMutation.isPending}
                        className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Отменить
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={!isDirty || updateMutation.isPending}
                        className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {updateMutation.isPending ? 'Сохранение...' : 'Сохранить'}
                    </button>
                </div>
            </div>

            {/* Metadata */}
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <label className="block text-gray-600 dark:text-gray-400 mb-1">ID</label>
                        <div className="font-mono text-xs text-gray-500 dark:text-gray-500 break-all">
                            {paragraph.id}
                        </div>
                    </div>
                    <div>
                        <label htmlFor="order-input" className="block text-gray-600 dark:text-gray-400 mb-1">
                            Порядковый номер
                        </label>
                        <input
                            id="order-input"
                            type="number"
                            value={order || ''}
                            onChange={(e) => setOrder(e.target.value ? parseInt(e.target.value) : undefined)}
                            className="w-full px-3 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
                        />
                    </div>
                </div>
                <div className="mt-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            id="verified-checkbox"
                            type="checkbox"
                            checked={verified}
                            onChange={(e) => setVerified(e.target.checked)}
                            className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-300">Проверен</span>
                    </label>
                </div>
            </div>

            {/* Editor */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
                <label htmlFor="content-textarea" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Содержимое параграфа
                </label>
                <textarea
                    id="content-textarea"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    className="w-full h-full min-h-[400px] px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    placeholder="Введите текст параграфа..."
                />
            </div>

            {/* Footer with stats */}
            <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <div>
                        Слов: {content.trim().split(/\s+/).filter(word => word.length > 0).length}
                    </div>
                    <div>
                        Символов: {content.length}
                    </div>
                </div>
            </div>

            {/* Error message */}
            {updateMutation.isError && (
                <div className="px-6 py-3 bg-red-50 dark:bg-red-900/20 border-t border-red-200 dark:border-red-800">
                    <div className="text-sm text-red-600 dark:text-red-400">
                        Ошибка сохранения: {updateMutation.error?.message || 'Неизвестная ошибка'}
                    </div>
                </div>
            )}
        </div>
    );
};
