import os
import re
from typing import List

# Path to Culpeper's Complete Herbal text file
TEXT_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pg49513.txt")

_CHUNKS: List[str] = []


def _load_chunks() -> List[str]:
    """Lazy load and chunk the herbal text file."""
    global _CHUNKS
    if _CHUNKS:
        return _CHUNKS

    if not os.path.exists(TEXT_FILE_PATH):
        return []

    try:
        with open(TEXT_FILE_PATH, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Split content into paragraphs/sections
        raw_paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 40]
        _CHUNKS = raw_paragraphs
    except Exception as e:
        print(f"Error loading herbal text file: {e}")
        _CHUNKS = []

    return _CHUNKS


def consult_culinary_herbal_docs(query: str) -> str:
    """Search Culpeper's The Complete Herbal text corpus and return relevant passages.

    Args:
        query: What herb, spice, plant, or culinary/medicinal property to search for.

    Returns:
        Relevant passages from Culpeper's Complete Herbal, or a notice if no passages were found.
    """
    chunks = _load_chunks()
    if not chunks:
        return "Herbal corpus file is not available."

    query_terms = set(re.findall(r"\w+", query.lower()))
    if not query_terms:
        return "Please provide a valid search query."

    scored_chunks = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = sum(chunk_lower.count(term) * (2 if len(term) > 3 else 1) for term in query_terms)
        if score > 0:
            scored_chunks.append((score, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    top_chunks = [chunk for _, chunk in scored_chunks[:5]]

    if not top_chunks:
        return f"No relevant passages found in Culpeper's Complete Herbal for query: '{query}'."

    joined_passages = "\n\n---\n\n".join(top_chunks)
    return (
        f"Grounded passages from Nicholas Culpeper's 'The Complete Herbal':\n\n"
        f"{joined_passages}"
    )
