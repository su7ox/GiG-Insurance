"""
Smart hierarchical chunking for GigInsurance policy documents.

Strategy:
  1. Strip decorative separators (=== / ---) — noise removal
  2. Split on natural section boundaries (SECTION X: / 4.1 SUBSECTION)
  3. Disruption type detected from subsection HEADER only (not body)
     → prevents "flood risk" in premium section creating wrong metadata
  4. FAQ split into individual Q&A pairs (each Q+A = one chunk)
  5. Every chunk tagged: section, category, disruption_type
  Result: each disruption type = one self-contained chunk
          (threshold + payout + note always retrieved together)

Run once:  python -m app.rag.ingest
Re-run whenever policy docs change.
"""

import os
import re
import chromadb
from chromadb.utils import embedding_functions
import logging

logger = logging.getLogger(__name__)

POLICY_DIR = os.path.join(os.path.dirname(__file__), "../../data")
CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./.chroma")
COLLECTION = "giginsurance_policy"


# ── Text helpers ───────────────────────────────────────────────────────────


def _clean(text: str) -> str:
    """Remove decorative separators and normalize blank lines."""
    text = re.sub(r"^[=\-]{10,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _detect_disruption(body: str) -> str:
    """
    Detect disruption type from the FIRST LINE (section header) only.
    Avoids false positives from words like 'flood risk' in body text.
    """
    first = body.splitlines()[0].upper()
    if "HEAVY RAIN" in first:
        return "heavy_rain"
    if "FLOOD" in first:
        return "flood"
    if "EXTREME HEAT" in first:
        return "extreme_heat"
    if "AIR QUALITY" in first or "AQI" in first:
        return "severe_aqi"
    if "CYCLONE" in first:
        return "cyclone"
    if "CURFEW" in first or "144" in first:
        return "curfew_section_144"
    return "general"


def _detect_category(header: str) -> str:
    """
    Match SECTION N: with colon to prevent 'SECTION 1' matching 'SECTION 13'.
    """
    h = header.upper()
    mapping = [
        (r"SECTION 1:", "about"),
        (r"SECTION 2:", "eligibility"),
        (r"SECTION 3:", "premium"),
        (r"SECTION 4:", "coverage"),
        (r"SECTION 5:", "payout_limits"),
        (r"SECTION 6:", "claims_process"),
        (r"SECTION 7:", "denial_reasons"),
        (r"SECTION 8:", "exclusions"),
        (r"SECTION 9:", "payout_process"),
        (r"SECTION 10:", "renewal"),
        (r"SECTION 11:", "fraud"),
        (r"SECTION 12:", "contact"),
        (r"SECTION 13:", "faq"),
    ]
    for pattern, category in mapping:
        if re.search(pattern, h):
            return category
    if re.match(r"\d+\.\d+", header):
        return "coverage"
    return "general"


def _split_faq(text: str) -> list[str]:
    """Split FAQ section into individual Q&A pairs."""
    pairs = re.split(r"\n(?=Q:)", text)
    return [p.strip() for p in pairs if "Q:" in p and "A:" in p]


# ── Core chunker ───────────────────────────────────────────────────────────


def smart_chunk(text: str) -> list[dict]:
    """
    Split policy text into semantically coherent chunks.
    Each disruption type (4.1–4.6) becomes one atomic chunk.
    FAQ becomes individual Q&A pair chunks.
    """
    text = _clean(text)
    chunks = []

    # Split on SECTION headers and 4.x subsection headers
    boundary = re.compile(
        r"(?=^(?:SECTION \d+:|(?:\d+\.\d+\s+[A-Z]{3,})))",
        re.MULTILINE,
    )
    splits = [s.strip() for s in boundary.split(text) if s.strip()]

    for split in splits:
        header = split.splitlines()[0].strip()
        body = split.strip()

        if len(body) < 60:  # skip tiny orphan chunks
            continue

        category = _detect_category(header)
        disruption = _detect_disruption(body)

        if category == "faq":
            for i, qa in enumerate(_split_faq(body)):
                chunks.append(
                    {
                        "id": f"faq_{i}",
                        "text": qa,
                        "metadata": {
                            "section": "FAQ",
                            "category": "faq",
                            "disruption_type": "general",
                        },
                    }
                )
            continue

        chunks.append(
            {
                "id": f"chunk_{len(chunks)}",
                "text": body,
                "metadata": {
                    "section": header[:80],
                    "category": category,
                    "disruption_type": disruption,
                },
            }
        )

    return chunks


# ── Ingestion ──────────────────────────────────────────────────────────────


def _load_docs(directory: str) -> list[dict]:
    docs = []
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith((".txt", ".md")):
            continue
        with open(os.path.join(directory, fname), encoding="utf-8") as f:
            text = f.read()
        file_chunks = smart_chunk(text)
        for c in file_chunks:
            c["metadata"]["source"] = fname
        docs.extend(file_chunks)
        logger.info(f"Loaded '{fname}' → {len(file_chunks)} chunks")
    return docs


def ingest():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    try:
        client.delete_collection(COLLECTION)
        logger.info(f"Dropped existing collection '{COLLECTION}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    docs = _load_docs(POLICY_DIR)
    if not docs:
        logger.error(f"No .txt/.md files found in {POLICY_DIR}")
        return

    collection.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[d["metadata"] for d in docs],
    )

    cats = {}
    for d in docs:
        c = d["metadata"]["category"]
        cats[c] = cats.get(c, 0) + 1

    print(f"\n✅ Ingested {len(docs)} chunks into ChromaDB collection '{COLLECTION}'")
    print("\nBreakdown by category:")
    for cat, count in sorted(cats.items()):
        print(f"  {cat:<20} {count} chunk(s)")
    print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ingest()
