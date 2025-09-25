# ContectualASLTranslator

AI powered translator that links signs from HandSpeak in context of the English sentence given.

## Project overview

This repository provides the infrastructure for a deterministic ASL gloss
translation pipeline. A sentence is tokenised, lightly normalised, converted into
an approximate ASL gloss and then linked to the corresponding HandSpeak search
pages.

The pipeline is intentionally modular so each stage can be swapped for a more
sophisticated implementation in the future (for example integrating a neural
machine translation model or using a curated HandSpeak dictionary).

## Getting started

1. Create and activate a virtual environment.
2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the tests:
   ```bash
   pytest
   ```
4. Translate a sentence from the command line:
   ```bash
   python main.py "I will eat an apple tomorrow"
   ```

The CLI accepts multiple sentences as positional arguments and can read from a
file using `--file`. The output is JSON and includes the gloss tokens and the
HandSpeak links for each token.

## Example output

```json
[
  {
    "original_sentence": "I will eat an apple tomorrow",
    "tokens": ["I", "will", "eat", "an", "apple", "tomorrow"],
    "normalized_tokens": ["i", "will", "eat", "an", "apple", "tomorrow"],
    "gloss_tokens": ["FUTURE", "FUTURE", "ME", "EAT", "APPLE"],
    "links": [
      "https://www.handspeak.com/word/search/index.php?word=future",
      "https://www.handspeak.com/word/search/index.php?word=future",
      "https://www.handspeak.com/word/search/index.php?word=me",
      "https://www.handspeak.com/word/search/index.php?word=eat",
      "https://www.handspeak.com/word/search/index.php?word=apple"
    ]
  }
]
```

> ⚠️ The gloss produced is intentionally simple and does not aim to fully
> replicate native ASL grammar. It exists as a foundation for future research
> and experimentation.
