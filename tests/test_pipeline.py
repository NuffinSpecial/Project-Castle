from asl_translator.pipeline import TranslationPipeline


def test_pipeline_generates_gloss_and_links():
    pipeline = TranslationPipeline()
    result = pipeline.translate("I will eat an apple tomorrow")

    assert result.tokens == ["I", "will", "eat", "an", "apple", "tomorrow"]
    assert result.normalized_tokens == ["i", "will", "eat", "an", "apple", "tomorrow"]
    assert result.gloss_tokens[0] == "FUTURE"
    assert "handspeak.com" in result.links[0]
    assert len(result.links) == len(result.gloss_tokens)
