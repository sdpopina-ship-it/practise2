"""Точка входа второго этапа практической работы."""

import argparse
from pathlib import Path
from typing import Sequence

from src.config import AppConfig, ConfigError, load_config
from src.graph import GraphError, format_graph, build_dependency_graph
from src.npm_client import NpmClientError


DEFAULT_CONFIG_PATH = Path("examples/config.toml")


def create_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргумента пути к TOML-конфигурации."""
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей npm (этап 3)."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="путь к TOML-файлу конфигурации",
    )
    return parser


def format_settings(config: AppConfig) -> tuple[str, ...]:
    """Преобразует параметры в строки формата ключ = значение."""
    return (
        f"package_name = {config.package_name}",
        f"repository = {config.repository}",
        f"use_test_repository = {config.use_test_repository}",
        f"package_version = {config.package_version}",
        f"ascii_tree = {config.ascii_tree}",
        f"max_depth = {config.max_depth}",
    )


def main(arguments: Sequence[str] | None = None) -> int:
    """Строит и выводит граф зависимостей или сообщение об ошибке."""
    parser = create_parser()
    options = parser.parse_args(arguments)
    try:
        config = load_config(options.config)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}")
        return 1
    try:
        graph = build_dependency_graph(config)
    except (GraphError, NpmClientError) as error:
        print(f"Ошибка построения графа: {error}")
        return 1
    package = f"{config.package_name}@{config.package_version}"
    print(f"Граф зависимостей {package}:")
    print(*format_graph(graph), sep="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
