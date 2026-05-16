"""Unit tests for app.core.security — password hashing and JWT utilities."""

import time
import uuid

import pytest
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestHashPassword:
    def test_hash_returns_string(self):
        result = hash_password("mysecretpass")
        assert isinstance(result, str)

    def test_hash_is_not_plaintext(self):
        pw = "mysecretpass"
        assert hash_password(pw) != pw

    def test_different_calls_produce_different_hashes(self):
        """bcrypt generates a new salt each call."""
        h1 = hash_password("samepass")
        h2 = hash_password("samepass")
        assert h1 != h2

    def test_hash_starts_with_bcrypt_prefix(self):
        assert hash_password("x").startswith("$2")


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        pw = "correcthorse"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("realpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_empty_password_against_hash_of_empty(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_empty_password_against_non_empty_hash(self):
        hashed = hash_password("notempty")
        assert verify_password("", hashed) is False

    def test_case_sensitive(self):
        hashed = hash_password("Password123")
        assert verify_password("password123", hashed) is False


class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token(user_id=uuid.uuid4(), role="hr")
        assert isinstance(token, str)

    def test_token_contains_sub_and_role(self):
        uid = uuid.uuid4()
        token = create_access_token(user_id=uid, role="employee")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(uid)
        assert payload["role"] == "employee"

    def test_token_has_exp_claim(self):
        token = create_access_token(user_id=uuid.uuid4(), role="hr")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert "exp" in payload
        assert payload["exp"] > time.time()

    def test_extra_claims_are_included(self):
        uid = uuid.uuid4()
        token = create_access_token(user_id=uid, role="hr", extra={"custom": "value"})
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["custom"] == "value"

    def test_user_id_as_string_is_accepted(self):
        uid = str(uuid.uuid4())
        token = create_access_token(user_id=uid, role="hr")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == uid

    def test_iat_claim_is_recent(self):
        token = create_access_token(user_id=uuid.uuid4(), role="hr")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert "iat" in payload
        assert abs(payload["iat"] - time.time()) < 5


class TestDecodeToken:
    def test_valid_token_returns_payload(self):
        uid = uuid.uuid4()
        token = create_access_token(user_id=uid, role="employee")
        payload = decode_token(token)
        assert payload["sub"] == str(uid)
        assert payload["role"] == "employee"

    def test_invalid_token_raises_jwt_error(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.token")

    def test_tampered_token_raises_jwt_error(self):
        token = create_access_token(user_id=uuid.uuid4(), role="hr")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_wrong_secret_raises_jwt_error(self):
        uid = uuid.uuid4()
        bad_token = jwt.encode(
            {"sub": str(uid), "role": "hr", "exp": time.time() + 3600},
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(JWTError):
            decode_token(bad_token)

    def test_round_trip_preserves_all_standard_claims(self):
        uid = uuid.uuid4()
        token = create_access_token(user_id=uid, role="hr", extra={"foo": "bar"})
        payload = decode_token(token)
        assert payload["sub"] == str(uid)
        assert payload["role"] == "hr"
        assert payload["foo"] == "bar"
        assert "exp" in payload
        assert "iat" in payload
