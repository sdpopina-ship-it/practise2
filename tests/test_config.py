"""Тесты чтения и проверки TOML-конфигурации первого этапа."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.config import ConfigError, load_config
from src.main import format_settings, main


VALID_CONFIG = """\
package_name = "demo-package"
repository = "repository.json"
use_test_repository = true
package_version = "1.0.0"
ascii_tree = false
max_depth = 2
"""


class ConfigurationTests(unittest.TestCase):
    """Проверяет все параметры TOML и вывод стартового приложения."""

    def setUp(self) -> None:
        """Подготавливает временную папку с корректным тестовым репозиторием."""
        self.temporary_directory = TemporaryDirectory()
        self.base_path = Path(self.temporary_directory.name)
        (self.base_path / "repository.json").write_text("{}", encoding="utf-8")

    def tearDown(self) -> None:
        """Удаляет временные файлы после теста."""
        self.temporary_directory.cleanup()

    def write_config(self, content: str) -> Path:
        """Сохраняет переданную конфигурацию и возвращает её путь."""
        config_path = self.base_path / "config.toml"
        config_path.write_text(content, encoding="utf-8")
        return config_path

    def test_loads_all_required_settings(self) -> None:
        """Корректная конфигурация создаёт объект со всеми параметрами."""
        config = load_config(self.write_config(VALID_CONFIG))
        self.assertEqual(config.package_name, "demo-package")
        self.assertEqual(config.repository, "repository.json")
        self.assertFalse(config.ascii_tree)
        self.assertEqual(config.max_depth, 2)

    def test_rejects_invalid_each_setting(self) -> None:
        """Каждый обязательный параметр имеет собственную проверку ошибки."""
        invalid_parts = (
            ('package_name = ""', "package_name"),
            ('repository = "missing.json"', "repository"),
            ('use_test_repository = "yes"', "use_test_repository"),
            ('package_version = ""', "package_version"),
            ('ascii_tree = "yes"', "ascii_tree"),
            ("max_depth = 0", "max_depth"),
        )
        for replacement, field_name in invalid_parts:
            with self.subTest(field=field_name):
                content = replace_config_part(VALID_CONFIG, replacement)
                with self.assertRaisesRegex(ConfigError, field_name):
                    load_config(self.write_config(content))

    def test_rejects_url_in_test_mode_when_file_is_missing(self) -> None:
        """Тестовый режим принимает только путь к существующему файлу."""
        content = VALID_CONFIG.replace(
            "repository.json",
            "https://registry.npmjs.org",
        )
        with self.assertRaisesRegex(ConfigError, "режиме тестирования"):
            load_config(self.write_config(content))

    def test_rejects_non_url_in_regular_mode(self) -> None:
        """Обычный режим принимает только корректный HTTP(S)-адрес."""
        content = VALID_CONFIG.replace(
            "use_test_repository = true",
            "use_test_repository = false",
        )
        with self.assertRaisesRegex(ConfigError, "HTTP"):
            load_config(self.write_config(content))

    def test_formats_settings_as_key_value_lines(self) -> None:
        """Первый этап отображает каждую настройку в формате ключ-значение."""
        config = load_config(self.write_config(VALID_CONFIG))
        settings = format_settings(config)
        self.assertEqual(len(settings), 6)
        self.assertIn("package_name = demo-package", settings)

    def test_main_returns_error_for_missing_config(self) -> None:
        """Приложение возвращает ошибку, если TOML-файл не существует."""
        result = main(["--config", str(self.base_path / "missing.toml")])
        self.assertEqual(result, 1)


def replace_config_part(content: str, replacement: str) -> str:
    """Заменяет строку параметра на переданную некорректную строку."""
    field_name = replacement.split(" = ", maxsplit=1)[0]
    lines = content.splitlines()
    updated_lines = [
        replacement if line.startswith(field_name + " =") else line
        for line in lines
    ]
    return "\n".join(updated_lines) + "\n"
