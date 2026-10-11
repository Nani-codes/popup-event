from cafe_concierge.menu import MENU, filter_menu


def test_menu_has_cozy_and_not_only_sweet_options():
    assert len(MENU) >= 6
    cozy = filter_menu("cozy not too sweet")
    assert cozy
    assert all("cozy" in item["tags"] or "comfort" in item["tags"] for item in cozy)
    assert any("sweet" not in item["tags"] for item in cozy)


def test_filter_coffee_and_cappuccino_present():
    ids = {item["id"] for item in MENU}
    assert "cappuccino" in ids
    assert "filter-coffee" in ids
