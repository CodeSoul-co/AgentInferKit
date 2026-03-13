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
    chunk_overlap: int = 0,
) -> List[Dict[str, Any]]:
    """Split QA records into chunks according to the given strategy.

    Args:
        records: List of QA sample dicts. Each must have at least 'sample_id'
                 and either 'question'+'reference_answer' or 'text'.
        strategy: Chunking strategy to use.
        chunk_size: Target chunk size (in tokens for BY_TOKEN, in chars otherwise).
        chunk_overlap: Number of overlapping units (chars or tokens) between
                       consecutive chunks. Ignored for BY_TOPIC strategy.

    Returns:
        A list of chunk dicts conforming to SCHEMA.md section 3:
            chunk_id, kb_name (filled later), version, text, source_qa_ids,
            topic, chunk_strategy, token_count, metadata.
    """
    if strategy == ChunkStrategy.BY_TOPIC:
        return _chunk_by_topic(records)
    elif strategy == ChunkStrategy.BY_SENTENCE:
        return _chunk_by_sentence(records, chunk_size, chunk_overlap)
    elif strategy == ChunkStrategy.BY_TOKEN:
        return _chunk_by_token(records, chunk_size, chunk_overlap)
    elif strategy == ChunkStrategy.BY_PARAGRAPH:
        return _chunk_by_paragraph(records, chunk_size, chunk_overlap)
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
    records: List[Dict[str, Any]], chunk_size: int, chunk_overlap: int = 0
) -> List[Dict[str, Any]]:
    """Split each record's text into sentences, then group sentences up to chunk_size chars.

    When chunk_overlap > 0, the last N chars worth of sentences from the
    previous chunk are carried over to the next chunk.
    """
    import re

    chunks = []
    idx = 0
    for r in records:
        text = _extract_text(r)
        sentences = re.split(r"(?<=[.!?\u3002\uff01\uff1f])\s*", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        current_sents: List[str] = []
        current_len = 0
        for sent in sentences:
            if current_len + len(sent) > chunk_size and current_sents:
                topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "")
                chunks.append(
                    _make_chunk(idx, " ".join(current_sents), [r.get("sample_id", "")], topic, "by_sentence")
                )
                idx += 1
                # Overlap: keep trailing sentences that fit within overlap budget
                if chunk_overlap > 0:
                    overlap_sents: List[str] = []
                    overlap_len = 0
                    for s in reversed(current_sents):
                        if overlap_len + len(s) > chunk_overlap:
                            break
                        overlap_sents.insert(0, s)
                        overlap_len += len(s)
                    current_sents = overlap_sents + [sent]
                    current_len = overlap_len + len(sent)
                else:
                    current_sents = [sent]
                    current_len = len(sent)
            else:
                current_sents.append(sent)
                current_len += len(sent)

        if current_sents:
            topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "")
            chunks.append(
                _make_chunk(idx, " ".join(current_sents), [r.get("sample_id", "")], topic, "by_sentence")
            )
            idx += 1
    return chunks


def _chunk_by_token(
    records: List[Dict[str, Any]], chunk_size: int, chunk_overlap: int = 0
) -> List[Dict[str, Any]]:
    """Split text into chunks of approximately chunk_size tokens.

    When chunk_overlap > 0, the last N tokens worth of words from the
    previous chunk are carried over to the next chunk.
    """
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
                # Overlap: keep trailing words that fit within overlap budget
                if chunk_overlap > 0:
                    overlap_words: List[str] = []
                    overlap_tokens = 0
                    for w in reversed(current_words):
                        wt = _estimate_tokens(w)
                        if overlap_tokens + wt > chunk_overlap:
                            break
                        overlap_words.insert(0, w)
                        overlap_tokens += wt
                    current_words = overlap_words + [word]
                    current_tokens = overlap_tokens + word_tokens
                else:
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
    records: List[Dict[str, Any]], chunk_size: int, chunk_overlap: int = 0
) -> List[Dict[str, Any]]:
    """Split text by paragraphs (double newlines), merging short ones up to chunk_size.

    When chunk_overlap > 0, the last N chars worth of paragraphs from the
    previous chunk are carried over to the next chunk.
    """
    chunks = []
    idx = 0
    for r in records:
        text = _extract_text(r)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        current_paras: List[str] = []
        current_len = 0
        for para in paragraphs:
            if current_len + len(para) > chunk_size and current_paras:
                topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "")
                chunks.append(
                    _make_chunk(idx, "\n\n".join(current_paras), [r.get("sample_id", "")], topic, "by_paragraph")
                )
                idx += 1
                # Overlap: keep trailing paragraphs that fit within overlap budget
                if chunk_overlap > 0:
                    overlap_paras: List[str] = []
                    overlap_len = 0
                    for p in reversed(current_paras):
                        if overlap_len + len(p) > chunk_overlap:
                            break
                        overlap_paras.insert(0, p)
                        overlap_len += len(p)
                    current_paras = overlap_paras + [para]
                    current_len = overlap_len + len(para)
                else:
                    current_paras = [para]
                    current_len = len(para)
            else:
                current_paras.append(para)
                current_len += len(para)

        if current_paras:
            topic = r.get("topic", "") or r.get("metadata", {}).get("topic", "")
            chunks.append(
                _make_chunk(idx, "\n\n".join(current_paras), [r.get("sample_id", "")], topic, "by_paragraph")
            )
            idx += 1
    return chunks
