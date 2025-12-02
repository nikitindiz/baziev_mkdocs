'use client';

import { useState, useMemo, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { SymbolsListResponse, SymbolsListFilters } from '@/types/symbol-list';
import { BlockMath } from 'react-katex';
import { SymbolEditorCompact } from './SymbolEditorCompact';
import 'katex/dist/katex.min.css';

interface SymbolsListProps {
    currentChapterId?: string;
    currentSectionId?: string;
}

async function fetchSymbolsList(filters: SymbolsListFilters): Promise<SymbolsListResponse> {
    const params = new URLSearchParams();

    if (filters.search) params.append('search', filters.search);
    if (filters.chapterId) params.append('chapterId', filters.chapterId);
    if (filters.sectionId) params.append('sectionId', filters.sectionId);
    if (filters.sortBy) params.append('sortBy', filters.sortBy);

    const response = await fetch(`/api/symbols/list?${params.toString()}`);

    if (!response.ok) {
        throw new Error(`Failed to fetch symbols: ${response.statusText}`);
    }

    return response.json();
}

export function SymbolsList({ currentChapterId, currentSectionId }: SymbolsListProps) {
    const router = useRouter();
    const searchParams = useSearchParams();
    const selectedSymbolId = searchParams.get('selected-symbol');

    const [searchText, setSearchText] = useState('');
    const [editingSymbolId, setEditingSymbolId] = useState<string | null>(null);
    const [filterBySection, setFilterBySection] = useState(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('symbolsList.filterBySection') === 'true';
        }
        return false;
    });
    const [filterByChapter, setFilterByChapter] = useState(() => {
        if (typeof window !== 'undefined') {
            return localStorage.getItem('symbolsList.filterByChapter') === 'true';
        }
        return false;
    });
    const [sortBy, setSortBy] = useState<'latex' | 'created'>(() => {
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem('symbolsList.sortBy');
            return (saved === 'created' ? 'created' : 'latex') as 'latex' | 'created';
        }
        return 'latex';
    });

    // Определяем фильтры для запроса
    const filters: SymbolsListFilters = useMemo(
        () => ({
            search: searchText,
            chapterId: filterByChapter ? currentChapterId : undefined,
            sectionId: filterBySection ? currentSectionId : undefined,
            sortBy,
        }),
        [searchText, filterByChapter, filterBySection, sortBy, currentChapterId, currentSectionId],
    );

    const { data, isLoading, error } = useQuery({
        queryKey: ['symbols-list', filters],
        queryFn: () => fetchSymbolsList(filters),
    });

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchText(e.target.value);
    };

    const toggleFilterBySection = () => {
        const newValue = !filterBySection;
        if (newValue && filterByChapter) {
            // Если включаем фильтр по секции, то отключаем фильтр по главе
            setFilterByChapter(false);
            localStorage.setItem('symbolsList.filterByChapter', 'false');
        }
        setFilterBySection(newValue);
        localStorage.setItem('symbolsList.filterBySection', String(newValue));
    };

    const toggleFilterByChapter = () => {
        const newValue = !filterByChapter;
        if (newValue && filterBySection) {
            // Если включаем фильтр по главе, то отключаем фильтр по секции
            setFilterBySection(false);
            localStorage.setItem('symbolsList.filterBySection', 'false');
        }
        setFilterByChapter(newValue);
        localStorage.setItem('symbolsList.filterByChapter', String(newValue));
    };

    const symbols = data?.symbols || [];

    const handleSymbolClick = (symbolId: string) => {
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.set('selected-symbol', symbolId);
        router.push(newUrl.pathname + newUrl.search, { scroll: false });
    };

    const handleSymbolDoubleClick = (symbolId: string) => {
        setEditingSymbolId(symbolId);
    };

    const handleCloseEditor = () => {
        setEditingSymbolId(null);
    };

    // Scroll to selected symbol when it's selected
    useEffect(() => {
        if (!selectedSymbolId || symbols.length === 0) return;

        setTimeout(() => {
            const element = document.getElementById(`symbol-${selectedSymbolId}`);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }, 100);
    }, [selectedSymbolId, symbols]);

    return (
        <div className="flex flex-col h-full">
            {/* Compact Editor */}
            {editingSymbolId && (
                <SymbolEditorCompact symbolId={editingSymbolId} onClose={handleCloseEditor} />
            )}

            {/* Заголовок */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
                    Символы
                </h2>

                {/* Поиск */}
                <input
                    type="text"
                    placeholder="Поиск символов..."
                    value={searchText}
                    onChange={handleSearchChange}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     placeholder-gray-400 dark:placeholder-gray-500
                     focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                />

                {/* Фильтры */}
                <div className="mt-3 space-y-2">
                    <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={filterBySection}
                            onChange={toggleFilterBySection}
                            disabled={!currentSectionId}
                            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded 
                         focus:ring-blue-500 dark:focus:ring-blue-600 
                         dark:bg-gray-700 dark:border-gray-600
                         disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                            Только текущая секция
                        </span>
                    </label>

                    <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={filterByChapter}
                            onChange={toggleFilterByChapter}
                            disabled={!currentChapterId}
                            className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded 
                         focus:ring-blue-500 dark:focus:ring-blue-600 
                         dark:bg-gray-700 dark:border-gray-600
                         disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                            Только текущая глава
                        </span>
                    </label>
                </div>

                {/* Сортировка */}
                <div className="mt-3">
                    <label className="text-sm text-gray-700 dark:text-gray-300 mb-1 block">
                        Сортировка:
                    </label>
                    <select
                        value={sortBy}
                        onChange={(e) => {
                            const newValue = e.target.value as 'latex' | 'created';
                            setSortBy(newValue);
                            localStorage.setItem('symbolsList.sortBy', newValue);
                        }}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md 
                       bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                       focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
                    >
                        <option value="latex">По алфавиту (LaTeX)</option>
                        <option value="created">По дате создания</option>
                    </select>
                </div>
            </div>

            {/* Список символов */}
            <div className="flex-1 overflow-y-auto p-4">
                {isLoading && (
                    <div className="flex justify-center items-center h-32">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    </div>
                )}

                {error && (
                    <div className="text-red-600 dark:text-red-400 text-sm text-center">
                        Ошибка загрузки символов
                    </div>
                )}

                {!isLoading && !error && symbols.length === 0 && (
                    <div className="text-gray-500 dark:text-gray-400 text-sm text-center">
                        Символы не найдены
                    </div>
                )}

                {!isLoading && !error && symbols.length > 0 && (
                    <div className="space-y-3">
                        {symbols.map((symbol) => {
                            const isSelected = symbol.id === selectedSymbolId;
                            return (
                                <div
                                    key={symbol.id}
                                    id={`symbol-${symbol.id}`}
                                    onClick={() => handleSymbolClick(symbol.id)}
                                    onDoubleClick={() => handleSymbolDoubleClick(symbol.id)}
                                    className={`p-3 border rounded-lg hover:shadow-md transition-all cursor-pointer ${isSelected
                                        ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-500 dark:border-blue-400 ring-2 ring-blue-500 dark:ring-blue-400'
                                        : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                                        }`}
                                    title="Двойной клик для редактирования"
                                >
                                    {/* LaTeX формула с кнопкой редактирования */}
                                    <div className="mb-2 relative">
                                        <div className="text-center bg-gray-50 dark:bg-gray-900 p-2 rounded">
                                            <BlockMath math={symbol.latex} />
                                        </div>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleSymbolDoubleClick(symbol.id);
                                            }}
                                            className="absolute top-1 right-1 p-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                                            title="Редактировать"
                                        >
                                            <svg
                                                className="w-4 h-4 text-gray-600 dark:text-gray-400"
                                                fill="none"
                                                stroke="currentColor"
                                                viewBox="0 0 24 24"
                                            >
                                                <path
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                    strokeWidth={2}
                                                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                                                />
                                            </svg>
                                        </button>
                                    </div>

                                    {/* Описание */}
                                    {symbol.description && (
                                        <div className="text-sm text-gray-700 dark:text-gray-300 mb-1">
                                            <span className="font-semibold">Описание:</span> {symbol.description}
                                        </div>
                                    )}

                                    {/* Единицы измерения */}
                                    {symbol.units && (
                                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                                            <span className="font-semibold">Единицы:</span> {symbol.units}
                                        </div>
                                    )}

                                    {/* Значение */}
                                    {symbol.value && (
                                        <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                                            <span className="font-semibold">Значение:</span> {symbol.value}
                                        </div>
                                    )}

                                    {/* ID символа и статистика */}
                                    <div className="text-xs text-gray-500 dark:text-gray-500 mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 space-y-1">
                                        <div className="flex items-center gap-1">
                                            <span className="font-semibold">ID:</span>
                                            <code className="px-1 py-0.5 bg-gray-100 dark:bg-gray-900 rounded font-mono text-[10px]">
                                                {symbol.id}
                                            </code>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    navigator.clipboard.writeText(symbol.id);
                                                }}
                                                className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
                                                title="Копировать ID"
                                            >
                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                                </svg>
                                            </button>
                                        </div>
                                        {symbol.usageCount !== undefined && (
                                            <div className="flex items-center gap-1">
                                                <span className="font-semibold">Использований:</span>
                                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${symbol.usageCount === 0
                                                        ? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                                                        : symbol.usageCount < 5
                                                            ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                                                            : symbol.usageCount < 10
                                                                ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                                                                : 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                                                    }`}>
                                                    {symbol.usageCount}
                                                </span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Контекст (глава/секция) */}
                                    {(symbol.chapterTitle || symbol.sectionTitle) && (
                                        <div className="text-xs text-gray-500 dark:text-gray-500 mt-1 pt-1 border-t border-gray-200 dark:border-gray-700">
                                            {symbol.chapterTitle && (
                                                <div className="truncate" title={symbol.chapterTitle}>
                                                    📖 {symbol.chapterTitle}
                                                </div>
                                            )}
                                            {symbol.sectionTitle && (
                                                <div className="truncate" title={symbol.sectionTitle}>
                                                    § {symbol.sectionTitle}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Статистика */}
            {!isLoading && !error && symbols.length > 0 && (
                <div className="p-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
                    <div className="flex justify-between items-center">
                        <span>Найдено символов: {symbols.length}</span>
                        <span>
                            Всего использований: {symbols.reduce((sum, s) => sum + (s.usageCount || 0), 0)}
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
