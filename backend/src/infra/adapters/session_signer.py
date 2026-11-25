"""Signed session cookie value (itsdangerous). No passwords: seeded-user switcher."""

from itsdangerous import BadSignature, URLSafeTimedSerializer


class SessionSigner:
    def __init__(self, secret: str, max_age_s: int) -> None:
        self._serializer = URLSafeTimedSerializer(secret, salt="l10-session")
        self._max_age_s = max_age_s

    def sign(self, user_id: str) -> str:
        return self._serializer.dumps({"uid": user_id})

    def unsign(self, token: str | None) -> str | None:
        """User id, or None if the token is missing, tampered with or expired."""
        if not token:
            return None
        try:
            data = self._serializer.loads(token, max_age=self._max_age_s)
        except BadSignature:
            return None
        uid = data.get("uid") if isinstance(data, dict) else None
        return uid if isinstance(uid, str) else None
