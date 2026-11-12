"""Тесты консольного вывода второго этапа."""

from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch
import unittest

from src.main import format_dependencies, main
from src.npm_client import Dependency


class MainTests(unittest.TestCase):
    """Проверяет формат вывода списка прямых зависимостей."""

    def test_formats_dependencies(self) -> None:
        """Вывод показывает имя зависимости и её диапазон версии."""
        dependencies = (Dependency("library", "^2.0.0"),)
        formatted_dependencies = format_dependencies(dependencies)
        self.assertEqual(formatted_dependencies, ("library: ^2.0.0",))

    def test_formats_empty_dependencies(self) -> None:
        """Отсутствие зависимостей выводится отдельным сообщением."""
        self.assertEqual(
            format_dependencies(()),
            ("Прямые зависимости не найдены.",),
        )

    def test_main_prints_direct_dependencies(self) -> None:
        """Второй этап выводит прямые зависимости вместо параметров запуска."""
        captured_output = StringIO()
        dependencies = (Dependency("library", "^2.0.0"),)
        with patch(
            "src.main.get_direct_dependencies",
            return_value=dependencies,
        ):
            with redirect_stdout(captured_output):
                result = main(["--config", "examples/config.toml"])
        self.assertEqual(result, 0)
        output = captured_output.getvalue()
        self.assertIn("Прямые зависимости express@4.21.2", output)
        self.assertIn("library: ^2.0.0", output)
