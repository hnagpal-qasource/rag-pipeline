from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalCase:
    question: str
    ground_truth: str
    required_keywords: list[str]


def default_eval_cases() -> list[EvalCase]:
    return [
        EvalCase(
            question="How do I activate international roaming?",
            ground_truth="Activate roaming from telecom app/account settings or through customer support.",
            required_keywords=["roaming", "activate", "support"],
        ),
        EvalCase(
            question="My SIM is not detected after restart. What should I do?",
            ground_truth="Reinsert the SIM, restart device, and manually select network before escalating.",
            required_keywords=["sim", "restart", "network"],
        ),
        EvalCase(
            question="Why is my mobile internet slow and what can I check first?",
            ground_truth="Check network mode, signal strength, data balance, and APN settings.",
            required_keywords=["internet", "signal", "apn"],
        ),
    ]
