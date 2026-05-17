import unittest

from scripts.run_concurrency_sweep import parse_int_list
from scripts.summarize_reports import build_row


class ScriptHelpersTest(unittest.TestCase):
    def test_parse_int_list(self) -> None:
        self.assertEqual(parse_int_list("1, 4,8"), [1, 4, 8])

    def test_build_summary_row(self) -> None:
        row = build_row(
            "a100-c4",
            {
                "request_count": 64,
                "total_tokens": 1024,
                "active_joules_per_token": 1.5,
                "active_kwh_per_1m_tokens": 0.42,
            },
            {
                "completed": 64,
                "errors": 0,
                "latency_p50_s": 0.2,
            },
        )

        self.assertEqual(row["run"], "a100-c4")
        self.assertEqual(row["completed"], 64)
        self.assertEqual(row["active_joules_per_token"], 1.5)


if __name__ == "__main__":
    unittest.main()
