from cafe_concierge import cafe_state, context, db
from cafe_concierge import tools


def setup_function():
    cafe_state.reset_cafe()


def test_get_cafe_info():
    info = tools.get_cafe_info()
    assert info["status"] == "success"
    assert "Third Wave" in info["name"]


def test_browse_menu_tool():
    result = tools.browse_menu("cozy not too sweet")
    assert result["status"] == "success"
    assert result["items"]


def test_place_and_status():
    placed = tools.place_order("cappuccino", mods="extra hot", guest_name="Judge")
    assert placed["status"] == "success"
    status = tools.get_order_status(placed["order_id"])
    assert status["status"] == "success"
    assert status["order"]["order_id"] == placed["order_id"]


def test_get_order_status_missing():
    status = tools.get_order_status("TWC-missing")
    assert status["status"] == "error"


def test_room_and_real_connection(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "cafe.db")
    db.init_db()
    pulse = tools.get_room_pulse()
    assert pulse["status"] == "success"

    db.upsert_user(sub="u1", email="u1@ex.com", name="Nani", picture=None)
    db.update_profile(
        "u1",
        interests=["ai", "coffee"],
        prefs={"personality": {"label": "Midnight Plotter", "tags": ["ai", "coffee"]}},
    )
    db.upsert_user(sub="u2", email="u2@ex.com", name="Priya", picture=None)
    db.update_profile(
        "u2",
        interests=["ai", "books"],
        prefs={"personality": {"label": "Kondapur Softie", "tags": ["ai", "books"]}},
    )

    token = context.current_user_sub.set("u1")
    try:
        empty = tools.find_connection("underwater-xyz")
        assert empty["status"] == "empty"

        match = tools.find_connection("ai, coffee")
        assert match["status"] == "success"
        assert match["match"]["sub"] == "u2"

        notified = tools.notify_match("u2", note="Chai pe milte hain?")
        assert notified["status"] == "success"
        notes = db.list_unread_notifications("u2")
        assert notes
        assert "Nani" in notes[0]["message"]

        listed = tools.list_my_matches()
        assert listed["count"] >= 1
    finally:
        context.current_user_sub.reset(token)
