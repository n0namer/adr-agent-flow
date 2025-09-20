---
adr_id: ADR-0001
title: "OAuth2 callback: code→token exchange"
status: accepted
context: |
  Требуется безопасный обмен authorization code на access_token.
decision: |
  Реализуем POST /oauth/callback; логируем события обмена; строгая валидация state.
consequences: |
  Нужны e2e-тесты, наблюдаемость, лимиты по времени ответа.
acceptance_criteria:
  - "Успешный обмен code→token возвращает 200 и access_token"
  - "Просроченный/невалидный code даёт 400 OAUTH_CODE_INVALID"
  - "Все попытки логина формируют DEBUG-событие oauth.exchange с полями trace_id, provider, outcome, latency_ms"
observability_signals:
  metrics:
    - name: oauth_exchange_total
      labels: [provider, outcome]
  logs:
    - level: DEBUG
      event: "oauth.exchange"
      must_have_fields: [trace_id, provider, outcome, latency_ms]
  traces:
    - span: "oauth.exchange"
      attributes: [provider, http.status_code]
contracts:
  public_api:
    - "POST /oauth/callback {code, state}"
links:
  - "/openapi.yaml#/paths/~1oauth~1callback/post"
owner: "core-auth"
---
