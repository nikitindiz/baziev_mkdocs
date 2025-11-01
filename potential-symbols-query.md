# Запрос для поиска формул без арифметических и других операторов

Задача: найти чистые обозначения - переменные, константы, химические формулы и обозначения без математических операций.

## Запрос к neo4j

Этот запрос находит формулы, которые не содержат:

- Арифметические операторы: +, -, *, /
- Операторы сравнения: =, <, >, ≥, ≤, ≈, ≠
- Дополнительные операторы: ±, ×, ÷, ≫, ≪, ⋅
- LaTeX функции: \frac, \sum, \int, \prod
- Стрелки: \rightarrow, \leftarrow, \rightleftharpoons (→, ←, ⇌)
- Отношения: \approx, \sim, \simeq, \equiv, \propto, \neq
- Специальные символы: \pm, \geq, \leq, \gg, \ll, \cdot
- Запятые: ,

```cypher
MATCH (f:Formula)
WHERE f.latex IS NOT NULL 
  AND NOT f.latex CONTAINS '+'
  AND NOT f.latex CONTAINS '-'
  AND NOT f.latex CONTAINS '*'
  AND NOT f.latex CONTAINS '/'
  AND NOT f.latex CONTAINS '='
  AND NOT f.latex CONTAINS '<'
  AND NOT f.latex CONTAINS '>'
  AND NOT f.latex CONTAINS '±'
  AND NOT f.latex CONTAINS '×'
  AND NOT f.latex CONTAINS '÷'
  AND NOT f.latex CONTAINS '\\frac'
  AND NOT f.latex CONTAINS '\\sum'
  AND NOT f.latex CONTAINS '\\int'
  AND NOT f.latex CONTAINS '\\prod'
  AND NOT f.latex CONTAINS '\\rightarrow'
  AND NOT f.latex CONTAINS '\\leftarrow'
  AND NOT f.latex CONTAINS '\\rightleftharpoons'
  AND NOT f.latex CONTAINS '\\approx'
  AND NOT f.latex CONTAINS '\\neq'
  AND NOT f.latex CONTAINS '≈'
  AND NOT f.latex CONTAINS '≠'
  AND NOT f.latex CONTAINS '→'
  AND NOT f.latex CONTAINS '←'
  AND NOT f.latex CONTAINS '⇌'
  AND NOT f.latex CONTAINS '\\sim'
  AND NOT f.latex CONTAINS '\\simeq'
  AND NOT f.latex CONTAINS '\\equiv'
  AND NOT f.latex CONTAINS '\\propto'
  AND NOT f.latex CONTAINS '\\pm'
  AND NOT f.latex CONTAINS ','
  AND NOT f.latex CONTAINS '\\geq'
  AND NOT f.latex CONTAINS '\\leq'
  AND NOT f.latex CONTAINS '≥'
  AND NOT f.latex CONTAINS '≤'
  AND NOT f.latex CONTAINS '\\gg'
  AND NOT f.latex CONTAINS '\\ll'
  AND NOT f.latex CONTAINS '≫'
  AND NOT f.latex CONTAINS '≪'
  AND NOT f.latex CONTAINS '\\cdot'
  AND NOT f.latex CONTAINS '⋅'
RETURN count(f) as total_count
```