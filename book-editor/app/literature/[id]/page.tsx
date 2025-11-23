'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Literature } from '@/types/literature';

export default function LiteraturePage() {
    const params = useParams();
    const router = useRouter();
    const literatureId = decodeURI(params.id as string);

    const [literature, setLiterature] = useState<Literature | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchLiterature() {
            try {
                setLoading(true);
                setError(null);

                console.log('Fetching literature ID:', literatureId);

                const response = await fetch(`/api/literature/${literatureId}`);

                if (!response.ok) {
                    throw new Error(`Failed to fetch literature: ${response.statusText}`);
                }

                const data = await response.json();
                setLiterature(data.data);

            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error occurred');
            } finally {
                setLoading(false);
            }
        }

        if (literatureId) {
            fetchLiterature();
        }
    }, [literatureId]);

    if (loading) {
        return (
            <div className="min-h-screen overflow-hidden flex items-center justify-center">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
                    <p className="text-gray-600 dark:text-gray-400">Загрузка...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen overflow-hidden flex items-center justify-center">
                <div className="text-center max-w-md p-8 bg-red-50 dark:bg-red-900/20 rounded-lg">
                    <h2 className="text-xl font-bold text-red-600 dark:text-red-400 mb-2">Ошибка</h2>
                    <p className="text-gray-700 dark:text-gray-300">{error}</p>
                    <button
                        onClick={() => router.back()}
                        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                        Назад
                    </button>
                </div>
            </div>
        );
    }

    if (!literature) {
        return (
            <div className="min-h-screen overflow-hidden flex items-center justify-center">
                <div className="text-center">
                    <p className="text-gray-600 dark:text-gray-400">Литература не найдена</p>
                    <button
                        onClick={() => router.back()}
                        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                    >
                        Назад
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen overflow-hidden bg-gray-50 dark:bg-gray-900">
            <div className="max-w-4xl mx-auto py-8 px-4">
                {/* Header */}
                <header className="mb-8">
                    <button
                        onClick={() => router.back()}
                        className="mb-4 px-4 py-2 text-blue-600 dark:text-blue-400 hover:underline"
                    >
                        ← Назад
                    </button>

                    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                        {literature.number && (
                            <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                                Источник №{literature.number}
                            </div>
                        )}

                        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                            Цитируемая литература
                        </h1>

                        {literature.author && (
                            <div className="mb-2">
                                <span className="font-semibold text-gray-700 dark:text-gray-300">
                                    Автор:
                                </span>{' '}
                                <span className="text-gray-900 dark:text-gray-100">
                                    {literature.author}
                                </span>
                            </div>
                        )}

                        {literature.title && (
                            <div className="mb-2">
                                <span className="font-semibold text-gray-700 dark:text-gray-300">
                                    Название:
                                </span>{' '}
                                <span className="text-gray-900 dark:text-gray-100">
                                    {literature.title}
                                </span>
                            </div>
                        )}

                        {literature.publication && (
                            <div className="mb-2">
                                <span className="font-semibold text-gray-700 dark:text-gray-300">
                                    Публикация:
                                </span>{' '}
                                <span className="text-gray-900 dark:text-gray-100">
                                    {literature.publication}
                                </span>
                            </div>
                        )}

                        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                            <h2 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">
                                Полный текст:
                            </h2>
                            <div className="text-gray-900 dark:text-gray-100 leading-relaxed whitespace-pre-wrap">
                                {literature.text}
                            </div>
                        </div>

                        {literature.source && (
                            <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                                <span className="font-semibold">Источник данных:</span> {literature.source}
                            </div>
                        )}
                    </div>
                </header>
            </div>
        </div>
    );
}
