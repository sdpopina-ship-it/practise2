"""Чтение и проверка параметров приложения из TOML-конфигурации."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import tomllib


DEFAULT_MAX_DEPTH = 3


class ConfigError(ValueError):
    """Сообщает о некорректном или неполном файле конфигурации."""


@dataclass(frozen=True)
class AppConfig:
    """Параметры запуска визуализатора зависимостей."""

    package_name: str
    repository: str
    use_test_repository: bool
    package_version: str
    ascii_tree: bool
    max_depth: int


def load_config(config_path: Path) -> AppConfig:
    """Загружает TOML-файл и возвращает проверенные параметры приложения."""
    if not config_path.is_file():
        raise ConfigError(f"Файл конфигурации не найден: {config_path}")
    try:
        with config_path.open("rb") as config_file:
            raw_config = tomllib.load(config_file)
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"Ошибка формата TOML: {error}") from error
    return parse_config(raw_config, config_path.parent)


def parse_config(raw_config: dict[str, Any], base_path: Path) -> AppConfig:
    """Проверяет все обязательные поля разобранной TOML-конфигурации."""
    test_mode = require_boolean(raw_config, "use_test_repository")
    repository = require_repository(raw_config, test_mode, base_path)
    return AppConfig(
        package_name=require_text(raw_config, "package_name"),
        repository=repository,
        use_test_repository=test_mode,
        package_version=require_text(raw_config, "package_version"),
        ascii_tree=require_boolean(raw_config, "ascii_tree"),
        max_depth=require_positive_integer(raw_config, "max_depth"),
    )


def require_text(raw_config: dict[str, Any], field_name: str) -> str:
    """Возвращает обязательную непустую строку из конфигурации."""
    value = raw_config.get(field_name)
    if not isinstance(value, str) or not value.strip():
        message = f"Параметр {field_name} должен быть непустой строкой."
        raise ConfigError(message)
    return value.strip()


def require_boolean(raw_config: dict[str, Any], field_name: str) -> bool:
    """Возвращает обязательное логическое значение из конфигурации."""
    value = raw_config.get(field_name)
    if not isinstance(value, bool):
        raise ConfigError(f"Параметр {field_name} должен быть true или false.")
    return value


def require_positive_integer(
    raw_config: dict[str, Any],
    field_name: str,
) -> int:
    """Возвращает обязательное положительное целое число."""
    value = raw_config.get(field_name)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        message = f"Параметр {field_name} должен быть целым числом от 1."
        raise ConfigError(message)
    return value


def require_repository(
    raw_config: dict[str, Any],
    test_mode: bool,
    base_path: Path,
) -> str:
    """Проверяет URL npm-репозитория или файл тестового репозитория."""
    repository = require_text(raw_config, "repository")
    if test_mode:
        verify_test_repository(repository, base_path)
    else:
        verify_repository_url(repository)
    return repository


def verify_test_repository(repository: str, base_path: Path) -> None:
    """Проверяет, что тестовый репозиторий существует в файловой системе."""
    repository_path = Path(repository).expanduser()
    if not repository_path.is_absolute():
        repository_path = base_path / repository_path
    if not repository_path.is_file():
        message = "В режиме тестирования repository должен ссылаться на файл: "
        raise ConfigError(message + str(repository_path))


def verify_repository_url(repository: str) -> None:
    """Проверяет, что адрес репозитория является HTTP(S)-URL."""
    parsed_url = urlparse(repository)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        message = "В обычном режиме repository должен быть HTTP(S)-адресом."
        raise ConfigError(message)
