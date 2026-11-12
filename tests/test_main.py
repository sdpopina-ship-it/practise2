"""Тесты консольного вывода третьего этапа."""

from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch
import unittest

from src.main import main


class MainTests(unittest.TestCase):
    """Проверяет консольный вывод графа зависимостей."""

    def test_main_prints_dependency_graph(self) -> None:
        """Третий этап отображает построенный граф зависимостей."""
        captured_output = StringIO()
        graph = {"express@4.21.2": ("accepts@~1.3.8",)}
        with patch(
            "src.main.build_dependency_graph",
            return_value=graph,
        ):
            with redirect_stdout(captured_output):
                result = main(["--config", "examples/config.toml"])
        self.assertEqual(result, 0)
        output = captured_output.getvalue()
        self.assertIn("Граф зависимостей express@4.21.2", output)
        self.assertIn("express@4.21.2 -> accepts@~1.3.8", output)
