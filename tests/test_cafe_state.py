from cafe_concierge import cafe_state, context, db


def setup_function(tmp_path=None):
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


def test_find_match_real_users_only(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "cafe.db")
    db.init_db()
    db.upsert_user(sub="a", email="a@ex.com", name="Ananya", picture=None)
    db.update_profile(
        "a",
        interests=["ai", "coffee"],
        prefs={
            "personality": {
                "label": "Midnight Plotter",
                "tags": ["ai", "coffee", "filter-coffee"],
            }
        },
    )
    db.upsert_user(sub="b", email="b@ex.com", name="Rohan", picture=None)
    db.update_profile(
        "b",
        interests=["ai", "hackathons"],
        prefs={
            "personality": {
                "label": "Jugaad Builder",
                "tags": ["ai", "hackathons", "espresso"],
            }
        },
    )

    token = context.current_user_sub.set("a")
    try:
        result = cafe_state.find_match(["ai", "coffee"])
        assert result["status"] == "success"
        assert result["source"] == "signed_in_guests"
        assert result["match"]["handle"] == "Rohan"
        assert result["match"]["sub"] == "b"
        assert result["matches"]
        listed = db.list_vibe_matches("a")
        assert any(m["matched_sub"] == "b" for m in listed)
        reverse = db.list_vibe_matches("b")
        assert any(m["matched_sub"] == "a" for m in reverse)
    finally:
        context.current_user_sub.reset(token)


def test_find_match_empty_no_seeds(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "cafe.db")
    db.init_db()
    result = cafe_state.find_match(["underwater-basket-weaving-xyz"])
    assert result["status"] == "empty"
    assert result["matches"] == []
    assert "fake" in result["suggestion"].lower() or "live" in result["suggestion"].lower()
