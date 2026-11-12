"""Тесты получения и обработки метаданных npm-пакета."""

from unittest.mock import patch
import unittest

from src.config import AppConfig
from src.npm_client import (
    NpmClientError,
    build_package_url,
    extract_direct_dependencies,
    get_direct_dependencies,
)


def build_config(use_test_repository: bool = False) -> AppConfig:
    """Создаёт конфигурацию для тестирования клиента npm."""
    return AppConfig(
        package_name="demo-package",
        repository="https://registry.npmjs.org",
        use_test_repository=use_test_repository,
        package_version="1.0.0",
        ascii_tree=False,
        max_depth=3,
    )


class NpmClientTests(unittest.TestCase):
    """Проверяет запрос конкретной версии и разбор dependencies."""

    def test_builds_url_for_scoped_package(self) -> None:
        """Имя scoped-пакета корректно кодируется в адресе запроса."""
        url = build_package_url(
            "https://registry.npmjs.org/",
            "@scope/package",
            "1.2.3",
        )
        expected_url = "https://registry.npmjs.org/%40scope%2Fpackage/1.2.3"
        self.assertEqual(url, expected_url)

    def test_extracts_sorted_dependencies(self) -> None:
        """Зависимости сортируются по имени и сохраняют диапазоны версий."""
        dependencies = extract_direct_dependencies(
            {"dependencies": {"zeta": "^2.0.0", "alpha": "~1.0.0"}}
        )
        self.assertEqual(dependencies[0].name, "alpha")
        self.assertEqual(dependencies[1].version_range, "^2.0.0")

    def test_returns_empty_tuple_for_package_without_dependencies(self) -> None:
        """Пакет без поля dependencies не считается ошибкой."""
        self.assertEqual(extract_direct_dependencies({}), ())

    def test_rejects_invalid_dependencies_structure(self) -> None:
        """Некорректное поле dependencies сопровождается понятной ошибкой."""
        with self.assertRaisesRegex(NpmClientError, "dependencies"):
            extract_direct_dependencies({"dependencies": ["not-a-mapping"]})

    def test_fetches_exact_configured_version(self) -> None:
        """Клиент получает зависимости по URL для имени и версии из TOML."""
        metadata = {"dependencies": {"library": "^1.2.0"}}
        with patch(
            "src.npm_client.download_package_metadata",
            return_value=metadata,
        ) as download:
            dependencies = get_direct_dependencies(build_config())
        self.assertEqual(dependencies[0].name, "library")
        self.assertIn("demo-package/1.0.0", download.call_args.args[0])

    def test_rejects_test_repository_at_stage_two(self) -> None:
        """На втором этапе данные должны запрашиваться по URL реестра npm."""
        with self.assertRaisesRegex(NpmClientError, "этапе 2"):
            get_direct_dependencies(build_config(use_test_repository=True))
