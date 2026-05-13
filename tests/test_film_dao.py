def test_create_list_find_film(film_dao):
    f = film_dao.create(title="Test Movie", description="Desc", duration=100)
    assert f.id is not None

    all_films = film_dao.list()
    assert any(x.id == f.id for x in all_films)

    found = film_dao.find_by_title("Test Movie")
    assert len(found) >= 1

    # cleanup
    film_dao.delete(f)
    assert film_dao.get(f.id) is None
