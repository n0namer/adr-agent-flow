Пройди стадии:
1) make verify (включает unit/coverage, e2e, security/perf и гейты)
2) python tools/check_project.py (ожидается summary.ok=true)
3) python tools/ci_intake.py --mode=<report-only|guard|enforce> --skip-verify
4) Если нужно подтянуть артефакты из CI — используй gh run download <RUN_ID> -n adrflow-reports -D reports/

Верни JSON:

{"adr_trace":"PASS","e2e":{"mlm":"PASS","vtb":"PASS"},"logs":"PASS","coverage":"PASS","security":"PASS","performance":"PASS","dod_gate":"PASS"}

Если FAIL — верни {"fix": [список нарушенных acceptance/DoD пунктов]}. Не добавляй новых задач — только закрывай текущие DoD-брейки.
