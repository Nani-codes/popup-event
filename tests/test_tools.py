from cafe_concierge import cafe_state
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


def test_room_and_connection_tools():
    pulse = tools.get_room_pulse()
    assert pulse["status"] == "success"
    match = tools.find_connection("ai, coffee", guest_name="Judge")
    assert match["status"] == "success"
