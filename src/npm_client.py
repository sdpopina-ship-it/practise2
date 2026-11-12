"""Получение информации о пакетах из HTTP API реестра npm."""

from collections.abc import Mapping
from dataclasses import dataclass
from json import JSONDecodeError, load
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.config import AppConfig


REQUEST_TIMEOUT_SECONDS = 10
NPM_ACCEPT_HEADER = "application/json"
USER_AGENT = "npm-dependency-visualizer/1.0"
HTTP_NOT_FOUND_STATUS = 404


class NpmClientError(RuntimeError):
    """Сообщает об ошибке получения или разбора данных npm."""


@dataclass(frozen=True)
class Dependency:
    """Описывает прямую зависимость и её npm-диапазон версии."""

    name: str
    version_range: str


def get_direct_dependencies(config: AppConfig) -> tuple[Dependency, ...]:
    """Возвращает прямые зависимости указанной версии npm-пакета."""
    if config.use_test_repository:
        raise NpmClientError(
            "На этапе 2 use_test_repository должно быть установлено в false."
        )
    package_url = build_package_url(
        config.repository,
        config.package_name,
        config.package_version,
    )
    metadata = download_package_metadata(package_url)
    return extract_direct_dependencies(metadata)


def build_package_url(
    repository_url: str,
    package_name: str,
    package_version: str,
) -> str:
    """Собирает URL эндпоинта npm для конкретной версии пакета."""
    encoded_name = quote(package_name, safe="")
    encoded_version = quote(package_version, safe="")
    return f"{repository_url.rstrip('/')}/{encoded_name}/{encoded_version}"


def download_package_metadata(package_url: str) -> dict[str, Any]:
    """Запрашивает JSON-описание пакета у реестра npm."""
    request = Request(
        package_url,
        headers={"Accept": NPM_ACCEPT_HEADER, "User-Agent": USER_AGENT},
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            metadata = load(response)
    except HTTPError as error:
        raise NpmClientError(http_error_message(error, package_url)) from error
    except URLError as error:
        message = f"Не удалось подключиться к npm: {error.reason}"
        raise NpmClientError(message) from error
    except JSONDecodeError as error:
        raise NpmClientError("Реестр npm вернул некорректный JSON.") from error
    if not isinstance(metadata, dict):
        raise NpmClientError("Описание npm-пакета должно быть JSON-объектом.")
    return metadata


def http_error_message(error: HTTPError, package_url: str) -> str:
    """Формирует понятное сообщение о статусе HTTP-ответа npm."""
    if error.code == HTTP_NOT_FOUND_STATUS:
        return f"Пакет или его версия не найдены: {package_url}"
    return f"Реестр npm вернул HTTP {error.code}: {error.reason}"


def extract_direct_dependencies(
    metadata: Mapping[str, Any],
) -> tuple[Dependency, ...]:
    """Извлекает и сортирует поле dependencies из метаданных npm-пакета."""
    dependencies = metadata.get("dependencies", {})
    if dependencies is None:
        return ()
    if not isinstance(dependencies, Mapping):
        raise NpmClientError("Поле dependencies должно быть JSON-объектом.")
    result = [
        Dependency(name, version_range)
        for name, version_range in dependencies.items()
        if is_valid_dependency(name, version_range)
    ]
    if len(result) != len(dependencies):
        message = "Каждая зависимость должна иметь имя и строку версии."
        raise NpmClientError(message)
    return tuple(sorted(result, key=lambda dependency: dependency.name.lower()))


def is_valid_dependency(name: object, version_range: object) -> bool:
    """Проверяет типы имени зависимости и её npm-диапазона версии."""
    return isinstance(name, str) and isinstance(version_range, str)
