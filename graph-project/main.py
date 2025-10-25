#!/usr/bin/env python3
"""
Главный скрипт для работы с графом знаний
"""
import click
import logging
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import load_config
from src.utils.neo4j_connection import Neo4jConnection
from src.utils.exporter import GraphExporter
from src.importers.structure_importer import StructureImporter
from src.importers.artifacts_importer import ArtifactsImporter
from src.importers.content_linker import ContentLinker
from src.queries.graph_queries import GraphQueries

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx):
    """Граф знаний - Физика Базиева"""
    ctx.ensure_object(dict)
    
    # Загрузка конфигурации
    config = load_config()
    ctx.obj['config'] = config
    
    # Подключение к Neo4j
    neo4j_conn = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    ctx.obj['neo4j'] = neo4j_conn


@cli.group()
def import_cmd():
    """Импорт данных в граф"""
    pass


@import_cmd.command('all')
@click.pass_context
def import_all(ctx):
    """Импортировать все данные"""
    config = ctx.obj['config']
    neo4j = ctx.obj['neo4j']
    
    if config['import']['clear_database']:
        click.confirm('Вы уверены, что хотите очистить базу данных?', abort=True)
        neo4j.clear_database()
    
    if config['import']['create_constraints']:
        logger.info("Creating constraints...")
        neo4j.create_constraints()
    
    if config['import']['create_indexes']:
        logger.info("Creating indexes...")
        neo4j.create_indexes()
    
    # Импорт структуры
    logger.info("Importing structure...")
    structure_importer = StructureImporter(neo4j, config)
    structure_importer.import_book()
    structure_importer.import_chapters()
    
    # Импорт артефактов
    logger.info("Importing artifacts...")
    artifacts_importer = ArtifactsImporter(neo4j, config)
    artifacts_importer.import_formulas()
    artifacts_importer.import_symbols()
    artifacts_importer.import_illustrations()
    artifacts_importer.import_tables()
    artifacts_importer.import_literature()
    
    # Связывание
    logger.info("Linking artifacts...")
    artifacts_importer.link_formulas_to_symbols()
    
    # Импорт параграфов и связывание контента
    logger.info("Importing paragraphs and linking content...")
    content_linker = ContentLinker(neo4j, config)
    content_linker.import_sections_and_paragraphs()
    content_linker.link_content()
    
    # Статистика
    stats = neo4j.get_stats()
    logger.info("Import completed!")
    logger.info("Statistics:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")


@import_cmd.command('structure')
@click.pass_context
def import_structure(ctx):
    """Импортировать только структуру (Book, Chapter)"""
    config = ctx.obj['config']
    neo4j = ctx.obj['neo4j']
    
    structure_importer = StructureImporter(neo4j, config)
    structure_importer.import_book()
    structure_importer.import_chapters()
    
    logger.info("Structure import completed!")


@import_cmd.command('formulas')
@click.pass_context
def import_formulas(ctx):
    """Импортировать формулы"""
    config = ctx.obj['config']
    neo4j = ctx.obj['neo4j']
    
    artifacts_importer = ArtifactsImporter(neo4j, config)
    artifacts_importer.import_formulas()
    artifacts_importer.link_formulas_to_symbols()
    
    logger.info("Formulas import completed!")


@import_cmd.command('symbols')
@click.pass_context
def import_symbols(ctx):
    """Импортировать символы"""
    config = ctx.obj['config']
    neo4j = ctx.obj['neo4j']
    
    artifacts_importer = ArtifactsImporter(neo4j, config)
    artifacts_importer.import_symbols()
    
    logger.info("Symbols import completed!")


@import_cmd.command('illustrations')
@click.pass_context
def import_illustrations(ctx):
    """Импортировать иллюстрации"""
    config = ctx.obj['config']
    neo4j = ctx.obj['neo4j']
    
    artifacts_importer = ArtifactsImporter(neo4j, config)
    artifacts_importer.import_illustrations()
    
    logger.info("Illustrations import completed!")


@import_cmd.command('tables')
@click.pass_context
def import_tables(ctx):
    """Импортировать таблицы"""
    config = ctx.obj['config']
    neo4j = ctx.obj['neo4j']
    
    artifacts_importer = ArtifactsImporter(neo4j, config)
    artifacts_importer.import_tables()
    
    logger.info("Tables import completed!")


@import_cmd.command('literature')
@click.pass_context
def import_literature(ctx):
    """Импортировать литературу"""
    config = ctx.obj['config']
    neo4j = ctx.obj['neo4j']
    
    artifacts_importer = ArtifactsImporter(neo4j, config)
    artifacts_importer.import_literature()
    
    logger.info("Literature import completed!")


@cli.group()
def query():
    """Выполнить запросы к графу"""
    pass


@query.command('formulas-in-section')
@click.option('--section-id', required=True, help='ID раздела')
@click.pass_context
def query_formulas_in_section(ctx, section_id):
    """Найти все формулы в разделе"""
    neo4j = ctx.obj['neo4j']
    queries = GraphQueries(neo4j)
    
    results = queries.formulas_in_section(section_id)
    
    click.echo(f"\nФормулы в разделе {section_id}:")
    for r in results:
        click.echo(f"  [{r['equation_number']}] {r['latex']}")


@query.command('symbol-usage')
@click.option('--latex', required=True, help='LaTeX символа')
@click.pass_context
def query_symbol_usage(ctx, latex):
    """Найти использования символа"""
    neo4j = ctx.obj['neo4j']
    queries = GraphQueries(neo4j)
    
    results = queries.symbol_usage(latex)
    
    click.echo(f"\nИспользования символа {latex}:")
    for r in results:
        click.echo(f"  {r['section_title']}: [{r['equation_number']}] {r['formula']}")


@query.command('top-cited')
@click.option('--limit', default=10, help='Количество результатов')
@click.pass_context
def query_top_cited(ctx, limit):
    """Самые цитируемые источники"""
    neo4j = ctx.obj['neo4j']
    queries = GraphQueries(neo4j)
    
    results = queries.top_cited_literature(limit)
    
    click.echo(f"\nТоп {limit} цитируемых источников:")
    for r in results:
        click.echo(f"  [{r['number']}] {r['author']}: {r['title']} (цитирований: {r['citation_count']})")


@query.command('chapter-stats')
@click.pass_context
def query_chapter_stats(ctx):
    """Статистика по главам"""
    neo4j = ctx.obj['neo4j']
    queries = GraphQueries(neo4j)
    
    results = queries.chapter_statistics()
    
    click.echo("\nСтатистика по главам:")
    click.echo(f"{'Глава':<60} | Разделы | Параграфы | Формулы")
    click.echo("-" * 100)
    for r in results:
        click.echo(f"{r['chapter']:<60} | {r['sections']:^7} | {r['paragraphs']:^10} | {r['formulas']:^7}")


@cli.command('stats')
@click.pass_context
def show_stats(ctx):
    """Показать статистику графа"""
    neo4j = ctx.obj['neo4j']
    stats = neo4j.get_stats()
    
    click.echo("\nСтатистика графа:")
    for key, value in stats.items():
        click.echo(f"  {key}: {value}")


@import_cmd.command('paragraphs')
@click.pass_context
def import_paragraphs(ctx):
    """Импортировать параграфы из markdown файлов"""
    config = ctx.obj['config']
    neo4j = ctx.obj['neo4j']
    
    content_linker = ContentLinker(neo4j, config)
    content_linker.import_sections_and_paragraphs()
    
    logger.info("Paragraphs import completed!")


@import_cmd.command('link-content')
@click.pass_context
def link_content(ctx):
    """Связать контент (формулы, иллюстрации и т.д.) с параграфами"""
    config = ctx.obj['config']
    neo4j = ctx.obj['neo4j']
    
    content_linker = ContentLinker(neo4j, config)
    content_linker.link_content()
    
    logger.info("Content linking completed!")


@cli.group()
def export():
    """Экспортировать граф в различные форматы"""
    pass


@export.command('json')
@click.option('--output', '-o', default='graph.json', help='Выходной файл')
@click.pass_context
def export_json(ctx, output):
    """Экспортировать граф в JSON"""
    neo4j = ctx.obj['neo4j']
    exporter = GraphExporter(neo4j)
    
    from pathlib import Path
    exporter.export_to_json(Path(output))
    click.echo(f"Graph exported to {output}")


@export.command('graphml')
@click.option('--output', '-o', default='graph.graphml', help='Выходной файл')
@click.pass_context
def export_graphml(ctx, output):
    """Экспортировать граф в GraphML"""
    neo4j = ctx.obj['neo4j']
    exporter = GraphExporter(neo4j)
    
    from pathlib import Path
    exporter.export_to_graphml(Path(output))
    click.echo(f"Graph exported to {output}")


@export.command('glossary')
@click.option('--output', '-o', default='glossary.md', help='Выходной файл')
@click.pass_context
def export_glossary(ctx, output):
    """Экспортировать глоссарий символов"""
    neo4j = ctx.obj['neo4j']
    exporter = GraphExporter(neo4j)
    
    from pathlib import Path
    exporter.export_glossary(Path(output))
    click.echo(f"Glossary exported to {output}")


@export.command('formula-index')
@click.option('--output', '-o', default='formula-index.md', help='Выходной файл')
@click.pass_context
def export_formula_index(ctx, output):
    """Экспортировать указатель формул"""
    neo4j = ctx.obj['neo4j']
    exporter = GraphExporter(neo4j)
    
    from pathlib import Path
    exporter.export_formula_index(Path(output))
    click.echo(f"Formula index exported to {output}")


@cli.command('serve')
@click.option('--port', default=4000, help='Порт для API сервера')
@click.pass_context
def serve_api(ctx, port):
    """Запустить GraphQL API сервер"""
    click.echo(f"Starting API server on port {port}...")
    click.echo("(Not implemented yet)")
    # TODO: Implement GraphQL API


if __name__ == '__main__':
    cli(obj={})
