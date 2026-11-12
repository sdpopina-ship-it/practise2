"""Точка входа второго этапа практической работы."""

import argparse
from pathlib import Path
from typing import Sequence

from src.config import AppConfig, ConfigError, load_config
from src.npm_client import Dependency, NpmClientError, get_direct_dependencies


DEFAULT_CONFIG_PATH = Path("examples/config.toml")


def create_parser() -> argparse.ArgumentParser:
    """Создаёт парсер аргумента пути к TOML-конфигурации."""
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей npm (этап 2)."
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


def format_dependencies(
    dependencies: tuple[Dependency, ...],
) -> tuple[str, ...]:
    """Преобразует зависимости в строки для вывода командной строки."""
    if not dependencies:
        return ("Прямые зависимости не найдены.",)
    return tuple(
        f"{dependency.name}: {dependency.version_range}"
        for dependency in dependencies
    )


def main(arguments: Sequence[str] | None = None) -> int:
    """Выводит прямые зависимости npm-пакета или сообщение об ошибке."""
    parser = create_parser()
    options = parser.parse_args(arguments)
    try:
        config = load_config(options.config)
    except ConfigError as error:
        print(f"Ошибка конфигурации: {error}")
        return 1
    try:
        dependencies = get_direct_dependencies(config)
    except NpmClientError as error:
        print(f"Ошибка npm: {error}")
        return 1
    package = f"{config.package_name}@{config.package_version}"
    print(f"Прямые зависимости {package}:")
    print(*format_dependencies(dependencies), sep="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
