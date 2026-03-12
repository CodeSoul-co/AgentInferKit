"""Ingest oracle chunks into Milvus and test retrieval."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "src"))

from rag import embedder, milvus_store

# 1. Load oracle chunks (deduplicate by chunk_id)
chunks = []
with open("data/rag/oracle_exam_chunks.jsonl") as f:
    for line in f:
        obj = json.loads(line.strip())
        for c in obj.get("chunks", []):
            if not any(x["chunk_id"] == c["chunk_id"] for x in chunks):
                chunks.append(c)
print(f"Loaded {len(chunks)} unique chunks")

# 2. Embed all chunks
texts = [c["text"] for c in chunks]
embeddings = embedder.embed(texts)
dim = embeddings.shape[1]
print(f"Embedded, dim={dim}")

# 3. Create Milvus collection and insert
col_name = milvus_store.create_collection("exam", "v1", dim, force=True)
for c in chunks:
    c.setdefault("source_qa_ids", [])
    c.setdefault("chunk_strategy", "oracle")
    c.setdefault("token_count", len(c["text"]))
n = milvus_store.insert(col_name, chunks, embeddings)
print(f"Inserted {n} chunks into {col_name}")

# 4. Test retrieval
queries = [
    "队列遵循什么原则",
    "归并排序的时间复杂度",
    "TCP三次握手第二步",
    "贝叶斯定理公式",
    "正态分布标准差",
]
for q in queries:
    qvec = embedder.embed([q])[0]
    results = milvus_store.search(col_name, qvec, top_k=3)
    print(f"\nQ: {q}")
    for r in results:
        print(f"  {r['score']:.4f} | {r['chunk_id']}: {r['text'][:70]}")
