"""Placeholder test referencing ADR-0001."""

# TEST-ADR: ADR-0001 CASE: success

def test_exchange_code_success():
    from src.oauth import exchange_code

    assert exchange_code("code", "state") == "token"
