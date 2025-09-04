# tests/test_kb_and_selflearn.py
import unittest
from src.core.knowledge_base import KnowledgeBase
from src.core.self_learning import SelfLearning

class TestKB(unittest.TestCase):
    def test_store_and_query(self):
        kb = KnowledgeBase()
        kb.store("test", "hello world")
        rows = kb.query("hello")
        self.assertTrue(any("hello" in r for r in rows))

    def test_self_learning(self):
        kb = KnowledgeBase()
        sl = SelfLearning(kb)
        sl.learn_from_input("datum1")
        n = sl.batch_learn(10)
        self.assertTrue(n >= 1)

if __name__ == "__main__":
    unittest.main()
