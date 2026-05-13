import unittest

from llm_power_profiler.stats import SessionStats


class SessionStatsTest(unittest.TestCase):
    def test_records_tokens_and_power_metrics(self) -> None:
        stats = SessionStats()
        stats.record_request(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        stats.record_power(total_power_w=100.0, avg_gpu_util_pct=50.0, max_memory_gb=2.0)
        stats.record_power(total_power_w=100.0, avg_gpu_util_pct=70.0, max_memory_gb=3.0)

        snapshot = stats.snapshot()

        self.assertEqual(snapshot.request_count, 1)
        self.assertEqual(snapshot.prompt_tokens, 10)
        self.assertEqual(snapshot.completion_tokens, 20)
        self.assertEqual(snapshot.total_tokens, 30)
        self.assertEqual(snapshot.peak_power_w, 100.0)
        self.assertEqual(snapshot.max_memory_gb, 3.0)
        self.assertAlmostEqual(snapshot.avg_gpu_util_pct or 0.0, 60.0)


if __name__ == "__main__":
    unittest.main()

