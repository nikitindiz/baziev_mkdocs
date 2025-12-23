'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';

const InlineMath = dynamic(() => import('react-katex').then((mod) => mod.InlineMath), { ssr: false });

interface SymbolData {
    id: string;
    latex: string;
    description?: string;
    units?: string;
    value?: string;
}

interface SymbolPickerModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (symbol: string) => void;
    formulaId: string;
    onSymbolCreated?: () => void;
}

type Tab = 'available' | 'new';

export function SymbolPickerModal({ isOpen, onClose, onSelect, formulaId, onSymbolCreated }: SymbolPickerModalProps) {
    const searchInputRef = useRef<HTMLInputElement>(null);
    const [activeTab, setActiveTab] = useState<Tab>('available');
    const [symbols, setSymbols] = useState<SymbolData[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchAllSections, setSearchAllSections] = useState(false);

    // Form state for new symbol
    const [newLatex, setNewLatex] = useState('');
    const [newDescription, setNewDescription] = useState('');
    const [newUnits, setNewUnits] = useState('');
    const [newValue, setNewValue] = useState('');
    const [creating, setCreating] = useState(false);

    // Загружаем символы при открытии модального окна или при изменении режима поиска
    useEffect(() => {
        if (isOpen) {
            setLoading(true);
            setError(null);

            const endpoint = searchAllSections
                ? '/api/symbols/all'
                : `/api/formulas/${formulaId}/symbols`;

            fetch(endpoint)
                .then((res) => {
                    if (!res.ok) {
                        throw new Error('Failed to fetch symbols');
                    }
                    return res.json();
                })
                .then((data) => {
                    setSymbols(data.symbols || []);
                })
                .catch((err) => {
                    setError(err.message);
                })
                .finally(() => {
                    setLoading(false);
                });
        }
    }, [isOpen, formulaId, searchAllSections]);

    useEffect(() => {
        if (isOpen && activeTab === 'available' && searchInputRef.current) {
            searchInputRef.current.focus();
        }
    }, [isOpen, activeTab]);

    useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, onClose]);

    // Фильтруем символы по поисковому запросу
    const filteredSymbols = symbols.filter((symbol) => {
        if (!searchQuery) return true;

        const query = searchQuery.toLowerCase();
        return (
            symbol.latex.toLowerCase().includes(query) ||
            symbol.description?.toLowerCase().includes(query) ||
            `${symbol.value}`.toLowerCase().includes(query) ||
            `${symbol.units}`.toLowerCase().includes(query)
        );
    });

    const handleSymbolClick = (symbol: SymbolData) => {
        onSelect(`{{symbol:${symbol.id}}}`);
    };

    const handleCreateSymbol = async () => {
        if (!newLatex.trim()) {
            setError('LaTeX код обязателен');
            return;
        }

        setCreating(true);
        setError(null);

        try {
            const response = await fetch('/api/symbols', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    latex: newLatex.trim(),
                    description: newDescription.trim() || undefined,
                    units: newUnits.trim() || undefined,
                    value: newValue.trim() || undefined,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to create symbol');
            }

            const newSymbol: SymbolData = await response.json();

            // Добавляем новый символ в список
            setSymbols([...symbols, newSymbol]);

            // Вызываем колбэк для обновления символов в родительском компоненте
            onSymbolCreated?.();

            // Вставляем символ в формулу
            onSelect(`{{symbol:${newSymbol.id}}}`);

            // Очищаем форму
            setNewLatex('');
            setNewDescription('');
            setNewUnits('');
            setNewValue('');

            // Переключаемся на таб с доступными символами
            setActiveTab('available');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setCreating(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl mx-4 flex flex-col max-h-[80vh]">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        Выбор символа
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-gray-200 dark:border-gray-700">
                    <button
                        onClick={() => setActiveTab('available')}
                        className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'available'
                            ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                            }`}
                    >
                        Доступные символы
                    </button>
                    <button
                        onClick={() => setActiveTab('new')}
                        className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${activeTab === 'new'
                            ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                            }`}
                    >
                        Новый символ
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden p-4">
                    {activeTab === 'available' && (
                        <div className="h-full flex flex-col space-y-4">
                            {/* Search Controls */}
                            <div className="space-y-2">
                                <input
                                    ref={searchInputRef}
                                    type="text"
                                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    placeholder="Поиск по символам..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                />
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        className="rounded"
                                        checked={searchAllSections}
                                        onChange={(e) => setSearchAllSections(e.target.checked)}
                                    />
                                    <span className="text-sm text-gray-700 dark:text-gray-300">
                                        Искать по всем секциям
                                    </span>
                                </label>
                            </div>

                            {/* Symbols List */}
                            <div className="flex-1 overflow-y-auto">
                                {loading && (
                                    <div className="flex items-center justify-center h-32">
                                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                                    </div>
                                )}

                                {error && (
                                    <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
                                        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                                    </div>
                                )}

                                {!loading && !error && filteredSymbols.length === 0 && (
                                    <div className="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">
                                        {searchQuery ? 'Символы не найдены' : 'Нет доступных символов в текущей секции'}
                                    </div>
                                )}

                                {!loading && !error && filteredSymbols.length > 0 && (
                                    <div className="space-y-2">
                                        {filteredSymbols.map((symbol) => (
                                            <button
                                                key={symbol.id}
                                                onClick={() => handleSymbolClick(symbol)}
                                                className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                                            >
                                                <div className="flex items-start gap-3">
                                                    <div className="shrink-0 w-16 h-10 flex items-center justify-center bg-gray-50 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
                                                        <InlineMath math={symbol.latex} />
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        {symbol.description && (
                                                            <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                                                {symbol.description}
                                                            </div>
                                                        )}
                                                        <div className="flex items-center gap-2 mt-1">
                                                            {symbol.value && (
                                                                <span className="text-xs text-gray-600 dark:text-gray-400">
                                                                    {symbol.value}
                                                                </span>
                                                            )}
                                                            {symbol.units && (
                                                                <span className="text-xs text-gray-500 dark:text-gray-500">
                                                                    {symbol.units}
                                                                </span>
                                                            )}
                                                        </div>
                                                        <div className="text-xs text-gray-400 dark:text-gray-500 font-mono mt-1">
                                                            {symbol.latex}
                                                        </div>
                                                    </div>
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === 'new' && (
                        <div className="h-full flex flex-col space-y-4">
                            <div className="space-y-4">
                                {/* LaTeX Input */}
                                <div className="space-y-1">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                        LaTeX код <span className="text-red-500">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        placeholder="Например: c или \alpha"
                                        value={newLatex}
                                        onChange={(e) => setNewLatex(e.target.value)}
                                    />
                                </div>

                                {/* Description Input */}
                                <div className="space-y-1">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                        Описание
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        placeholder="Например: скорость света"
                                        value={newDescription}
                                        onChange={(e) => setNewDescription(e.target.value)}
                                    />
                                </div>

                                {/* Value Input */}
                                <div className="space-y-1">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                        Значение
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        placeholder="Например: 299792458"
                                        value={newValue}
                                        onChange={(e) => setNewValue(e.target.value)}
                                    />
                                </div>

                                {/* Units Input */}
                                <div className="space-y-1">
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                        Единицы измерения
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        placeholder="Например: м/с"
                                        value={newUnits}
                                        onChange={(e) => setNewUnits(e.target.value)}
                                    />
                                </div>

                                {/* Preview */}
                                {newLatex && (
                                    <div className="space-y-1">
                                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Предварительный просмотр
                                        </label>
                                        <div className="p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
                                            <InlineMath math={newLatex} />
                                        </div>
                                    </div>
                                )}

                                {/* Error Message */}
                                {error && (
                                    <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
                                        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                                    </div>
                                )}

                                {/* Create Button */}
                                <button
                                    onClick={handleCreateSymbol}
                                    disabled={creating || !newLatex.trim()}
                                    className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {creating ? 'Создание...' : 'Создать и вставить'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
