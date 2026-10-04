"""Budgets for local NLP, including transcripts retrieved from upstream or MongoDB."""
MAX_TEXT_CHARACTERS = 100_000
MAX_TOKENS = 10_000
MAX_KEYWORD_NODES = 1_000
MAX_TRANSCRIPT_SEGMENTS = 10_000


class NLPLimitError(ValueError):
    """Input is too large for the bounded local NLP pipeline."""


def validate_text(text):
    if len(text) > MAX_TEXT_CHARACTERS:
        raise NLPLimitError("NLP text exceeds 100000 characters")
