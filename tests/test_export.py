import json
import tempfile
import unittest
from pathlib import Path

from llm_power_profiler.export import write_json_report


class ExportTest(unittest.TestCase):
    def test_write_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "report.json"
            write_json_report(str(path), {"total_tokens": 42, "joules_per_token": 1.25})

            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(payload["total_tokens"], 42)
        self.assertEqual(payload["joules_per_token"], 1.25)


if __name__ == "__main__":
    unittest.main()

