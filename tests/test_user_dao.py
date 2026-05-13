def test_create_get_update_delete_user(user_dao):
    # create
    user = user_dao.create(username="alice", email="alice@example.com", password="pwd")
    assert user.id is not None

    # get
    fetched = user_dao.get(user.id)
    assert fetched.username == "alice"

    # find by username
    found = user_dao.find_by_username("alice")
    assert found.id == user.id

    # update
    user_dao.update(fetched, email="alice2@example.com")
    assert fetched.email == "alice2@example.com"

    # delete
    user_dao.delete(fetched)
    assert user_dao.get(user.id) is None
