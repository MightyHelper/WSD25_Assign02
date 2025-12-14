from project.tests.conftest import UserWithLogin


def test_user_type_default_and_response(test_app, normal_user: UserWithLogin):
    user, headers = normal_user
    assert user.type == 0

    # get user by id and ensure type present
    r2 = test_app.get(f'/api/v1/users/{user.id}')
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2['type'] == 0
