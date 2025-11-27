# Проблема: Греческие буквы обернуты в \text{}

## Описание

В базе данных Neo4j в формулах (узлы типа `Formula`) обнаружена ошибка: греческие буквы ошибочно обернуты в команду `\text{}`.

Например:

-   `\text{\alpha}` вместо `\alpha`
-   `\text{\lambda}` вместо `\lambda`
-   `\text{\mu}` вместо `\mu`

## Статистика

Всего формул с `\text{\` конструкциями: **716**

Распределение по греческим буквам:

-   `\text{\lambda}`: 77 формул
-   `\text{\pi}`: 24 формул
-   `\text{\mu}`: 23 формул
-   `\text{\alpha}`: 22 формул
-   `\text{\omega}`: 21 формул
-   `\text{\rho}`: 9 формул
-   `\text{\nu}`: 8 формул
-   `\text{\tau}`: 6 формул

## Примеры ошибочных формул

1. `\eta_{\text{\pi}}(\Delta \varphi) = \Delta \varphi / 2\pi`
2. `\mu_{\text{\lambda}}`
3. `n_{\text{\alpha}}`
4. `d_{\text{\lambda}}`
5. `Z_{\text{\lambda}} = S_{\text{\lambda}} \cdot j_{n} = \frac{\pi \cdot d_{\text{\lambda}}^{2} \cdot j_{n}}{4}`

## Правильная форма

Греческие буквы в LaTeX не должны быть обернуты в `\text{}`:

-   ❌ `\text{\lambda}`
-   ✅ `\lambda`

Команда `\text{}` предназначена для обычного текста, а не для математических символов.

## Решение

Создать скрипт для массового исправления всех вхождений:

```cypher
// Для каждой греческой буквы выполнить замену
MATCH (f:Formula)
WHERE f.latex CONTAINS '\\text{\\'
SET f.latex =
  replace(
    replace(
      replace(
        replace(
          replace(
            replace(
              replace(
                replace(f.latex,
                  '\\text{\\alpha}', '\\alpha'),
                '\\text{\\lambda}', '\\lambda'),
              '\\text{\\mu}', '\\mu'),
            '\\text{\\pi}', '\\pi'),
          '\\text{\\rho}', '\\rho'),
        '\\text{\\nu}', '\\nu'),
      '\\text{\\tau}', '\\tau'),
    '\\text{\\omega}', '\\omega')
RETURN count(f) as updated_count
```

## Риски

1. Нужно убедиться, что `\text{}` используется ТОЛЬКО для греческих букв в нижних индексах
2. Может быть легитимное использование `\text{}` для другого текста (например, русских слов)

## Дополнительная проверка

Нужно проверить, есть ли в формулах легитимное использование `\text{}`:

```cypher
MATCH (f:Formula)
WHERE f.latex CONTAINS '\\text{'
  AND NOT f.latex CONTAINS '\\text{\\alpha}'
  AND NOT f.latex CONTAINS '\\text{\\lambda}'
  AND NOT f.latex CONTAINS '\\text{\\mu}'
  AND NOT f.latex CONTAINS '\\text{\\pi}'
  AND NOT f.latex CONTAINS '\\text{\\rho}'
  AND NOT f.latex CONTAINS '\\text{\\nu}'
  AND NOT f.latex CONTAINS '\\text{\\tau}'
  AND NOT f.latex CONTAINS '\\text{\\omega}'
RETURN f.id, f.latex
LIMIT 10
```

**Результат:** Найдено 4608 формул с легитимным использованием `\text{}` для русских слов и единиц измерения.

## Результат исправления

✅ **Исправлено:** 189 формул  
✅ **Проверка:** 0 формул с оставшимися ошибками  
✅ **Дата исправления:** 27 ноября 2025

Скрипт: `graph-project/fix_greek_letters_in_subscripts.py`

Все греческие буквы успешно исправлены. Легитимное использование `\text{}` для обычного текста (русские слова, единицы измерения) сохранено.
