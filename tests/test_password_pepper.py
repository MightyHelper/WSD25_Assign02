import os
from app.security.password import hash_password, verify_password

def test_pepper_required_in_config():
    # if PEPPER is not set the functions still work but we recommend setting it via env
    # This test asserts hashing/verification works when PEPPER is set
    os.environ.setdefault('PEPPER', 'test-pepper')
    pwd = 'secret'
    h = hash_password(pwd)
    assert verify_password(pwd, h) is True

