# adr-agent-flow

Архитектурный workflow-набор: стандарт ADR, атомы, правила качества, защита покрытия, документация.

## Объединённый дизайн-план / спецификация

### Основные цели

* Автоматизация всех стадий от целей до реализации и обратной связи: ADR → атомизация → код → тесты → трейсинг → документация → feedback loop.
* Минимум ручного вовлечения: агент (Codex / LLM) задаёт только необходимые вопросы и в основном действует сам.
* Чёткая, формализованная структура инструкций, шаблонов и правил.
* Поддержка качественных практик: SOLID, тестируемость, покрытие, статический анализ, безопасность.
* Параллельное выполнение атомов, если не пересекаются, с учётом зависимостей и ownership.

---

### Компоненты системы (файлы / структуры)


### CLI adrflow

Для запуска локальных гейтов и отчётов доступен CLI:

* `adrflow init` — аудит и подготовка bootstrap-патча (идемпотентный).
* `adrflow verify` — локальный прогон гейтов из `.adrflow.yaml` с сохранением `reports/verify.json`.
* `adrflow docs` — печать ожидаемых артефактов и фактически сгенерированных файлов в каталоге `reports/`.
* `adrflow suggest` — список минимальных фиксов на основе `reports/verify.json` (вида `gate: [miss]`).
* `adrflow adopt --mode=<report|guard|enforce>` — перевод гейтов в нужный режим. Опциональный `--service` меняет режим точечно.

Конфигурация хранится в `.adrflow.yaml`; она описывает пути артефактов, выбранные адаптеры и режим включения гейтов (report-only/guard/enforce).
| Название                                            | Назначение                                                                                                                                        |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **governance/design\_principles.yaml**              | Определяет дизайн-принципы: SOLID, separation-of-concerns, modularity, low coupling, high cohesion и др.                                          |
| **governance/ci\_checks.yaml**                      | Пороги Definition-of-Done: минимальное покрытие, требования к статике, допуски по security.                                                     |
| **docs/dod/DoD.yaml**                                | Машиночитаемый Definition of Done: scope, пороги качества, артефакты, список гейтов и команд для CI.                                            |
| **docs/adr/**                                        | Принятые ADR с front-matter, включающим acceptance criteria и сигналы наблюдаемости.                                                            |
| **tools/adr_trace.py**                               | Автоматический трейсинг ADR ↔ код ↔ тесты, формирует `reports/adr_trace.json`.                                                                  |
| **tools/log_analyzer.py**                            | Анализ JSONL debug-логов и проверка наличия сигналов, описанных в ADR.                                                                          |
| **tools/dod_gate.py**                                | Единый DoD-гейт: проверка покрытия, трейсинга, лог-анализа, security/perf/мутационного отчёта и обязательных артефактов.                        |
| **tools/ci_intake.py**                               | Оркестратор для Codex/LLM-контейнера: по необходимости скачивает артефакты (`gh run download` или REST), вызывает `adrflow verify` и агрегирует `reports/dod_gate.json`. |
| **.github/workflows/ci.yml**                         | CI-конвейер, который последовательно запускает тесты, трейсинг, анализ логов и DoD gate.                                                         |
| **prompts/finish_release.md**                        | Инструкция для агента на финальной стадии: запуск трейсинга, E2E, лог-анализа и DoD gate с JSON-ответом.                                        |
| **prompts/adr\_draft\_bot.md**, **dod\_curator.md**, **gate\_composer.md** | Роли для генерации ADR, уточнения DoD и сборки CI-гейтов.                                                  |
| **prompts/llm\_fact\_checker.md**, **llm\_planner.md**, **llm\_referee.md** | LLM-судьи: проверка логов/репортов против ADR, планирование фиксов и мета-оценка решений.                    |
| **governance/ownership.yaml / allowed\_paths.yaml** | Отвечает за who owns какую часть кода и какие пути могут перекрывать атомы; правила непересечения.                                                |
| **adr\_schema/**                                    | Шаблоны ADR и атомов + JSON-схемы для валидации.                                                                                                  |
| **prompts/**                                        | Шаги/сценарии для агента: выяснение контекста, генерация ADR, атомизация, план параллельности, реализация, трейсинг, docs, feedback, регенерация. |
| **workflow\.md**                                    | Карта фаз + переходов + что агент делает на каждом шаге + политика “следующий шаг сам” + состояние.                                               |
| **README.adragent.md**                              | Контракт агента: как запускать, каким образом работать, как вести состояние, уровень автономии.                                                   |
| **state/adragent\_state.json (или yaml)**           | Файл состояния между сессиями агента: текущая фаза, активные ADR/атомы, gaps, что уже сделано.                                                    |

---

#### Обязательные артефакты и порядок запуска

* **Coverage:** `reports/coverage.json` — формируется `pytest --cov` (см. `make test`). Порог: line ≥ 85, branch ≥ 75.
* **Security:** `reports/security.json` — минимум содержит `critical`, `high`. Порог: 0 критических/высоких.
* **Performance:** `reports/performance.json` — метрики `p95_ms`, `error_rate_pct`, `throughput_rps` (поддержка DoD для перфоманса).
* **E2E:** `reports/e2e/*.json` — статусы сценариев с ключом `ok/pass`. Минимум: mlm и vtb.
* **DEBUG logs:** `reports/debug.log.jsonl` — структурированные события (`event`, `adr`, `trace_id`, `provider`, `outcome`, `latency_ms`).
* **ADR trace & log check:** `reports/adr_trace.json`, `reports/adr_log_check.json` — результаты гейтов `adr-trace` и `log-vs-adr`.
* **Теги в коде/тестах:** комментарии вида `# ADR: ADR-XXXX` и `# TEST-ADR: ADR-XXXX` для каждого acceptance-пути.

Типовой локальный цикл (greenfield):

```bash
make verify                  # собирает coverage/e2e/security/perf, запускает гейты и ci_intake
python tools/check_project.py  # печатает JSON вердикт (обёртка над adrflow verify)
python tools/ci_intake.py --mode=report-only  # повторная агрегация/интеграция с GitHub при необходимости
```

Для brownfield-проектов `make verify` использует ваши реальные тесты/скрипты (см. `Makefile`), а `tools/ci_intake.py` способен подтянуть артефакты из GitHub Actions.

#### CI intake и доступ к GitHub

`tools/ci_intake.py` умеет скачивать артефакты тремя способами:

1. **GitHub CLI** (`gh run download`). Установите CLI в контейнере и передайте `--fetch --gh-cli --run-id=<id> [--artifact=name]`.
2. **REST API** (`https://api.github.com/repos/:owner/:repo/actions/runs/:run_id/artifacts`). Используйте `GH_TOKEN` с `actions:read` и укажите `--owner`, `--repo`, `--run-id`.
3. **Локальный режим** — если артефакты уже в `reports/`, просто вызовите `python tools/ci_intake.py --skip-verify --mode=<режим>`.

#### Настройка GitHub-интеграции

Чтобы Codex (или другой агент) смог подтягивать CI-артефакты прямо из GitHub, подготовьте среду следующим образом:

1. **Установите GitHub CLI** в контейнере агента: `sudo apt-get update && sudo apt-get install -y gh`.
2. **Выдайте токен:** создайте PAT с правами `actions:read`, `contents:read`, `pull_requests:read` (можно ограничить SSO) и передайте его через переменную окружения `GH_TOKEN` или `GITHUB_TOKEN`.
3. **Аутентифицируйте gh:** `echo "$GH_TOKEN" | gh auth login --with-token`.
4. **Передайте контекст запуска** (можно через переменные или флаги CLI):
   * `ADR_GH_OWNER` / `ADR_GH_REPO` — владелец и репозиторий (альтернатива флагам `--owner`/`--repo`).
   * `ADR_GH_RUN_ID` — идентификатор нужного GitHub Actions run (либо используйте `--branch` и `--workflow` для автоматического поиска последнего).
   * `ADR_GH_ARTIFACT` (опционально) — имя артефакта, если run содержит несколько архивов.
5. **Запустите intake:**
   ```bash
   python tools/ci_intake.py \
     --mode=guard \
     --fetch \
     --gh-cli \
     --owner "$ADR_GH_OWNER" --repo "$ADR_GH_REPO" \
     --run-id "$ADR_GH_RUN_ID" \
     --artifact "$ADR_GH_ARTIFACT"
   ```
   Скрипт скачает артефакты в `reports/`, повторно вызовет `adrflow verify` и запишет агрегированный результат в `reports/dod_gate.json`.

Если хотите обойтись без GitHub CLI, передайте `--rest` и укажите `--token` либо положитесь на `GH_TOKEN` — скрипт вызовет REST API напрямую.

#### Экспорт патча в GitHub и мгновенная проверка CI из Codex

Чтобы оперативно выгружать изменения в репозиторий и сразу видеть результаты GitHub Actions прямо из Codex, придерживайтесь следующего порядка:

1. **Подготовьте доступ к GitHub.** Установите GitHub CLI внутри контейнера Codex, создайте персональный токен с правами `actions:read`, `contents:read`, `pull_requests:read`, выполните `gh auth login` и передайте контекст запуска (`ADR_GH_OWNER`, `ADR_GH_REPO`, `ADR_GH_RUN_ID`, при необходимости `ADR_GH_ARTIFACT`).
2. **Создайте рабочую ветку и прогоните проверки.** Переключитесь на новую ветку (например, `chore/codex-task-<дата>-<rand>`), запустите `make verify`/`python tools/check_project.py` и зафиксируйте изменения коммитом.
3. **Отправьте коммит в GitHub.** Выполните `git push origin <branch>` — пуш запустит GitHub Actions.
4. **Сразу запросите результаты CI.** Получите идентификатор workflow (`gh run list` или API) и передайте его `tools/ci_intake.py`:
   ```bash
   python tools/ci_intake.py \
     --mode=guard \
     --fetch --gh-cli \
     --owner "$ADR_GH_OWNER" --repo "$ADR_GH_REPO" \
     --run-id "$ADR_GH_RUN_ID" \
     --artifact "$ADR_GH_ARTIFACT"
   ```
   Скрипт скачает артефакты, выполнит `adrflow verify` и сформирует агрегированный отчёт `reports/dod_gate.json`.
5. **Интерпретируйте отчёт.** Посмотрите вывод `python tools/check_project.py` и содержимое `reports/dod_gate.json`, чтобы понять статусы DoD-гейтов. При успехе переходите к созданию Pull Request.

> **Совет.** Если GitHub CLI недоступен, используйте `python tools/ci_intake.py --rest --token $GH_TOKEN --owner ...` — intake обратится к REST API напрямую.

#### Работа без GitHub-интеграции

В режиме чисто локальной проверки агент может не подключаться к GitHub вовсе:

1. Сформируйте артефакты локально (`make verify` или собственный набор команд) — в каталоге `reports/` должны появиться coverage, security, e2e и debug-лог.
2. Вызовите `python tools/check_project.py` — команда прогонит `adrflow verify`, сформирует `reports/verify.json` и выведет JSON-вердикт.
3. При необходимости выполните `python tools/ci_intake.py --mode=report-only --skip-fetch` — intake прочитает уже готовые файлы из `reports/` и соберёт `reports/dod_gate.json` без обращения к GitHub.
4. Для CI в частной среде (GitLab, локальный Jenkins) достаточно обеспечить, чтобы шаги пайплайна складывали артефакты в ту же структуру и сохраняли их как build-артефакты — intake будет работать поверх локального каталога.

#### Синтетические отчёты для отладки

- `python tools/bootstrap_reports.py --scenario fail --reports reports/failing` — сформирует демонстрационный пакет с нарушениями (низкое покрытие, провал e2e, security и performance), на котором `adrflow verify`/`ci_intake` подсветят проблемы Definition of Done.
- `python tools/bootstrap_reports.py --scenario pass --reports reports` или `make artifacts` — соберёт «зелёный» набор артефактов для дымового прогона.

JSON-ответ (пример):

```json
{
  "metadata": {"run_id": 123, "mode": "guard"},
  "verify": {"adr-trace": {"ok": true, "miss": []}, "summary": {"ok": true}},
  "dod": {"summary": {"ok": true, "miss": []}, "coverage": {"ok": true, "actual": {"line": 90, "branch": 80}}},
  "summary": {"ok": true, "mode": "guard", "miss": []}
}
```

Если любой из гейтов `ok=false`, `summary.miss` перечислит конкретные нарушения DoD.

### Процесс / фазы (workflow)

1. **Фаза A — Цель / выработка контекста**
   Агент задаёт вопросы: цель, scope, ограничения, владельцы, зависимости.

2. **Фаза B — ADR генерация**
   Агент создает ADR по шаблону, валидирует front-matter, записывает в `docs/adr/ADR-XXXX.md`.

3. **Фаза C — Атомизация**
   Разделение ADR на атомы: минимальные независимые части с описанием scope\_paths, зависимости, owner, artifacts.

4. **Фаза D — План параллельности**
   Проверка непересечения, рисков, предлагаются батчи атомов, которые можно выполнять одновременно.

5. **Фаза E — Реализация атомов**
   Агент генерирует план кода + тестов, код, тесты, минимум соблюдения SOLID. Public API с ADR-тегами.

6. **Фаза F — Трейсинг и тесты-покрытие**
   Проверка: все публичные символы ADR-теги, unit + integration тесты + (если поддерживает стек) мутaционное покрытие. Проверка линтеров, статического анализа, безопасности. Собираем структурированные JSONL debug-логи (с `event`, `adr`, `trace_id` и др.) для дальнейшей сверки с ADR acceptance.

7. **Фаза G — Документация**
   Генерация / обновление индекса ADR↔символы, сборка документации (MyST/Sphinx или аналог), артефакты.

8. **Фаза H — Обратная связь / ревью / gaps**
   Сверка результатов с acceptance criteria ADR; автоматический анализ логов против `observability_signals` (tools/log_analyzer.py); определение пробелов (“gaps”); агрегирование статусов через `tools/ci_intake.py` (тянет артефакты из GitHub, запускает LLM-судей, пишет `reports/dod_gate.json`). Если есть gaps — регенерация атомов / планов; если всё выполнено — возможен шаг релиза и DoD gate.

9. **Merge / Release политика**
   Без ADR-тега, без покрытия, без документации / трейсинга — **нет мерджа**.

---

### Качество кода / архитектуры

* **SOLID**: выделение обязанностей, интерфейсы, абстракции, слабая связанность. Агент проверяет соответствие дизайна при атомизации и реализации.
* **TDD**: тесты пишутся одновременно с кодом (атомами), в идеале сначала тест → код.
* **Статический анализ, типизация, линтеры**: встроены в CI.
* **Security / безопасное программирование** как часть ci\_checks.

---

### Автономность агента

* Агент хранит и читает состояние (файл state).
* Агент знает “следующий шаг” на каждый момент, и действует без запроса, пока не встретит “кричащую” ситуацию (слом API / security / слишком рискованный diff).
* Уровень автономности регулируется (governance/autonomy.yaml).

---

## Лучшие практики из индустрии, которые сочетать

* **“Fail fast”** в CI: ошибки на lint / тестах / статических проверках должны быстро прерывать, не допускать дальнейших стадий. (из CI/CD best practices) ([Spacelift][1])
* **Организация тестовой автоматизации**: unit, integration, performance, E2E, security проверки — как стандарт. ([Medium][2])
* **Версионирование, хранение конфигурации как кода** (IaC, схемы) — всё в git, в явных yml/json/md. ([docs.databricks.com][3])
* **Обратная связь / непрерывное улучшение / метрики CI** — отслеживание покрытия, времени прохождения тестов, поддержка build stability. ([JetBrains][4])

---

## Итог — спецификация “объединённого пакета требований”

Вот как быть:

* Собрать пакет файлов, как мы обсуждали, включая **governance/design\_principles.yaml**, **ci\_checks.yaml**, **ownership**, **allowed\_paths**, **prompts**, **schemas**, **workflow**, **state**.
* В шаблонах prompts + контракте агента включить упоминание SOLID и дизайн-принципов как обязательных и проверяемых.
* В CI /pipeline чеклисте прописать линтеры, static analysis, code smells, проверки размеров классов/методов, зависимости, чтобы иметь механизмы обнаружения нарушений SOLID.
* В трейсинг / обратной связи агент должен фиксировать “дизайн-принцип violations” как “gaps”, и создавать атомы для рефакторинга, если такие нарушения есть.

---

Если хочешь, могу прямо составить файл `governance/design_principles.yaml` + `design_checks.md` + примеры шаблонов, которые объединяют SOLID + то, что ты хотел, чтобы ты сразу включил в свой стартовый пакет.

[1]: https://spacelift.io/blog/ci-cd-best-practices?utm_source=chatgpt.com "CI/CD Best Practices - Top 11 Tips for Successful Pipelines"
[2]: https://medium.com/%40robert_mcbryde/building-a-best-practice-test-automation-pipeline-with-ci-cd-an-introduction-5a4939bd2c93?utm_source=chatgpt.com "Building a Best Practice Test Automation Pipeline with CI/CD"
[3]: https://docs.databricks.com/aws/en/dev-tools/ci-cd/best-practices?utm_source=chatgpt.com "Best practices and recommended CI/CD workflows on ..."
[4]: https://www.jetbrains.com/teamcity/ci-cd-guide/ci-cd-best-practices/?utm_source=chatgpt.com "Best Practices for Successful CI/CD | TeamCity CI/CD Guide"
