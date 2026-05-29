import unittest

from validation.metrics import retrieval_relevance_score, groundedness_score, refusal_score


class TestMetrics(unittest.TestCase):
    def test_retrieval_relevance_all_keywords_found(self):
        contexts = [
            "To activate roaming go to your account settings.",
            "International roaming requires a valid plan.",
        ]
        score = retrieval_relevance_score(contexts, ["roaming", "activate"])
        self.assertEqual(score, 1.0)

    def test_retrieval_relevance_partial_hits(self):
        contexts = ["To activate roaming go to your account settings."]
        score = retrieval_relevance_score(contexts, ["roaming", "activate", "apn"])
        self.assertAlmostEqual(score, 2.0 / 3.0)

    def test_retrieval_relevance_no_keywords(self):
        score = retrieval_relevance_score(["some text"], [])
        self.assertEqual(score, 0.0)

    def test_retrieval_relevance_no_contexts(self):
        score = retrieval_relevance_score([], ["roaming"])
        self.assertEqual(score, 0.0)

    def test_groundedness_answer_in_context(self):
        contexts = ["International roaming can be activated from your account."]
        answer = "International roaming can be activated from your account."
        score = groundedness_score(answer, contexts)
        self.assertGreater(score, 0.9)

    def test_groundedness_answer_outside_context(self):
        contexts = ["How to reset your voicemail PIN."]
        answer = "International roaming requires a separate plan."
        score = groundedness_score(answer, contexts)
        self.assertEqual(score, 0.0)

    def test_groundedness_empty_answer(self):
        score = groundedness_score("", ["some context"])
        self.assertEqual(score, 0.0)

    def test_refusal_score_positive(self):
        phrases = [
            "I don't know the answer to that.",
            "I cannot answer this question.",
            "Sorry, that is outside my scope.",
            "The context does not contain enough information.",
            "I don't have that information.",
            "I can't answer that question.",
        ]
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertEqual(refusal_score(phrase), 1.0)

    def test_refusal_score_negative(self):
        answer = "You can activate international roaming in your account settings."
        self.assertEqual(refusal_score(answer), 0.0)

    def test_refusal_score_empty(self):
        self.assertEqual(refusal_score(""), 0.0)


if __name__ == "__main__":
    unittest.main()