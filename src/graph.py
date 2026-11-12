"""Построение графа зависимостей npm рекурсивным обходом DFS."""

from collections.abc import Callable, Mapping
from json import JSONDecodeError, load
from pathlib import Path
from typing import TypeAlias

from src.config import AppConfig
from src.npm_client import get_package_dependencies


DependencyGraph: TypeAlias = dict[str, tuple[str, ...]]
NodeLoader: TypeAlias = Callable[[str], tuple[str, ...]]
PACKAGE_NAME_LENGTH = 1


class GraphError(RuntimeError):
    """Сообщает об ошибках чтения или построения графа зависимостей."""


def build_dependency_graph(config: AppConfig) -> DependencyGraph:
    """Строит граф из тестового файла или через реестр npm."""
    if config.use_test_repository:
        return build_test_graph(config)
    return build_npm_graph(config)


def build_test_graph(config: AppConfig) -> DependencyGraph:
    """Строит граф из локального файла тестового репозитория."""
    repository = load_test_repository(Path(config.repository))
    if config.package_name not in repository:
        message = (
            f"Пакет {config.package_name} не найден в тестовом репозитории."
        )
        raise GraphError(message)
    return build_graph_with_dfs(
        config.package_name,
        repository.__getitem__,
        config.max_depth,
    )


def build_npm_graph(config: AppConfig) -> DependencyGraph:
    """Строит граф, последовательно запрашивая версии пакетов из npm."""
    root_node = package_label(config.package_name, config.package_version)
    package_references = {
        root_node: (config.package_name, config.package_version),
    }

    def load_node(node: str) -> tuple[str, ...]:
        """Загружает зависимости npm-пакета и создаёт подписи его потомков."""
        package_name, package_version = package_references[node]
        dependencies = get_package_dependencies(
            config.repository,
            package_name,
            package_version,
        )
        labels = tuple(
            package_label(dependency.name, dependency.version_range)
            for dependency in dependencies
        )
        for dependency, label in zip(dependencies, labels, strict=True):
            package_references[label] = (
                dependency.name,
                dependency.version_range,
            )
        return labels

    return build_graph_with_dfs(root_node, load_node, config.max_depth)


def package_label(package_name: str, package_version: str) -> str:
    """Формирует однозначную строковую подпись npm-пакета в графе."""
    return f"{package_name}@{package_version}"


def build_graph_with_dfs(
    root_node: str,
    load_node: NodeLoader,
    max_depth: int,
) -> DependencyGraph:
    """Обходит зависимости DFS с рекурсией и ограничением глубины."""
    graph: DependencyGraph = {}
    active_nodes: set[str] = set()
    minimum_depths: dict[str, int] = {}

    def visit(node: str, depth: int) -> None:
        """Добавляет узел и его потомков, не зацикливая рекурсию."""
        previous_depth = minimum_depths.get(node)
        already_processed = (
            previous_depth is not None and previous_depth <= depth
        )
        if node in active_nodes or already_processed:
            return
        minimum_depths[node] = depth
        if depth >= max_depth:
            graph[node] = ()
            return
        active_nodes.add(node)
        dependencies = load_node(node)
        graph[node] = dependencies
        for dependency in dependencies:
            visit(dependency, depth + 1)
        active_nodes.remove(node)

    visit(root_node, 0)
    return graph


def load_test_repository(repository_path: Path) -> DependencyGraph:
    """Загружает JSON-граф тестового репозитория и проверяет его формат."""
    try:
        with repository_path.open(encoding="utf-8") as repository_file:
            raw_repository = load(repository_file)
    except OSError as error:
        message = f"Не удалось открыть тестовый репозиторий: {error}"
        raise GraphError(message) from error
    except JSONDecodeError as error:
        message = f"Тестовый репозиторий содержит неверный JSON: {error}"
        raise GraphError(message) from error
    return validate_test_repository(raw_repository)


def validate_test_repository(raw_repository: object) -> DependencyGraph:
    """Проверяет, что тестовые пакеты — заглавные латинские буквы."""
    if not isinstance(raw_repository, Mapping):
        raise GraphError("Тестовый репозиторий должен быть JSON-объектом.")
    packages_are_valid = all(
        is_test_package(package) for package in raw_repository
    )
    if not raw_repository or not packages_are_valid:
        message = (
            "Имена тестовых пакетов должны быть заглавными латинскими буквами."
        )
        raise GraphError(message)
    lists_are_valid = all(
        isinstance(dependencies, list)
        for dependencies in raw_repository.values()
    )
    if not lists_are_valid:
        message = "Зависимости тестового пакета должны быть JSON-массивом."
        raise GraphError(message)
    graph = {
        package: tuple(dependencies)
        for package, dependencies in raw_repository.items()
    }
    dependencies_are_valid = all(
        valid_dependencies(dependencies, graph)
        for dependencies in graph.values()
    )
    if not dependencies_are_valid:
        message = (
            "Зависимости должны ссылаться на пакеты тестового репозитория."
        )
        raise GraphError(message)
    return graph


def is_test_package(package_name: object) -> bool:
    """Проверяет формат имени тестового пакета."""
    return (
        isinstance(package_name, str)
        and len(package_name) == PACKAGE_NAME_LENGTH
        and package_name.isascii()
        and package_name.isupper()
    )


def valid_dependencies(
    dependencies: object,
    graph: Mapping[str, tuple[str, ...]],
) -> bool:
    """Проверяет список зависимостей тестового пакета."""
    return (
        isinstance(dependencies, tuple)
        and all(
            is_test_package(dependency) and dependency in graph
            for dependency in dependencies
        )
    )


def format_graph(graph: Mapping[str, tuple[str, ...]]) -> tuple[str, ...]:
    """Преобразует граф в построчное текстовое представление."""
    return tuple(
        format_graph_node(node, dependencies)
        for node, dependencies in graph.items()
    )


def format_graph_node(node: str, dependencies: tuple[str, ...]) -> str:
    """Форматирует одну вершину графа и её исходящие рёбра."""
    if not dependencies:
        return f"{node} -> (нет зависимостей в пределах глубины)"
    return f"{node} -> {', '.join(dependencies)}"
