def test_wh_question_moves_wh_to_end(pipeline):
    result = pipeline.translate("why would you want to go over there?")
    assert result.gloss_tokens == ["YOU", "WANT", "GO", "THERE", "WHY"]


def test_where_question(pipeline):
    result = pipeline.translate("Where are you going?")
    assert result.gloss_tokens == ["YOU", "GO", "WHERE"]


def test_can_you_polar_question(pipeline):
    result = pipeline.translate("can you?")
    assert result.gloss_tokens == ["YOU", "CAN", "YN-Q"]
    assert len(result.mutable_groups) == 1
    assert result.mutable_groups[0]["indices"] == [0, 1]
