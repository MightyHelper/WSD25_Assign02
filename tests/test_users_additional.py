from app.security.password import hash_password, verify_password


def test_hash_and_verify():
    pw = "mysecret"
    h = hash_password(pw)
    assert verify_password(pw, h) is True
    assert verify_password("wrong", h) is False


def test_user_model_roundtrip(normal_user):
    # normal_user fixture creates a user in DB and returns (User, headers)
    user, _ = normal_user
    assert user.email.endswith("@example.com")
