---
id: ATOM-0000
adr: ADR-0000
status: planned
owner: <squad>
created: YYYY-MM-DD
scope_paths:
  - src/
dependencies:
  - ATOM-0001
quality_rules:
  coverage: 0.8
  lint: true
artifacts:
  - type: code
    path: src/module.ts
  - type: test
    path: tests/module.test.ts
---

# Цель

Кратко опишите ожидаемый результат атома.

# План

Пошаговое описание реализации, тестов, документации.

# Проверки

Список команд, которые должен выполнить агент для валидации атома.

# Примечания

Особые ограничения, риски, требования к ревью.
