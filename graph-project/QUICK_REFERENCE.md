# Graph Project - Quick Reference

## 🚀 Установка (5 минут)

```bash
# 1. Запустить Neo4j
docker run -d --name neo4j-baziev -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password neo4j:latest

# 2. Настроить проект
cd graph-project
./setup.sh

# 3. Проверить
python check.py

# 4. Импортировать данные (~10 минут)
source venv/bin/activate
python main.py import all
```

## 📋 Частые команды

### Импорт
```bash
python main.py import all              # Всё сразу
python main.py import structure        # Только структура
python main.py import formulas         # Только формулы
python main.py import link-content     # Связывание
```

### Запросы
```bash
python main.py stats                   # Общая статистика
python main.py query chapter-stats     # По главам
python main.py query top-cited         # Топ литературы
python examples.py                     # Все примеры
```

### Экспорт
```bash
python main.py export glossary -o glossary.md
python main.py export formula-index -o formulas.md
python main.py export json -o graph.json
```

## 🔑 Ключевые файлы

| Файл | Описание |
|------|----------|
| `config/config.yml` | Настройки Neo4j и пути |
| `main.py` | CLI интерфейс |
| `examples.py` | Примеры использования |
| `check.py` | Проверка установки |

## 📊 Статистика данных

После импорта:
- **Формулы**: ~1000+
- **Символы**: ~200+
- **Иллюстрации**: ~65
- **Таблицы**: ~36
- **Литература**: ~48
- **Параграфы**: ~2000+
- **Всего узлов**: ~3000-5000
- **Всего связей**: ~10000-20000

## 🔍 Примеры Cypher

```cypher
// Топ используемых символов
MATCH (s:Symbol)<-[:USES_SYMBOL]-(f:Formula)
WITH s, count(f) as usage
RETURN s.latex, s.description, usage
ORDER BY usage DESC LIMIT 10;

// Самые цитируемые источники
MATCH (l:Literature)<-[:CITES]-(p:Paragraph)
RETURN l.author, l.title, count(p) as citations
ORDER BY citations DESC LIMIT 10;

// Формулы в разделе
MATCH (s:Section)-[:HAS_PARAGRAPH]->(p)-[:CONTAINS_FORMULA]->(f)
RETURN f.latex LIMIT 25;
```

## ⚙️ Конфигурация

**config/config.yml**:
```yaml
neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "password"
  database: "baziev"

paths:
  # Важно! Документы со ссылками на сущности
  docs: "../normalized/step-05-extract-and-link-quoted-literature/result"
  formulas: "../normalized/formulas"
  symbols: "../normalized/symbols"
  # и т.д.
```

## 🐛 Решение проблем

### Ошибка подключения к Neo4j
```bash
neo4j status          # Проверить статус
neo4j start           # Запустить
```

### Медленный импорт
Увеличьте `batch_size` в config.yml:
```yaml
import:
  batch_size: 500  # вместо 100
```

### Очистить базу
```bash
python main.py import all --clear-database
# ⚠️ УДАЛИТ ВСЕ ДАННЫЕ!
```

## 📚 Документация

- **README.md** - главная документация
- **ARCHITECTURE.md** - архитектура проекта
- **USAGE.md** - детальное руководство
- **PROJECT_SUMMARY.md** - что реализовано

## 🌐 Полезные ссылки

- Neo4j Browser: http://localhost:7474
- Документация Neo4j: https://neo4j.com/docs/
- Cypher руководство: https://neo4j.com/docs/cypher-manual/

## 💡 Советы

1. Всегда проверяйте `python check.py` перед импортом
2. Используйте `python main.py stats` для мониторинга
3. Начните с `python examples.py` для знакомства с API
4. Изучите `src/queries/examples.cypher` для продвинутых запросов
5. Neo4j Browser отлично подходит для визуального исследования

---

**Быстрая помощь**: `python main.py --help`
