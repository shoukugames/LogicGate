from logicgate import storage


def test_scores_keep_top_ten(tmp_path, monkeypatch):
    monkeypatch.setenv("LOGICGATE_DATA", str(tmp_path))
    for i in range(15):
        storage.add_score(f"P{i}", i * 100 + 50, 3, "easy")
    scores = storage.load_scores()
    assert len(scores) == 10
    assert scores[0]["score"] == 1450
    assert not storage.qualifies(100)
    assert storage.qualifies(5000)


def test_progress_and_reset(tmp_path, monkeypatch):
    monkeypatch.setenv("LOGICGATE_DATA", str(tmp_path))
    storage.record_game_start()
    storage.record_attempt(1, "easy", "simple", "solved", 33.3, 1, 1200)
    data = storage.load_progress()
    assert data["games"] == 1 and data["attempts"][0]["seconds"] == 33.3
    storage.reset_progress()
    assert storage.load_progress()["attempts"] == []


def test_corrupt_file_is_set_aside(tmp_path, monkeypatch):
    monkeypatch.setenv("LOGICGATE_DATA", str(tmp_path))
    (tmp_path / "scores.json").write_text("{not json")
    assert storage.load_scores() == []
    assert (tmp_path / "scores.json.corrupt").exists()
