"""Offline NLP and API compatibility checks; never contact MongoDB or cloud APIs."""
import importlib
import math
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class NLPRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patches = [
            patch.dict(os.environ, {
                "YOUSIGHTS_MONGODB_URI": "mongodb://127.0.0.1:27017/review",
                "YOUSIGHTS_BASIC_AUTH_USERNAME": "review-test",
                "YOUSIGHTS_BASIC_AUTH_PASSWORD": "synthetic-test-value",
            }),
            patch("pymongo.MongoClient", return_value=MagicMock()),
            patch("requests.sessions.Session.request", side_effect=AssertionError("Network request forbidden")),
            patch("logging.config.dictConfig"),
            patch("socket.socket.connect", side_effect=AssertionError("Socket connection forbidden")),
        ]
        for item in cls.patches:
            item.start()
            cls.addClassCleanup(item.stop)
        cls.app_init = importlib.import_module("__init__")
        cls.processing = importlib.import_module("sources.youtube_text_processing")
        cls.keywords = importlib.import_module("sources.youtube_text_keywords")
        cls.sentiment = importlib.import_module("sources.youtube_sentiment_fast")

    def test_bundled_stopwords_and_wordnet_work_without_downloads(self):
        self.assertEqual(self.processing.normalization("The CAFÉ and server, running!"), ["cafe", "server"])
        self.assertEqual(self.processing.lemmatize_verbs(["running", "better"]), ["run", "good"])
        for word in self.processing.my_stopwords:
            if isinstance(word, str) and word.isalpha() and word == word.lower():
                self.assertNotIn(word.lower(), self.processing.normalization(word))

    def test_official_model_has_pos_sentence_and_entity_components(self):
        nlp = self.keywords.keywords_nlp
        self.assertEqual(nlp.meta["version"], "3.8.0")
        doc = nlp("Apple builds computers in London. Developers write Python.")
        self.assertEqual(len(list(doc.sents)), 2)
        self.assertTrue(any(token.pos_ in self.keywords.CANDIDATE_POS for token in doc))
        self.assertTrue(any(entity.text == "London" for entity in doc.ents))

    def test_textrank_connected_and_empty_graphs(self):
        words = ["python", "developer", "software", "server", "developer", "python"]
        result = self.keywords.get_keywords(words, 200)
        self.assertTrue(result)
        self.assertTrue(all(math.isfinite(float(weight)) and weight > 0 for weight in result.values()))
        self.assertEqual(result, self.keywords.get_keywords(words, 200))
        self.assertEqual(self.keywords.get_keywords([], 200), {})
        self.assertEqual(len(self.keywords.get_keywords(words, 2)), 2)

    def test_textrank_isolated_node_has_defined_weight(self):
        # Simulate dirty allocation when masked divide has no explicit output.
        import numpy as np
        real_divide = np.divide
        def dirty_divide(a, b, **kwargs):
            if "out" not in kwargs:
                kwargs["out"] = np.full_like(a, np.nan)
            return real_divide(a, b, **kwargs)
        token = type("Token", (), {"text": "python", "pos_": "NOUN"})()
        doc = type("Doc", (), {"sents": [[token]]})()
        with patch.object(self.keywords, "keywords_nlp", return_value=doc), patch.object(np, "divide", side_effect=dirty_divide):
            result = self.keywords.get_keywords(["python"], 200)
        self.assertAlmostEqual(float(result["python"]), 0.15)

    def test_frequency_similarity_and_sentiment(self):
        from sources.youtube_similarity import Similarity
        self.assertEqual(self.processing.get_freq("Python Python server running"), [
            {"word": "python", "weight": 2}, {"word": "server", "weight": 1}])
        scores = Similarity().cos_similarity([["python", "server"], ["python", "server"], ["garden", "flowers"]])
        self.assertAlmostEqual(float(scores[0]), 1.0)
        self.assertAlmostEqual(float(scores[1]), 0.0)
        results = self.sentiment.sentiment_fast(["This is excellent", "This is awful"], [{"likeCount": 1}, {"likeCount": 0}])
        self.assertEqual(results["best_comments"], ["This is excellent"])
        self.assertEqual(results["worst_comments"], ["This is awful"])
        self.assertEqual(results["comment_positive_ratio"], 0.5)

    def test_real_synthetic_transcript_table_of_contents(self):
        from sources.youtube_transcript_analysis import generate_table_of_contents
        transcript = [{"start": i * 10.0, "duration": 10.0, "text": "Python developers build software. Servers execute programs."} for i in range(10)]
        result = generate_table_of_contents(transcript)
        self.assertEqual(len(result), 10)
        self.assertTrue(all(item["content"] and set(item) == {"start", "end", "content"} for item in result))
        self.assertIsInstance(self.processing.get_weighted_keywords(self.processing.get_trans_str(transcript)), list)

    def test_cached_video_analysis_uses_local_nlp_and_mocked_entities(self):
        from sources import youtube_analysis_computing as analysis
        transcript = [{"start": i * 10.0, "duration": 10.0, "text": "Python developers build software. Servers execute programs."} for i in range(10)]
        video = {"video_id": "synthetic-video", "data": {
            "title": "Synthetic Python tutorial", "likeCount": 2, "dislikeCount": 0, "viewCount": 10,
            "en_transcript": transcript,
            "some_comments": {"comment_results": ["Excellent tutorial"], "comment_results_more_info": [{"likeCount": 1}]},
        }}
        with patch.object(analysis.youtube_entities, "get_entity", return_value=[]):
            result = analysis.analysis_computing("Python", "cached", {"video_results_count": 1, "video_results": [video]})
        self.assertEqual(result["video_count"], 1)
        analyzed = result["video_statistic_data"][0]["data"]
        self.assertEqual(len(analyzed["en_transcript"]["table_of_contents"]), 10)
        self.assertTrue(analyzed["en_transcript"]["freq_trans"])
        self.assertTrue(math.isfinite(float(analyzed["en_transcript"]["trans_similarity"])))
        self.assertEqual(analyzed["en_transcript"]["entities"], [])

    def test_text_and_token_budgets_reject_before_expensive_work(self):
        from sources.nlp_limits import NLPLimitError, MAX_TEXT_CHARACTERS, MAX_TOKENS, validate_text
        validate_text("x" * MAX_TEXT_CHARACTERS)
        with patch.object(self.processing.nltk, "word_tokenize") as tokenize:
            with self.assertRaises(NLPLimitError):
                self.processing.normalization("x" * (MAX_TEXT_CHARACTERS + 1))
            tokenize.assert_not_called()
        with patch.object(self.processing.nltk, "word_tokenize", return_value=["word"] * (MAX_TOKENS + 1)):
            with self.assertRaises(NLPLimitError):
                self.processing.normalization("short input")
        with patch.object(self.keywords, "keywords_nlp") as nlp:
            for words in [["x"] * (MAX_TOKENS + 1), ["x" * (MAX_TEXT_CHARACTERS + 1)]]:
                with self.assertRaises(NLPLimitError):
                    self.keywords.get_keywords(words, 200)
            nlp.assert_not_called()
        # spaCy may split one supplied word into many tokens; check its tokenizer
        # output before running tagger/parser/NER, not just the input word count.
        with patch.object(self.keywords, "keywords_nlp") as nlp:
            nlp.make_doc.return_value = [None] * (MAX_TOKENS + 1)
            with self.assertRaises(NLPLimitError):
                self.keywords.get_keywords(["punctuation-heavy-input"], 200)
            nlp.assert_not_called()

    def test_candidate_budget_prevents_large_dense_matrix(self):
        import numpy as np
        from sources.nlp_limits import NLPLimitError, MAX_KEYWORD_NODES
        tokens = [type("Token", (), {"text": "word" + str(i), "pos_": "NOUN"})() for i in range(MAX_KEYWORD_NODES + 1)]
        doc = type("Doc", (), {"sents": [tokens]})()
        with patch.object(self.keywords, "keywords_nlp", return_value=doc), patch.object(np, "zeros") as allocate:
            with self.assertRaises(NLPLimitError):
                self.keywords.get_keywords(["synthetic"], 200)
            allocate.assert_not_called()
        # The exact node boundary still supports the normal graph/ranking path.
        doc.sents = [tokens[:-1]]
        with patch.object(self.keywords, "keywords_nlp", return_value=doc):
            result = self.keywords.get_keywords(["synthetic"], 200)
        self.assertEqual(len(result), 200)
        self.assertTrue(all(math.isfinite(float(weight)) for weight in result.values()))

    def test_transcript_budgets_and_join_semantics(self):
        from sources.nlp_limits import NLPLimitError, MAX_TEXT_CHARACTERS, MAX_TRANSCRIPT_SEGMENTS
        from sources.youtube_transcript_analysis import generate_periods_transcript_text
        self.assertEqual(self.processing.get_trans_str([]), "")
        self.assertEqual(self.processing.get_trans_str([{"text": "first"}, {"text": "second"}]), "first second ")
        self.assertEqual(len(self.processing.get_trans_str([{"text": "x" * (MAX_TEXT_CHARACTERS - 1)}])), MAX_TEXT_CHARACTERS)
        overlong = [{"text": "x" * MAX_TEXT_CHARACTERS, "start": 0, "duration": 1}]
        with self.assertRaises(NLPLimitError):
            self.processing.get_trans_str(overlong)
        with self.assertRaises(NLPLimitError):
            generate_periods_transcript_text(overlong, 10)
        with self.assertRaises(NLPLimitError):
            self.processing.get_trans_str([{"text": ""}] * (MAX_TRANSCRIPT_SEGMENTS + 1))

    def test_oversized_upstream_analysis_propagates_budget_error(self):
        from sources import youtube_analysis_computing as analysis
        from sources.nlp_limits import NLPLimitError, MAX_TEXT_CHARACTERS
        video = {"data": {"en_transcript": [{"text": "x" * MAX_TEXT_CHARACTERS}]}}
        with patch.object(self.keywords, "keywords_nlp") as nlp:
            with self.assertRaises(NLPLimitError):
                analysis.analysis_computing("Python", "live", {"video_results_count": 1, "video_results": [video]})
            nlp.assert_not_called()

    def test_api_models_import_and_auth_without_services(self):
        server = importlib.import_module("server")
        client = server.app.test_client()
        self.assertEqual(client.get("/api/v1.0/status").status_code, 200)
        self.assertEqual(client.get("/api/v1.0/logs").status_code, 401)
        swagger = client.get("/swagger.json")
        self.assertEqual(swagger.status_code, 200)
        self.assertIn("Data analysis", swagger.get_json()["definitions"])

    def test_mongodb_read_and_write_calls_use_modern_client(self):
        from sources import database_common, youtube_feedback
        collection = self.app_init.shared_mongodb_client["yousights"]["topics"]
        collection.find.return_value = [{"name": "Python", "name_in_db": "python", "real_time_query": "Python tutorial"}]
        self.assertEqual(database_common.get_db_topics()[0]["name"], "Python")
        collection.find.assert_called_with({"all_matcher": "a"})
        result = youtube_feedback.feedback_record({"feedback": "synthetic feedback"})
        self.assertEqual(result["message"], "feedback record success")
        self.app_init.shared_mongodb_client["yousights"]["feedbackRecords"].insert_one.assert_called_once()


if __name__ == "__main__":
    unittest.main()
