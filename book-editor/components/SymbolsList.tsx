'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { SymbolsListResponse, SymbolsListFilters } from '@/types/symbol-list';
import { BlockMath } from 'react-katex';
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
    const [searchText, setSearchText] = useState('');
    const [filterBySection, setFilterBySection] = useState(false);
    const [filterByChapter, setFilterByChapter] = useState(false);
    const [sortBy, setSortBy] = useState<'latex' | 'created'>('latex');

    // Определяем фильтры для запроса
    const filters: SymbolsListFilters = useMemo(() => ({
        search: searchText,
        chapterId: filterByChapter ? currentChapterId : undefined,
        sectionId: filterBySection ? currentSectionId : undefined,
        sortBy,
    }), [searchText, filterByChapter, filterBySection, sortBy, currentChapterId, currentSectionId]);

    const { data, isLoading, error } = useQuery({
        queryKey: ['symbols-list', filters],
        queryFn: () => fetchSymbolsList(filters),
    });

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSearchText(e.target.value);
    };

    const toggleFilterBySection = () => {
        if (!filterBySection && filterByChapter) {
            // Если включаем фильтр по секции, то отключаем фильтр по главе
            setFilterByChapter(false);
        }
        setFilterBySection(!filterBySection);
    };

    const toggleFilterByChapter = () => {
        if (!filterByChapter && filterBySection) {
            // Если включаем фильтр по главе, то отключаем фильтр по секции
            setFilterBySection(false);
        }
        setFilterByChapter(!filterByChapter);
    };

    const symbols = data?.symbols || [];

    return (
        <div className="flex flex-col h-full">
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
                        onChange={(e) => setSortBy(e.target.value as 'latex' | 'created')}
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
                        {symbols.map((symbol) => (
                            <div
                                key={symbol.id}
                                className="p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 
                           rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                            >
                                {/* LaTeX формула */}
                                <div className="mb-2 text-center bg-gray-50 dark:bg-gray-900 p-2 rounded">
                                    <BlockMath math={symbol.latex} />
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

                                {/* Контекст (глава/секция) */}
                                {(symbol.chapterTitle || symbol.sectionTitle) && (
                                    <div className="text-xs text-gray-500 dark:text-gray-500 mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
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
                        ))}
                    </div>
                )}
            </div>

            {/* Статистика */}
            {!isLoading && !error && (
                <div className="p-3 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400 text-center">
                    Найдено символов: {symbols.length}
                </div>
            )}
        </div>
    );
}
