# Быстрый старт: Импорт подразделов

## Что это?

Скрипт импортирует заголовки третьего уровня (`### 1. Название`) из markdown файлов в Neo4j как узлы **Subsection**.

## Предварительные требования

✅ Neo4j запущен и доступен  
✅ Есть файл `config/config.yml` с учетными данными  
✅ В базе уже импортированы Chapter, Section и Paragraph

## Быстрый запуск

### Шаг 1: Пробный запуск (dry-run)

```bash
cd graph-project
python import_subsections.py --dry-run
```

Этот режим **не вносит изменений** в базу данных, только показывает, что будет сделано.

### Шаг 2: Реальный импорт

Если dry-run прошёл успешно:

```bash
python import_subsections.py
```

## Что происходит?

1. ✅ Создаются узлы `Subsection` для каждого заголовка `###`
2. ✅ Связываются с родительскими `Section` через `HAS_SUBSECTION`
3. ✅ Существующие `Paragraph` переназначаются к соответствующим `Subsection`
4. ✅ Создаются связи `NEXT`/`PREVIOUS` между подразделами

## Безопасность

⚠️ **Важно**: Скрипт **НЕ изменяет** содержимое существующих узлов (Paragraph, Formula и т.д.)

Он только:

-   Создаёт новые узлы Subsection
-   Создаёт новые связи
-   Сохраняет все существующие данные

## Проверка результата

После импорта проверьте в Neo4j:

```cypher
// Сколько создано подразделов?
MATCH (sub:Subsection)
RETURN count(sub) as total

// Примеры подразделов
MATCH (s:Section)-[:HAS_SUBSECTION]->(sub:Subsection)
RETURN s.title as параграф, sub.number as номер, sub.title as подраздел
LIMIT 10
```

## Возможные проблемы

### Ошибка подключения к Neo4j

```
✗ Ошибка подключения к Neo4j
```

**Решение:** Проверьте в `config/config.yml`:

-   `uri`: должен быть `bolt://localhost:7687`
-   `username` и `password` - корректные
-   Neo4j запущен

### Файл конфигурации не найден

```
✗ Ошибка: файл конфигурации не найден!
```

**Решение:** Создайте `config/config.yml` или укажите путь:

```bash
python import_subsections.py --config /путь/к/config.yml
```

### Нет Section в базе

Если в базе еще нет данных, сначала выполните:

```bash
# Импортировать главы и секции
python run_import.py
```

## Дополнительная информация

Подробная документация: [SUBSECTION_ENTITY.md](./SUBSECTION_ENTITY.md)

## Помощь

```bash
python import_subsections.py --help
```
