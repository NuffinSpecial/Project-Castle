def test_pipeline_generates_gloss_and_sign_slots(pipeline):
    result = pipeline.translate("I will eat an apple tomorrow")

    assert result.tokens == ["I", "will", "eat", "an", "apple", "tomorrow"]
    assert result.lemmas == ["i", "will", "eat", "an", "apple", "tomorrow"]
    assert result.gloss_tokens == ["FUTURE", "ME", "EAT", "APPLE"]
    assert result.gloss_tokens.count("FUTURE") == 1
    assert len(result.links) == len(result.gloss_tokens)
    assert len(result.sign_available) == len(result.gloss_tokens)
    assert all(link is None for link in result.links)


def test_thank_you_mwe(pipeline):
    result = pipeline.translate("thank you")
    assert result.gloss_tokens == ["THANK-YOU"]
