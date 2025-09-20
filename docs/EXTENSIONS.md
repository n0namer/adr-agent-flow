# Расширение ADR Agent Flow

Этот пакет задуман как расширяемый: гейты, адаптеры и LLM-"судьи" можно подключать без правки ядра. Ниже краткое руководство.

## Где регистрировать расширения

* **Гейты** — реализуйте класс `Gate` и отметьте его декоратором `@register_gate`. Модуль можно положить в `tools/plugins/` или выпустить как pip-пакет c entry point `adrflow.plugins`.
* **Адаптеры** — воспользуйтесь `tools/adapters/register_adapter`, чтобы объявить чтение/конвертацию coverage, e2e, security, logger-артефактов.
* **LLM-судьи** — реализуйте метод `judge(name, payload)` и зарегистрируйте стратегию через `judges.register("<provider>", obj)`.

## Подключение

Укажите источник плагинов в `.adrflow.yaml`:

```yaml
plugins:
  discovery:
    - local:tools/plugins
    - entrypoint:adrflow.plugins
```

При запуске `adrflow` плагины будут автоматически найдены и зарегистрированы.

## Создание гейта

```python
from tools.gates.base import Gate, GateResult
from tools.gates.registry import register_gate

@register_gate
class MyGate(Gate):
    key = "my-gate"
    title = "My custom check"

    def run(self, cfg):
        # своя логика
        return GateResult(ok=True, miss=[])
```

Добавьте ключ `my-gate` в `gates.include` конфигурации, чтобы гейт запускался через `adrflow verify` или в CI.

## Создание адаптера

```python
from tools.adapters import register_adapter

class MyCoverageAdapter:
    def read(self, cfg):
        return {"line": 90, "branch": 80}

register_adapter("coverage", "my", MyCoverageAdapter())
```

В `.adrflow.yaml` можно выбрать адаптер: `adapters.coverage: custom:my`.

## Подключение LLM-судьи

```python
from tools.ext_registry import judges

class DeepSeekJudge:
    def judge(self, name, payload):
        # HTTP вызов модели
        return payload

judges.register("deepseek", DeepSeekJudge())
```

После этого настройте `.adrflow.yaml`:

```yaml
llm_judge:
  provider: deepseek
  model: deepseek-chat
```

`tools/log_analyzer.py` автоматически воспользуется выбранным провайдером.

Требуемые переменные окружения: `LLM_JUDGE=deepseek` (или другое имя провайдера), `DEEPSEEK_API_KEY`/`OPENAI_API_KEY` и при необходимости `LLM_JUDGE_MODEL`. Payload, который получает ваш judge, повторяет структуру отчётов (`items`, `pass`, `miss`) и может быть расширен, но итог должен возвращать такой же словарь.
