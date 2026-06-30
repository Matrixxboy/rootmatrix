import tiktoken

# We use cl100k_base by default (GPT-4 / 4o tokenizer)
ENCODING_NAME = "cl100k_base"

# Singleton encoder to avoid reloading overhead
_encoder = None

def get_encoder():
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding(ENCODING_NAME)
    return _encoder

def count(text: str) -> int:
    """Returns the token count of a given string."""
    if not text:
        return 0
    return len(get_encoder().encode(text))
