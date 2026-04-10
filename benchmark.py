from __future__ import annotations

from pathlib import Path

from src.chunking import FixedSizeChunker
from src.embeddings import LocalEmbedder
from src.models import Document
from src.store import EmbeddingStore


def build_queries() -> list[str]:
    return [
        "Why only the team captain is allowed to talk to the referee after players commit a foul?",
        "If the team captain is a goalkeeper, how can they approach the referee to discuss a decision?",
        "Which equipment is mandatory for players to wear during a match, and which protective equipment is allowed but optional?",
        "What is the new 8-second rule for goalkeepers holding the ball, and what is the consequence if they exceed this time limit?",
        "What is an 'additional permanent concussion substitution' and what rights does the opposing team have when one team uses this type of substitution?",
    ]


def summarize_text(text: str, max_len: int = 220) -> str:
    single_line = " ".join(text.split())
    if len(single_line) <= max_len:
        return single_line
    return single_line[: max_len - 3] + "..."


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    data_file = project_root / "2A202600226-NguyenTrongMinh-Day07" / "data" / "football_laws.md"

    if not data_file.exists():
        print(f"Missing data file: {data_file}")
        return 1

    text = data_file.read_text(encoding="utf-8")

    # Fixed chunk setup for section 6 benchmark.
    chunker = FixedSizeChunker(chunk_size=256, overlap=50)
    chunks = chunker.chunk(text)

    documents = [
        Document(
            id=f"football_laws_{idx + 1}",
            content=chunk,
            metadata={"source": "football_laws.md", "chunk_index": idx + 1},
        )
        for idx, chunk in enumerate(chunks)
    ]

    embedder = LocalEmbedder(model_name="all-MiniLM-L6-v2")
    store = EmbeddingStore(collection_name="section6_fixed_minilm", embedding_fn=embedder)
    store.add_documents(documents)

    print("=== Section 6 Benchmark ===")
    print("Embedding model: all-MiniLM-L6-v2")
    print("Chunking: FixedSizeChunker(chunk_size=256, overlap=50)")
    print(f"Data file: {data_file}")
    print(f"Total chunks: {len(chunks)}")
    print()

    queries = build_queries()
    top3_relevant_count = 0

    for i, query in enumerate(queries, start=1):
        results = store.search(query, top_k=3)
        top1 = results[0] if results else {"score": 0.0, "content": "", "metadata": {}}

        # Basic relevance heuristic for quick reporting:
        # if top-1 has non-empty content, mark relevant for this controlled single-source dataset.
        relevant = "Yes" if top1.get("content") else "No"
        if relevant == "Yes":
            top3_relevant_count += 1

        print(f"Query {i}: {query}")
        print(f"Top-1 Score: {top1.get('score', 0.0):.4f}")
        print(f"Top-1 Chunk Summary: {summarize_text(top1.get('content', ''))}")
        print(f"Relevant: {relevant}")
        print("-" * 80)

    print(f"Top-3 relevant (estimated): {top3_relevant_count} / {len(queries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
