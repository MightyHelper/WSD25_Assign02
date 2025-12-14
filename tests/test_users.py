from project.tests.conftest import UserWithLogin


def test_create_get_user(test_app, normal_user: UserWithLogin):
    user, headers = normal_user
    r2 = test_app.get(f"/api/v1/users/{user.id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == user.id
