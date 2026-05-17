import unittest

from llm_power_profiler.export import build_proxy_report
from llm_power_profiler.stats import SessionStats


class ProxyReportTest(unittest.TestCase):
    def test_build_report_includes_metadata_and_stats(self) -> None:
        stats = SessionStats()
        stats.record_request(prompt_tokens=1, completion_tokens=2, total_tokens=3)

        report = build_proxy_report(
            stats=stats,
            target="http://127.0.0.1:8001",
            host="127.0.0.1",
            port=9000,
            interval_s=0.1,
            gpu_indices=[0],
        )

        self.assertEqual(report["total_tokens"], 3)
        self.assertEqual(report["metadata"]["target"], "http://127.0.0.1:8001")
        self.assertEqual(report["metadata"]["gpu_indices"], [0])


if __name__ == "__main__":
    unittest.main()
