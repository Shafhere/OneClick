import re


def chunks(text: str, chunk_size: int = 1000, overlap: int = 160):
    if chunk_size < 1 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be positive and overlap must be smaller than chunk_size")
    start = 0
    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if len(chunk) >= 80:
            yield start, chunk
        start += chunk_size - overlap


def tokens(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-zA-Z0-9]{2,}", text.lower()) if word not in {
        "the", "and", "for", "with", "from", "that", "this", "are", "was", "were", "what", "when", "where", "does", "how", "who", "company"
    }}
