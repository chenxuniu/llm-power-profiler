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

    def test_records_active_request_metrics(self) -> None:
        stats = SessionStats()
        stats.record_power(total_power_w=100.0, avg_gpu_util_pct=None, max_memory_gb=None)
        stats.begin_request()
        stats.record_power(total_power_w=100.0, avg_gpu_util_pct=None, max_memory_gb=None)
        stats.complete_request(prompt_tokens=5, completion_tokens=5, total_tokens=10)

        snapshot = stats.snapshot()

        self.assertEqual(snapshot.request_count, 1)
        self.assertEqual(snapshot.total_tokens, 10)
        self.assertEqual(snapshot.inflight_requests, 0)
        self.assertGreaterEqual(snapshot.active_duration_s, 0.0)
        self.assertIsNotNone(snapshot.active_tokens_per_second)


if __name__ == "__main__":
    unittest.main()
