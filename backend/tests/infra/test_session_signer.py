from src.infra.adapters.session_signer import SessionSigner


def test_round_trip() -> None:
    s = SessionSigner("secret", 60)
    assert s.unsign(s.sign("u2")) == "u2"


def test_tampered_or_foreign_token_rejected() -> None:
    token = SessionSigner("secret", 60).sign("u2")
    assert SessionSigner("other-secret", 60).unsign(token) is None
    assert SessionSigner("secret", 60).unsign(token[:-2] + "xx") is None
    assert SessionSigner("secret", 60).unsign(None) is None
