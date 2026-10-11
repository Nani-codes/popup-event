from cafe_concierge import context, db
from cafe_concierge import tools
from cafe_concierge.vibe import QUESTIONS, score_answers


def test_score_answers_plotter_leaning():
    answers = {
        "movie": "inception",
        "weekend": "hackathon",
        "playlist": "lofi",
        "drink_alter_ego": "filter",
        "party_role": "corner",
    }
    result = score_answers(answers)
    assert result["label"]
    assert result["archetype"] in {
        "plotter",
        "builder",
        "romantic",
        "aesthete",
        "spark",
        "host",
    }
    assert "filter-coffee" in result["tags"] or "ai" in result["tags"]
    assert len(result["answers"]) == len(QUESTIONS)


def test_vibe_quiz_persists_personality(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "cafe.db")
    db.init_db()
    user, created = db.upsert_user(
        sub="u1", email="u1@example.com", name="Nani", picture=None
    )
    assert created is True
    assert user["email"] == "u1@example.com"

    token = context.current_user_sub.set("u1")
    try:
        start = tools.start_vibe_check()
        assert start["phase"] == "question"
        qid = start["question"]["id"]
        choice = start["question"]["options"][0]["id"]

        while True:
            step = tools.answer_vibe_question(qid, choice)
            if step.get("phase") == "complete":
                break
            assert step["phase"] == "question"
            qid = step["question"]["id"]
            choice = step["question"]["options"][0]["id"]

        assert step["personality"]["label"]
        profile = tools.get_my_profile()
        assert profile["vibe_complete"] is True
        assert profile["personality"]["label"] == step["personality"]["label"]
    finally:
        context.current_user_sub.reset(token)
