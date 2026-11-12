"""Тесты рекурсивного DFS-построения графа зависимостей."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.config import AppConfig
from src.graph import (
    GraphError,
    build_dependency_graph,
    build_graph_with_dfs,
    format_graph,
    validate_test_repository,
)


class GraphTests(unittest.TestCase):
    """Проверяет DFS, циклы, глубину и формат тестового репозитория."""

    def test_builds_graph_with_recursive_dfs(self) -> None:
        """DFS добавляет транзитивные зависимости в порядке обхода."""
        repository = {"A": ("B", "C"), "B": ("D",), "C": (), "D": ()}
        graph = build_graph_with_dfs("A", repository.__getitem__, 3)
        self.assertEqual(graph["A"], ("B", "C"))
        self.assertEqual(graph["B"], ("D",))
        self.assertIn("D", graph)

    def test_handles_cycle_without_infinite_recursion(self) -> None:
        """Циклическая зависимость сохраняет ребро, но не повторяет обход."""
        repository = {"A": ("B",), "B": ("C",), "C": ("A",)}
        graph = build_graph_with_dfs("A", repository.__getitem__, 3)
        self.assertEqual(graph["C"], ("A",))
        self.assertEqual(set(graph), {"A", "B", "C"})

    def test_limits_graph_to_configured_depth(self) -> None:
        """Узлы на предельной глубине не раскрывают своих потомков."""
        repository = {"A": ("B",), "B": ("C",), "C": ("D",), "D": ()}
        graph = build_graph_with_dfs("A", repository.__getitem__, 2)
        self.assertEqual(graph, {"A": ("B",), "B": ("C",), "C": ()})

    def test_rejects_non_capital_package_name(self) -> None:
        """В тестовом репозитории разрешены только заглавные латинские буквы."""
        with self.assertRaisesRegex(GraphError, "заглавными"):
            validate_test_repository({"package": []})

    def test_rejects_unknown_test_dependency(self) -> None:
        """Каждая зависимость должна быть объявлена в тестовом репозитории."""
        with self.assertRaisesRegex(GraphError, "ссылаться"):
            validate_test_repository({"A": ["B"]})

    def test_builds_graph_from_test_repository_file(self) -> None:
        """Режим тестирования читает граф из указанного JSON-файла."""
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "repository.json"
            path.write_text('{"A": ["B"], "B": []}', encoding="utf-8")
            config = AppConfig("A", str(path), True, "test", False, 2)
            graph = build_dependency_graph(config)
        self.assertEqual(graph, {"A": ("B",), "B": ()})

    def test_formats_graph_as_adjacency_lines(self) -> None:
        """Текстовый вывод перечисляет рёбра графа построчно."""
        lines = format_graph({"A": ("B",), "B": ()})
        self.assertEqual(lines[0], "A -> B")
        self.assertIn("B -> (нет зависимостей", lines[1])
