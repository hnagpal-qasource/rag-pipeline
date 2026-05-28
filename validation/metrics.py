from __future__ import annotations

import re


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9]+", text.lower()))


def retrieval_relevance_score(contexts: list[str], required_keywords: list[str]) -> float:
    if not contexts or not required_keywords:
        return 0.0
    context_blob = " ".join(contexts).lower()
    hits = sum(1 for kw in required_keywords if kw.lower() in context_blob)
    return hits / len(required_keywords)


def groundedness_score(answer: str, contexts: list[str]) -> float:
    if not answer or not contexts:
        return 0.0
    answer_tokens = _tokens(answer)
    context_tokens = _tokens(" ".join(contexts))
    if not answer_tokens:
        return 0.0
    overlap = answer_tokens.intersection(context_tokens)
    return len(overlap) / len(answer_tokens)
