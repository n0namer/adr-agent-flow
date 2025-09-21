# Руководство для LLM-агента

Это руководство предназначено для автономного агента (Codex/LLM), который работает с репозиторием `adr-agent-flow`. Документ агрегирует ключевой контекст, порядок действий и команды, чтобы можно было быстро войти в проект, подготовить артефакты и проанализировать результаты DoD-гейтов.

## 1. Краткая цель репозитория

`adr-agent-flow` — эталонный набор для архитектурного workflow. Он описывает, как формировать и проверять Definition of Done (DoD) с помощью автоматизированных гейтов: ADR, трейсинг, покрытие, security/perf отчёты, e2e сценарии и интеграция с CI.

## 2. Предварительные требования

- Python 3.11+ (проект разрабатывается и тестируется на CPython).
- Установите зависимости: `pip install -r requirements.txt`.
- Для интеграции с GitHub Actions потребуются:
  - GitHub CLI (`gh`) **или** доступ к REST API.
  - Токен с правами `actions:read`, `contents:read`, `pull_requests:read` (рекомендуется переменная `GH_TOKEN`).

## 3. Структура и ключевые артефакты

| Путь | Назначение |
| --- | --- |
| `docs/dod/DoD.yaml` | Машиночитаемый DoD: артефакты, гейты, пороги качества. |
| `governance/design_principles.yaml` | Дизайн-принципы (SOLID, модульность, наблюдаемость). |
| `governance/ci_checks.yaml` | Пороговые значения DoD: покрытие, security, perf, e2e. |
| `tools/cli.py` | CLI `adrflow`: инициализация, верификация, документация. |
| `tools/ci_intake.py` | Оркестратор для загрузки артефактов CI и агрегации `reports/dod_gate.json`. |
| `tools/bootstrap_reports.py` | Генерация синтетических артефактов (прохождение/провал гейтов). |
| `tests/` | Pytest-сценарии, покрывающие позитивные и негативные кейсы DoD. |
| `Makefile` | Сборные цели: `make verify`, `make test`, `make artifacts` и т.д. |
| `reports/` | Каталог для артефактов (coverage, security, perf, e2e, лог). |
| `prompts/`, `workflow.md`, `README.adragent.md` | Методология, роли и состояние ADR-агента. |

## 4. Базовый рабочий цикл агента

### 4.1 Подготовка

1. Убедитесь, что зависимости установлены (`pip install -r requirements.txt`).
2. При необходимости создайте ветку `chore/codex-task-<дата>-<rand>` и настройте Git-авторские данные.

### 4.2 Сбор артефактов и проверок

- **Полный прогон DoD-гейтов**: `make verify`
  - Вызывает `pytest --cov` и складывает отчёт в `reports/coverage.json`.
  - Генерирует синтетические security/perf и e2e отчёты, если реальные отсутствуют.
  - Прогоняет `python tools/cli.py verify --json --exit-code`.
  - Собирает агрегированный гейт `reports/dod_gate.json` через `tools/ci_intake.py --mode=report-only --skip-verify`.
- **Избирательные шаги**:
  - `make test` — только pytest с покрытием.
  - `make artifacts` — только вспомогательные артефакты (coverage, логи, заглушки).
  - `python tools/check_project.py` — читает `reports/verify.json` и печатает вердикт.

### 4.3 Работа с GitHub CI

1. Аутентифицируйтесь в GitHub CLI: `echo "$GH_TOKEN" | gh auth login --with-token`.
2. После пуша ветки (`git push origin <branch>`) выполните:
   ```bash
   python tools/ci_intake.py \
     --mode=guard \
     --fetch --gh-cli \
     --owner "$ADR_GH_OWNER" --repo "$ADR_GH_REPO" \
     --run-id "$ADR_GH_RUN_ID" \
     --artifact "$ADR_GH_ARTIFACT"
   ```
   Скрипт скачает CI-артефакты, заново прогонит `adrflow verify` и обновит `reports/dod_gate.json`.
3. При отсутствии GitHub CLI используйте REST-режим: `python tools/ci_intake.py --rest --token $GH_TOKEN --owner ... --repo ... --run-id ...`.

### 4.4 Интерпретация результатов

- `reports/verify.json` и `reports/dod_gate.json` содержат `summary.ok` и список `miss` для проваленных гейтов.
- `python tools/check_project.py` печатает агрегированную сводку для быстрого анализа.
- Каждому нарушению DoD соответствует конкретный файл в `reports/` (coverage/security/perf/e2e/logs/trace).

## 5. Синтетические сценарии (smoke/negative testing)

Для проверки собственного пайплайна без реального CI используйте `tools/bootstrap_reports.py`:

- Позитивный набор: `python tools/bootstrap_reports.py --scenario pass --reports reports` — создаёт зелёные артефакты.
- Негативный набор: `python tools/bootstrap_reports.py --scenario fail --reports reports/failing` — формирует пакет с нарушениями покрытия, e2e, security, perf и трейсинга.
- Отдельные артефакты можно сгенерировать флагом `--emit=<coverage|logs|e2e|security|performance>`.

Pytest-тест `tests/test_failure_bundle.py` подтверждает, что `adrflow verify` фиксирует нарушения из failing-сценария.

## 6. Поддержание соответствия ADR

- Тегируйте код и тесты комментариями `# ADR: ADR-XXXX` / `# TEST-ADR: ADR-XXXX`.
- Для новых решений оформляйте ADR по шаблонам из `adr_schema/` и размещайте в `docs/adr/`.
- Ведите состояние агента в `state/adragent_state.json` (фаза, активные атомы, outstanding задачи).

## 7. Типичные проблемы и отладка

| Симптом | Что проверить |
| --- | --- |
| `summary.ok=false` в `reports/dod_gate.json` | Откройте соответствующую секцию (`coverage`, `security`, `e2e`, `performance`, `adr-trace`) и исправьте нарушения. |
| Pytest не видит пакеты | Убедитесь, что `PYTHONPATH=.` передан (см. `Makefile`). |
| `ci_intake` не скачивает артефакты | Проверьте токен/флаги `--owner`, `--repo`, `--run-id`, наличие GitHub CLI. |
| Нужно переиспользовать локальные артефакты | Запустите `python tools/ci_intake.py --mode=report-only --skip-fetch`. |

## 8. Чек-лист перед завершением задачи

1. Обновлены ADR/документация и состояние агента.
2. Прогнан `make verify` или эквивалентный набор проверок.
3. `reports/dod_gate.json` и `reports/verify.json` показывают `summary.ok=true` (если работа не связана с демонстрацией failing-сценария).
4. Подготовлен git-коммит, изменения запушены в ветку, CI запущен и результаты проверены через `ci_intake`.

Документ поддерживается в актуальном состоянии вместе с `README.md`. При расхождениях обновляйте оба источника или делайте ссылку на этот плейбук в PR.
