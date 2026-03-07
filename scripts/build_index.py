"""Script: Build Milvus RAG index from chunk JSONL.

Usage:
    python scripts/build_index.py --input data/processed/knowledge_chunks/kb_name.jsonl \
                                  --kb_name my_kb \
                                  --version v1 \
                                  --embedder BAAI/bge-m3
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag import embedder, milvus_store
from src.utils.file_io import read_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Milvus RAG index from chunk JSONL.")
    parser.add_argument("--input", required=True, help="Path to chunks JSONL file.")
    parser.add_argument("--kb_name", required=True, help="Knowledge base name.")
    parser.add_argument("--version", default="v1", help="Collection version suffix.")
    parser.add_argument("--embedder", default=None, help="Embedding model name override.")
    args = parser.parse_args()

    chunks = read_jsonl(args.input)
    print(f"Loaded {len(chunks)} chunks from {args.input}")

    # Embed
    texts = [c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks...")
    embeddings = embedder.embed(texts, model_name=args.embedder)
    dim = embeddings.shape[1]
    print(f"Embedding dim: {dim}")

    # Create collection and insert
    collection_name = milvus_store.create_collection(args.kb_name, args.version, dim)
    inserted = milvus_store.insert(collection_name, chunks, embeddings)
    print(f"Inserted {inserted} chunks into collection '{collection_name}'")
    print("Done.")


if __name__ == "__main__":
    main()
