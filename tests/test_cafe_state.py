from cafe_concierge import cafe_state


def setup_function():
    cafe_state.reset_cafe()


def test_venue_is_third_wave_kondapur():
    venue = cafe_state.get_venue()
    assert "Third Wave" in venue["name"]
    assert "Kondapur" in venue["name"] or "Kondapura" in venue["name"]
    assert "Glacier" in venue["address"]


def test_create_order_returns_ticket_with_eta():
    order = cafe_state.create_order(["cappuccino"], mods="less foam", guest_name="Nani")
    assert order["status"] == "success"
    assert order["order_id"].startswith("TWC-")
    assert order["eta_minutes"] >= 1
    assert "Cappuccino" in order["items"][0]["name"]


def test_unknown_item_fails_gracefully():
    order = cafe_state.create_order(["nope-drink"])
    assert order["status"] == "error"
    assert "not found" in order["message"].lower()


def test_get_order_missing():
    assert cafe_state.get_order("TWC-999") is None


def test_room_pulse_has_tips():
    pulse = cafe_state.get_room_pulse()
    assert pulse["crowd"] in {"quiet", "steady", "busy"}
    assert pulse["staff_tip"]
    assert pulse["guest_tip"]


def test_find_match_by_interest():
    result = cafe_state.find_match(["ai", "coffee"], guest_name="Nani")
    assert result["status"] == "success"
    assert result["match"]["handle"]
    assert result["icebreaker"]


def test_find_match_empty_suggests_solo():
    result = cafe_state.find_match(["underwater-basket-weaving-xyz"])
    assert result["status"] == "empty"
    assert "cozy" in result["suggestion"].lower() or "solo" in result["suggestion"].lower()
