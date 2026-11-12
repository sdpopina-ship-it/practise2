#!/usr/bin/env sh
set -eu

printf '%s\n' 'Обычный тестовый граф:'
./run.sh --config examples/test_config.toml
printf '%s\n' '' 'Граф с циклической зависимостью:'
./run.sh --config examples/test_cycle_config.toml
printf '%s\n' '' 'Граф с ограничением глубины:'
./run.sh --config examples/test_depth_config.toml
