from enum import Enum
from typing import Any, Dict, List

from src.utils.id_gen import generate_experiment_id


class ChunkStrategy(str, Enum):
    BY_TOPIC = "by_topic"
    BY_SENTENCE = "by_sentence"
    BY_TOKEN = "by_token"
    BY_PARAGRAPH = "by_paragraph"


def chunk(
    records: List[Dict[str, Any]],
    strategy: ChunkStrategy = ChunkStrategy.BY_TOPIC,
    chunk_size: int = 256,
) -> List[Dict[str, Any]]:
    """Split QA records into chunks according to the given strategy.

    Args:
        records: List of QA sample dicts. Each must have at least 'sample_id'
                 and either 'question'+'reference_answer' or 'text'.
        strategy: Chunking strategy to use.
        chunk_size: Target chunk size (in tokens for BY_TOKEN, in chars otherwise).

    Returns:
        A list of chunk dicts conforming to SCHEMA.md section 3:
            chunk_id, kb_name (filled later), version, text, source_qa_ids,
            topic, chunk_strategy, token_count, metadata.
    """
    if strategy == ChunkStrategy.BY_TOPIC:
        return _chunk_by_topic(records)
    elif strategy == ChunkStrategy.BY_SENTENCE:
        return _chunk_by_sentence(records, chunk_size)
    elif strategy == ChunkStrategy.BY_TOKEN:
        return _chunk_by_token(records, chunk_size)
    elif strategy == ChunkStrategy.BY_PARAGRAPH:
        return _chunk_by_paragraph(records, chunk_size)
    else:
        raise ValueError(f"Unknown chunk strategy: {strategy}")


def _extract_text(record: Dict[str, Any]) -> str:
    """Extract the full text content from a QA record."""
    parts = []
    if record.get("question"):
        parts.append(record["question"])
    if record.get("reference_answer"):
        parts.append(record["reference_answer"])
    if record.get("text"):
        parts.append(record["text"])
    if record.get("explanation"):
        parts.append(record["explanation"])
    return "\n".join(parts)


def _estimate_tokens(text: str) -> int:
    """Rough token count estimation (1 token ~ 1.3 chars for Chinese, ~4 chars for English)."""
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.3 + other_chars / 4)


def _make_chunk(
    chunk_index: int,
    text: str,
    source_qa_ids: List[str],
    topic: str,
    strategy: str,
) -> Dict[str, Any]:
    """Build a single chunk dict."""
    return {
        "chunk_id": f"chunk_{chunk_index:05d}",
        "kb_name": "",
        "version": "1.0.0",
        "text": text,
        "source_qa_ids": source_qa_ids,
        "topic": topic,
        "chunk_strategy": strategy,
        "token_count": _estimate_tokens(text),
        "metadata": {},
    }


def _chunk_by_topic(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group records by their 'topic' or 'metadata.topic' field; each group becomes one chunk."""
    from collections import defaultdict

    topic_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in records:
        topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "unknown")
        topic_groups[topic].append(r)

    chunks = []
    idx = 0
    for topic, group in sorted(topic_groups.items()):
        combined_text = "\n\n".join(_extract_text(r) for r in group)
        source_ids = [r.get("sample_id", "") for r in group]
        chunks.append(_make_chunk(idx, combined_text, source_ids, topic, "by_topic"))
        idx += 1
    return chunks


def _chunk_by_sentence(
    records: List[Dict[str, Any]], chunk_size: int
) -> List[Dict[str, Any]]:
    """Split each record's text into sentences, then group sentences up to chunk_size chars."""
    import re

    chunks = []
    idx = 0
    for r in records:
        text = _extract_text(r)
        sentences = re.split(r"(?<=[.!?。！？])\s*", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        current_text = ""
        for sent in sentences:
            if len(current_text) + len(sent) > chunk_size and current_text:
                topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "")
                chunks.append(
                    _make_chunk(idx, current_text, [r.get("sample_id", "")], topic, "by_sentence")
                )
                idx += 1
                current_text = sent
            else:
                current_text = (current_text + " " + sent).strip()

        if current_text:
            topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "")
            chunks.append(
                _make_chunk(idx, current_text, [r.get("sample_id", "")], topic, "by_sentence")
            )
            idx += 1
    return chunks


def _chunk_by_token(
    records: List[Dict[str, Any]], chunk_size: int
) -> List[Dict[str, Any]]:
    """Split text into chunks of approximately chunk_size tokens."""
    chunks = []
    idx = 0
    for r in records:
        text = _extract_text(r)
        words = text.split()
        current_words: List[str] = []
        current_tokens = 0

        for word in words:
            word_tokens = _estimate_tokens(word)
            if current_tokens + word_tokens > chunk_size and current_words:
                chunk_text = " ".join(current_words)
                topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "")
                chunks.append(
                    _make_chunk(idx, chunk_text, [r.get("sample_id", "")], topic, "by_token")
                )
                idx += 1
                current_words = [word]
                current_tokens = word_tokens
            else:
                current_words.append(word)
                current_tokens += word_tokens

        if current_words:
            chunk_text = " ".join(current_words)
            topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "")
            chunks.append(
                _make_chunk(idx, chunk_text, [r.get("sample_id", "")], topic, "by_token")
            )
            idx += 1
    return chunks


def _chunk_by_paragraph(
    records: List[Dict[str, Any]], chunk_size: int
) -> List[Dict[str, Any]]:
    """Split text by paragraphs (double newlines), merging short ones up to chunk_size."""
    chunks = []
    idx = 0
    for r in records:
        text = _extract_text(r)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        current_text = ""
        for para in paragraphs:
            if len(current_text) + len(para) > chunk_size and current_text:
                topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "")
                chunks.append(
                    _make_chunk(idx, current_text, [r.get("sample_id", "")], topic, "by_paragraph")
                )
                idx += 1
                current_text = para
            else:
                current_text = (current_text + "\n\n" + para).strip()

        if current_text:
            topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "")
            chunks.append(
                _make_chunk(idx, current_text, [r.get("sample_id", "")], topic, "by_paragraph")
            )
            idx += 1
    return chunks
