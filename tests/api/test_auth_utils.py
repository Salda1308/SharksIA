from api.auth_utils import hash_password, verify_password, create_jwt, decode_jwt


def test_password_round_trip():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_round_trip():
    token = create_jwt({"user_id": "abc"})
    payload = decode_jwt(token)
    assert payload["user_id"] == "abc"


def test_jwt_invalid_raises():
    payload = decode_jwt("not-a-token")
    assert payload is None
