from asl_translator.nlp.flexibility import find_mutable_groups


def test_polar_question_has_mutable_pronoun_modal():
    tokens = ["YOU", "CAN", "YN-Q"]
    groups = find_mutable_groups(tokens)
    assert len(groups) == 1
    assert groups[0].indices == (0, 1)
    assert ("CAN", "YOU") in groups[0].alternatives


def test_future_me_mutable_time_subject(pipeline):
    result = pipeline.translate("I will eat an apple tomorrow")
    assert any(group["indices"] == [0, 1] for group in result.mutable_groups)
