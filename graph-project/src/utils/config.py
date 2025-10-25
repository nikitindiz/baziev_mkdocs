"""
Утилиты для работы с конфигурацией
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Загрузить конфигурацию из YAML файла"""
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yml"
    
    # Если config.yml не существует, используем example
    if not os.path.exists(config_path):
        config_path = Path(__file__).parent.parent.parent / "config" / "config.example.yml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Загрузить переменные окружения из .env
    env_path = Path(__file__).parent.parent.parent / ".env"
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    # Переопределить из переменных окружения
    if os.getenv("NEO4J_URI"):
        config["neo4j"]["uri"] = os.getenv("NEO4J_URI")
    if os.getenv("NEO4J_USERNAME"):
        config["neo4j"]["username"] = os.getenv("NEO4J_USERNAME")
    if os.getenv("NEO4J_PASSWORD"):
        config["neo4j"]["password"] = os.getenv("NEO4J_PASSWORD")
    if os.getenv("NEO4J_DATABASE"):
        config["neo4j"]["database"] = os.getenv("NEO4J_DATABASE")
    
    return config


def get_absolute_path(relative_path: str, base_path: str = None) -> Path:
    """Получить абсолютный путь относительно проекта"""
    if base_path is None:
        base_path = Path(__file__).parent.parent.parent
    else:
        base_path = Path(base_path)
    
    return (base_path / relative_path).resolve()
