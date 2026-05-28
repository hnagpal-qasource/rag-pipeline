import unittest

from validation.metrics import groundedness_score, retrieval_relevance_score


class TestMetrics(unittest.TestCase):
    def test_retrieval_relevance(self):
        contexts = ["Roaming can be activated via app and support."]
        score = retrieval_relevance_score(contexts, ["roaming", "activate", "support"])
        self.assertGreaterEqual(score, 2 / 3)

    def test_groundedness(self):
        answer = "Activate roaming from app support"
        contexts = ["You can activate roaming from telecom app or support center"]
        score = groundedness_score(answer, contexts)
        self.assertGreater(score, 0.5)


if __name__ == "__main__":
    unittest.main()
