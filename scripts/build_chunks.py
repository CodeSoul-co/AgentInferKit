"""Script: Build knowledge chunks from raw QA data.

Usage:
    python scripts/build_chunks.py --input data/raw/qa_data.jsonl \
                                   --output data/processed/knowledge_chunks/kb_name.jsonl \
                                   --strategy by_topic \
                                   --chunk_size 256
"""
import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.chunker import ChunkStrategy, chunk
from src.utils.file_io import read_jsonl, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Build knowledge chunks from raw QA data.")
    parser.add_argument("--input", required=True, help="Path to input JSONL file with QA records.")
    parser.add_argument("--output", required=True, help="Path to output JSONL file for chunks.")
    parser.add_argument("--strategy", default="by_topic", choices=[s.value for s in ChunkStrategy],
                        help="Chunking strategy.")
    parser.add_argument("--chunk_size", type=int, default=256, help="Target chunk size.")
    parser.add_argument("--kb_name", default="", help="Knowledge base name to fill into chunks.")
    args = parser.parse_args()

    records = read_jsonl(args.input)
    print(f"Loaded {len(records)} records from {args.input}")

    strategy = ChunkStrategy(args.strategy)
    chunks = chunk(records, strategy=strategy, chunk_size=args.chunk_size)

    if args.kb_name:
        for c in chunks:
            c["kb_name"] = args.kb_name

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output, chunks)
    print(f"Wrote {len(chunks)} chunks to {args.output}")


if __name__ == "__main__":
    main()
