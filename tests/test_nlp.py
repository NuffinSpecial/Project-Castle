from asl_translator.nlp.analyzer import analyze_sentence
from asl_translator.nlp.mwe import extract_mwe


def test_regex_analyzer_tokens():
    analysis = analyze_sentence("Hello 5 worlds", prefer_spacy=False)
    lemmas = analysis.lemmas
    assert "hello" in lemmas
    assert "five" in lemmas or "5" in lemmas


def test_mwe_extraction():
    gloss, remaining = extract_mwe(["thank", "you", "friend"])
    assert gloss == ["THANK-YOU"]
    assert remaining == ["friend"]
