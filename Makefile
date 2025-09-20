.PHONY: verify all test test-e2e security artifacts

PYTEST ?= pytest

reports := reports

$(reports):
	mkdir -p $(reports)

test: $(reports)
	PYTHONPATH=. $(PYTEST) --cov=src --cov-report=json:$(reports)/coverage.json

test-e2e: $(reports)
	python tools/bootstrap_reports.py --reports $(reports) --emit=e2e

security: $(reports)
	python tools/bootstrap_reports.py --reports $(reports) --emit=security
	python tools/bootstrap_reports.py --reports $(reports) --emit=performance

artifacts: $(reports)
	python tools/bootstrap_reports.py --reports $(reports) --emit=logs
	python tools/bootstrap_reports.py --reports $(reports) --emit=coverage

verify: artifacts test security test-e2e
	python tools/cli.py verify --json --exit-code
	python tools/ci_intake.py --mode=report-only --skip-verify --out $(reports)/dod_gate.json

all: verify
