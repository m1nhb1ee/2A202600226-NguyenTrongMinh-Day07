from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        
        # Split on sentence boundaries: ". ", "! ", "? " or similar whitespace after punctuation
        # Using lookbehind regex to preserve punctuation with sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out empty strings
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return [text] if text else []

        chunks = []
        current_chunk_sentences = []
        
        for sentence in sentences:
            current_chunk_sentences.append(sentence)
            if len(current_chunk_sentences) >= self.max_sentences_per_chunk:
                # Join sentences and add to chunks
                chunk_text = ' '.join(current_chunk_sentences)
                chunks.append(chunk_text)
                current_chunk_sentences = []

        if current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)
            chunks.append(chunk_text)
        
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not remaining_separators:
            if len(current_text) <= self.chunk_size:
                return [current_text]
            else:
                chunks = []
                for i in range(0, len(current_text), self.chunk_size):
                    chunks.append(current_text[i : i + self.chunk_size])
                return chunks
        
        separator = remaining_separators[0]
        rest = remaining_separators[1:]
        
        if not separator:
            if len(current_text) <= self.chunk_size:
                return [current_text]
            else:
                chunks = []
                for i in range(0, len(current_text), self.chunk_size):
                    chunks.append(current_text[i : i + self.chunk_size])
                return chunks
        
        if separator not in current_text:
            return self._split(current_text, rest)
        
        parts = current_text.split(separator)
        result = []
        current_chunk = ""
        
        for part in parts:
            if not current_chunk:
                candidate = part
            else:
                candidate = current_chunk + separator + part
            
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    result.append(current_chunk)
                
                if len(part) > self.chunk_size:
                    result.extend(self._split(part, rest))
                    current_chunk = ""
                else:
                    current_chunk = part
        
        if current_chunk:
            result.append(current_chunk)
        
        return result


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # Compute magnitudes (L2 norm)
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    
    # Handle zero-magnitude vectors
    if mag_a == 0 or mag_b == 0:
        return 0.0
    
    # Compute dot product and divide by product of magnitudes
    dot_product = _dot(vec_a, vec_b)
    return dot_product / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # Initialize chunkers
        fixed_chunker = FixedSizeChunker(chunk_size=chunk_size)
        sentence_chunker = SentenceChunker()
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)
        
        # Run each chunker
        fixed_chunks = fixed_chunker.chunk(text)
        sentence_chunks = sentence_chunker.chunk(text)
        recursive_chunks = recursive_chunker.chunk(text)
        
        # Helper to compute statistics
        def compute_stats(chunks):
            if not chunks:
                return {"count": 0, "avg_length": 0.0, "chunks": []}
            return {
                "count": len(chunks),
                "avg_length": sum(len(c) for c in chunks) / len(chunks),
                "chunks": chunks,
            }
        
        # Return comparison results
        return {
            "fixed_size": compute_stats(fixed_chunks),
            "by_sentences": compute_stats(sentence_chunks),
            "recursive": compute_stats(recursive_chunks),
        }
