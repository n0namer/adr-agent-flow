"""Пример пользовательского гейта: проверка наличия раздела Runbook в README."""
from tools.gates.base import Gate, GateResult
from tools.gates.registry import register_gate

@register_gate
class ReadmeRunbookGate(Gate):
    key = "readme-runbook"
    title = "README has Runbook"

    def run(self, cfg):
        try:
            text = open("README.md", "r", encoding="utf-8").read()
        except FileNotFoundError:
            return GateResult(ok=False, miss=["README.md not found"])
        ok = ("Runbook" in text) or ("Руководство эксплуатации" in text)
        miss = [] if ok else ["README missing 'Runbook' section"]
        return GateResult(ok=ok, miss=miss)
