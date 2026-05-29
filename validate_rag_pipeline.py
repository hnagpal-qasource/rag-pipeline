from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_groq import ChatGroq

from rag_chain import build_chain
from retriever import build_retriever
from validation.config import load_config
from validation.dataset import default_eval_cases
from validation.metrics import groundedness_score, refusal_score, retrieval_relevance_score


class _HashEmbeddings(Embeddings):
    """Lightweight deterministic embeddings for local metric evaluation."""

    def __init__(self, dim: int = 256):
        self.dim = dim

    def _embed(self, text: str) -> list[float]:
        import hashlib
        import re

        tokens = re.findall(r"\w+", text.lower())
        vec = [0.0] * self.dim
        for t in tokens:
            d = hashlib.sha256(t.encode("utf-8")).digest()
            idx = int.from_bytes(d[:4], "big") % self.dim
            vec[idx] += 1.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _configure_local_hf_cache() -> None:
    # No-op with the current local retriever implementation.
    return None


def _ensure_ragas_compat() -> None:
    # ragas currently imports this legacy module path during import.
    module_name = "langchain_community.chat_models.vertexai"
    if module_name in sys.modules:
        return

    shim = ModuleType(module_name)

    class ChatVertexAI:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise ImportError("ChatVertexAI compatibility shim placeholder.")

    shim.ChatVertexAI = ChatVertexAI
    sys.modules[module_name] = shim


def _check_preflight(require_ragas: bool) -> dict:
    _configure_local_hf_cache()
    _ensure_ragas_compat()
    checks: dict[str, dict] = {}

    checks["env_GROQ_API_KEY"] = {
        "ok": bool(os.getenv("GROQ_API_KEY")),
        "value_present": bool(os.getenv("GROQ_API_KEY")),
    }

    checks["retriever_mode"] = {"ok": True, "value": "local_file_based"}

    if require_ragas:
        try:
            import ragas  # noqa: F401
            import datasets  # noqa: F401

            checks["ragas_installed"] = {"ok": True}
        except Exception as exc:
            checks["ragas_installed"] = {"ok": False, "error": repr(exc)}
    else:
        checks["ragas_installed"] = {"ok": True, "skipped": True}

    return checks


def _ragas_metrics(records: list[dict]) -> tuple[dict, str | None]:
    _configure_local_hf_cache()
    _ensure_ragas_compat()
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

        judge_llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            max_tokens=1024,
            timeout=120,
            max_retries=3,
        )
        local_embeddings = _HashEmbeddings(dim=256)

        # Evaluate one record at a time to avoid ragas parallel timeout on slow networks.
        # ragas 0.1.x has no batch_size param — it uses joblib internally and
        # the 3-minute default timeout kills all jobs when the network is slow.
        all_scores: dict[str, list[float]] = {
            "faithfulness": [],
            "answer_relevancy": [],
            "context_precision": [],
            "context_recall": [],
        }

        for i, record in enumerate(records):
            print(f"    RAGAS evaluating record {i+1}/{len(records)}: {record['question'][:40]}...")
            try:
                single_ds = Dataset.from_list([record])
                result = evaluate(
                    single_ds,
                    metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
                    llm=judge_llm,
                    embeddings=local_embeddings,
                )
                row = result.to_pandas()
                for metric in all_scores:
                    val = row[metric].mean()
                    all_scores[metric].append(float(val) if not (val != val) else 0.0)
            except Exception as e:
                print(f"    WARNING: RAGAS failed on record {i+1}: {e}")
                for metric in all_scores:
                    all_scores[metric].append(0.0)

        normalized = {k: sum(v) / len(v) if v else 0.0 for k, v in all_scores.items()}
        return normalized, None
    except Exception:
        return {}, traceback.format_exc()


def run_validation(config_path: str | None = None, eval_cases: list | None = None) -> dict:
    load_dotenv()
    config = load_config(config_path)

    report: dict = {
        "started_at": _utc_now(),
        "config": config,
        "preflight": _check_preflight(bool(config.get("require_ragas", True))),
        "cases": [],
        "aggregate": {},
        "ragas": {},
        "status": "failed",
        "errors": [],
    }

    preflight_ok = all(item.get("ok", False) for item in report["preflight"].values())
    if not preflight_ok:
        report["errors"].append("Preflight checks failed")
        report["finished_at"] = _utc_now()
        return report

    if eval_cases is None:
        eval_cases = default_eval_cases()
    if len(eval_cases) < config["min_cases"]:
        report["errors"].append(
            f"Dataset has {len(eval_cases)} cases but min_cases is {config['min_cases']}"
        )
        report["finished_at"] = _utc_now()
        return report

    retriever = build_retriever()
    chain = build_chain()

    retrieval_scores = []
    groundedness_scores = []
    refusal_correct = []
    ragas_records = []

    for case in eval_cases:
        docs = retriever.invoke(case.question)
        contexts = [d.page_content for d in docs]
        answer = chain.invoke(case.question)

        relevance = retrieval_relevance_score(contexts, case.required_keywords)
        grounded = groundedness_score(answer, contexts)
        refused = refusal_score(answer)

        retrieval_scores.append(relevance)
        groundedness_scores.append(grounded)

        # For positive cases: system should NOT refuse (refusal should be absent)
        # For negative cases: system SHOULD refuse (refusal should be present)
        if case.expects_refusal:
            refusal_correct.append(1.0 if refused >= 0.5 else 0.0)
        else:
            refusal_correct.append(1.0 if refused < 0.5 else 0.0)

        ragas_records.append(
            {
                "question": case.question,
                "answer": answer,
                "ground_truth": case.ground_truth,
                "contexts": contexts,
            }
        )

        report["cases"].append(
            {
                "input": asdict(case),
                "retrieved_docs": len(docs),
                "retrieval_relevance": relevance,
                "groundedness": grounded,
                "refusal_detected": bool(refused >= 0.5),
                "refusal_correct": refusal_correct[-1] == 1.0,
                "answer_preview": answer[:240],
            }
        )

    report["aggregate"] = {
        "retrieval_relevance": sum(retrieval_scores) / len(retrieval_scores),
        "groundedness": sum(groundedness_scores) / len(groundedness_scores),
        "refusal_accuracy": sum(refusal_correct) / len(refusal_correct),
    }

    config_require_ragas = config.get("require_ragas", True)

    if config_require_ragas:
        ragas_scores, ragas_error = _ragas_metrics(ragas_records)
    else:
        ragas_scores, ragas_error = {}, None

    report["ragas"] = {"scores": ragas_scores, "error": ragas_error}

    thresholds = config["thresholds"]
    checks = {
        "retrieval_relevance": report["aggregate"]["retrieval_relevance"] >= thresholds["retrieval_relevance"],
        "groundedness": report["aggregate"]["groundedness"] >= thresholds["groundedness"],
        "refusal_accuracy": report["aggregate"]["refusal_accuracy"] >= thresholds["refusal_accuracy"],
    }

    if config_require_ragas:
        for name in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            checks[name] = report["ragas"]["scores"].get(name, 0.0) >= thresholds[name]

    report["checks"] = checks
    report["status"] = "passed" if all(checks.values()) else "failed"
    report["finished_at"] = _utc_now()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAG + RAGAS validation")
    parser.add_argument("--config", default=None, help="Path to JSON config")
    parser.add_argument(
        "--out",
        default="reports/validation_report.json",
        help="Path to output JSON report",
    )
    parser.add_argument(
        "--test-type",
        choices=["positive", "negative", "all"],
        default="all",
        help="Which test cases to run: positive (in-scope), negative (edge/refusal), or all",
    )
    args = parser.parse_args()

    # Filter cases based on test type
    all_cases = default_eval_cases()
    if args.test_type == "positive":
        eval_cases = [c for c in all_cases if not c.expects_refusal]
    elif args.test_type == "negative":
        eval_cases = [c for c in all_cases if c.expects_refusal]
    else:
        eval_cases = all_cases

    report = run_validation(args.config, eval_cases=eval_cases)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Validation status: {report['status']}")
    print(f"Report: {out_path}")
    if report.get("errors"):
        print("Errors:")
        for err in report["errors"]:
            print(f"- {err}")

    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
