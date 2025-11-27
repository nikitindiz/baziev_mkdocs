'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { Formula } from '@/types/formula';
import dynamic from 'next/dynamic';
import { SymbolPickerModal } from './SymbolPickerModal';

const BlockMath = dynamic(() => import('react-katex').then((mod) => mod.BlockMath), { ssr: false });
const InlineMath = dynamic(() => import('react-katex').then((mod) => mod.InlineMath), { ssr: false });

interface FormulaEditorProps {
    formulaId: string;
}

export function FormulaEditor({ formulaId }: FormulaEditorProps) {
    const router = useRouter();
    const queryClient = useQueryClient();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [formula, setFormula] = useState<Formula | null>(null);

    // Form state
    const [latex, setLatex] = useState('');
    const [formulaType, setFormulaType] = useState<'inline' | 'display'>('inline');
    const [isSymbol, setIsSymbol] = useState(false);
    const [symbolDefinition, setSymbolDefinition] = useState('');
    const [symbolValue, setSymbolValue] = useState('');
    const [symbolUnits, setSymbolUnits] = useState('');
    const [symbolConfidence, setSymbolConfidence] = useState<'high' | 'medium' | 'low' | ''>('');
    const [notSureIfSymbol, setNotSureIfSymbol] = useState(false);
    const [isSymbolPickerOpen, setIsSymbolPickerOpen] = useState(false);

    useEffect(() => {
        async function fetchFormula() {
            try {
                const response = await fetch(`/api/formulas/${formulaId}`);
                if (!response.ok) {
                    throw new Error('Failed to fetch formula');
                }
                const data: Formula = await response.json();
                setFormula(data);

                // Инициализируем форму данными
                setLatex(data.latex);
                setFormulaType(data.type);
                setIsSymbol(data.is_symbol || false);
                setSymbolDefinition(data.symbol_definition || '');
                setSymbolValue(data.symbol_value || '');
                setSymbolUnits(data.symbol_units || '');
                setSymbolConfidence((data.symbol_parse_confidence || '') as any);
                setNotSureIfSymbol(data.not_sure_if_this_is_symbol || false);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            } finally {
                setLoading(false);
            }
        }

        fetchFormula();
    }, [formulaId]);

    const handleCancel = () => {
        // Remove selected-formula query parameter
        const url = new URL(window.location.href);
        url.searchParams.delete('selected-formula');
        router.push(url.pathname + url.search, { scroll: false });
    };

    const handleSave = async () => {
        if (!formula) return;

        setSaving(true);
        setError(null);

        try {
            const response = await fetch(`/api/formulas/${formulaId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    latex,
                    type: formulaType,
                    is_symbol: isSymbol,
                    symbol_definition: isSymbol ? symbolDefinition : undefined,
                    symbol_value: isSymbol ? symbolValue : undefined,
                    symbol_units: isSymbol ? symbolUnits : undefined,
                    symbol_parse_confidence: isSymbol && symbolConfidence ? symbolConfidence : undefined,
                    not_sure_if_this_is_symbol: notSureIfSymbol,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to update formula');
            }

            const updatedFormula: Formula = await response.json();
            setFormula(updatedFormula);

            // Инвалидируем кеш параграфов для обновления связанных компонентов
            queryClient.invalidateQueries({ queryKey: ['paragraphs'] });
            // Инвалидируем все контексты параграфов для обновления страниц read-in-context
            queryClient.invalidateQueries({ queryKey: ['paragraph-context'] });

            // Закрываем редактор после успешного сохранения
            handleCancel();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setSaving(false);
        }
    };

    const handleSymbolSelect = (symbol: string) => {
        // Вставляем символ в текущую позицию курсора
        const textarea = document.querySelector('textarea') as HTMLTextAreaElement;
        if (textarea) {
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const newValue = latex.substring(0, start) + symbol + latex.substring(end);
            setLatex(newValue);

            // Возвращаем фокус и устанавливаем курсор после вставленного символа
            setTimeout(() => {
                textarea.focus();
                textarea.setSelectionRange(start + symbol.length, start + symbol.length);
            }, 0);
        }
        setIsSymbolPickerOpen(false);
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
                    <div className="bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg p-4 text-center min-h-20 flex items-center justify-center">
                        {latex ? (
                            formulaType === 'display' ? (
                                <BlockMath math={latex} />
                            ) : (
                                <InlineMath math={latex} />
                            )
                        ) : (
                            <div className="text-gray-400 dark:text-gray-500 text-sm">
                                Формула будет отображаться здесь
                            </div>
                        )}
                    </div>
                </div>

                {/* LaTeX Input */}
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            LaTeX
                        </label>
                        <button
                            type="button"
                            onClick={() => setIsSymbolPickerOpen(true)}
                            className="px-3 py-1 text-xs font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                        >
                            Symbol
                        </button>
                    </div>
                    <textarea
                        className="w-full h-24 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-mono text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Введите LaTeX код..."
                        value={latex}
                        onChange={(e) => setLatex(e.target.value)}
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
                                checked={formulaType === 'inline'}
                                onChange={(e) => setFormulaType(e.target.value as 'inline')}
                            />
                            <span className="text-sm text-gray-700 dark:text-gray-300">Встроенная</span>
                        </label>
                        <label className="flex items-center">
                            <input
                                type="radio"
                                name="formulaType"
                                value="display"
                                className="mr-2"
                                checked={formulaType === 'display'}
                                onChange={(e) => setFormulaType(e.target.value as 'display')}
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
                                checked={isSymbol}
                                onChange={(e) => setIsSymbol(e.target.checked)}
                            />
                            <label htmlFor="isSymbol" className="text-sm text-gray-700 dark:text-gray-300">
                                Это символ
                            </label>
                        </div>

                        {isSymbol && (
                            <>
                                <div className="space-y-1">
                                    <label className="block text-xs text-gray-600 dark:text-gray-400">
                                        Определение символа
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100"
                                        placeholder="Например: скорость света"
                                        value={symbolDefinition}
                                        onChange={(e) => setSymbolDefinition(e.target.value)}
                                    />
                                </div>

                                <div className="space-y-1">
                                    <label className="block text-xs text-gray-600 dark:text-gray-400">
                                        Значение символа
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100"
                                        placeholder="Например: 299792458"
                                        value={symbolValue}
                                        onChange={(e) => setSymbolValue(e.target.value)}
                                    />
                                </div>

                                <div className="space-y-1">
                                    <label className="block text-xs text-gray-600 dark:text-gray-400">
                                        Единицы измерения
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100"
                                        placeholder="Например: м/с"
                                        value={symbolUnits}
                                        onChange={(e) => setSymbolUnits(e.target.value)}
                                    />
                                </div>

                                <div className="space-y-1">
                                    <label className="block text-xs text-gray-600 dark:text-gray-400">
                                        Уверенность распознавания
                                    </label>
                                    <select
                                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-100"
                                        value={symbolConfidence}
                                        onChange={(e) => setSymbolConfidence(e.target.value as 'high' | 'medium' | 'low' | '')}
                                    >
                                        <option value="">Не определено</option>
                                        <option value="high">Высокая</option>
                                        <option value="medium">Средняя</option>
                                        <option value="low">Низкая</option>
                                    </select>
                                </div>

                                <div className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        id="notSureIfSymbol"
                                        className="rounded"
                                        checked={notSureIfSymbol}
                                        onChange={(e) => setNotSureIfSymbol(e.target.checked)}
                                    />
                                    <label htmlFor="notSureIfSymbol" className="text-xs text-gray-600 dark:text-gray-400">
                                        Не уверен, что это символ
                                    </label>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                {/* Metadata */}
                {formula && (
                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            Метаданные
                        </label>
                        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-3 space-y-2">
                            {typeof formula.metadata === 'object' && formula.metadata && (
                                <>
                                    {(formula.metadata as any).equation_number && (
                                        <div className="text-xs">
                                            <span className="text-gray-600 dark:text-gray-400">Номер уравнения: </span>
                                            <span className="text-gray-900 dark:text-gray-100 font-mono">
                                                {(formula.metadata as any).equation_number}
                                            </span>
                                        </div>
                                    )}
                                    {(formula.metadata as any).db_key && (
                                        <div className="text-xs">
                                            <span className="text-gray-600 dark:text-gray-400">DB Key: </span>
                                            <span className="text-gray-900 dark:text-gray-100 font-mono">
                                                {(formula.metadata as any).db_key}
                                            </span>
                                        </div>
                                    )}
                                    {(formula.metadata as any).src && (
                                        <div className="text-xs">
                                            <span className="text-gray-600 dark:text-gray-400">Источник: </span>
                                            <span className="text-gray-900 dark:text-gray-100 font-mono break-all">
                                                {(formula.metadata as any).src}
                                            </span>
                                        </div>
                                    )}
                                </>
                            )}
                            {typeof formula.source === 'object' && formula.source && (
                                <>
                                    {(formula.source as any).file && (
                                        <div className="text-xs">
                                            <span className="text-gray-600 dark:text-gray-400">Файл: </span>
                                            <span className="text-gray-900 dark:text-gray-100 font-mono break-all">
                                                {(formula.source as any).file}
                                            </span>
                                        </div>
                                    )}
                                    {(formula.source as any).position !== undefined && (
                                        <div className="text-xs">
                                            <span className="text-gray-600 dark:text-gray-400">Позиция: </span>
                                            <span className="text-gray-900 dark:text-gray-100 font-mono">
                                                {(formula.source as any).position}
                                            </span>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                )}

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
                    onClick={handleSave}
                    disabled={saving || !latex}
                >
                    {saving ? 'Сохранение...' : 'Сохранить'}
                </button>
                <button
                    className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg font-medium text-sm transition-colors"
                    onClick={handleCancel}
                    disabled={saving}
                >
                    Отмена
                </button>
            </div>

            {/* Symbol Picker Modal */}
            <SymbolPickerModal
                isOpen={isSymbolPickerOpen}
                onClose={() => setIsSymbolPickerOpen(false)}
                onSelect={handleSymbolSelect}
                formulaId={formulaId}
            />
        </div>
    );
}
