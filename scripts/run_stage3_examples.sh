#!/usr/bin/env sh
set -eu

SCRIPT_DIRECTORY=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIRECTORY=$(dirname -- "$SCRIPT_DIRECTORY")
cd "$PROJECT_DIRECTORY"

printf '%s\n' 'Обычный тестовый граф:'
./run.sh --config examples/test_config.toml
printf '%s\n' '' 'Граф с циклической зависимостью:'
./run.sh --config examples/test_cycle_config.toml
printf '%s\n' '' 'Граф с ограничением глубины:'
./run.sh --config examples/test_depth_config.toml
