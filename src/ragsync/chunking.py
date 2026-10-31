def chunk_text(text: str, max_words: int = 80, overlap: int = 15) -> list[str]:
    """Split text into chunks of about max_words words, with overlapping edges."""
    if overlap >= max_words:
        raise ValueError("overlap must be smaller than max_words")

    chunks: list[str] = []
    current: list[str] = []

    for paragraph in text.split("\n\n"):
        words = paragraph.split()
        if not words:
            continue
        pieces = [words[i : i + max_words] for i in range(0, len(words), max_words)]
        for piece in pieces:
            if current and len(current) + len(piece) > max_words:
                chunks.append(" ".join(current))
                current = current[-overlap:] if overlap else []
            current.extend(piece)

    if current:
        chunks.append(" ".join(current))
    return chunks
